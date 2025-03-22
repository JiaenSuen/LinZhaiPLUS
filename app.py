from flask import Flask, render_template, request, redirect, url_for, session, flash
from model.knn import knn_similar_listings
import sqlite3
from model.map_func import generate_map
from model.xgb import predict_price
from model.db_handler import *


app = Flask(__name__)
app.secret_key = '0000'

# Route :

@app.route('/')
def home():
    return render_template('home.html')

database_path = "data/database.db"





def get_db_connection():
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row   
    return conn

# 查詢房屋清單 
def query_listings(filter_type=None, filter_city=None, min_rent=None, max_rent=None):
    conn = get_db_connection()
    query = """
        SELECT id, title, description, image, house_type, city, price
        FROM listings
        WHERE 1=1
    """
    params = []
    if filter_type:
        query += " AND house_type = ?"
        params.append(filter_type)
    if filter_city:
        query += " AND city = ?"
        params.append(filter_city)
    if min_rent:
        query += " AND price >= ?"
        params.append(min_rent)
    if max_rent:
        query += " AND price <= ?"
        params.append(max_rent)
    
    listings = conn.execute(query, params).fetchall()
    conn.close()
    return listings


# 獲取可選的城市和屋型
def get_filter_options():
    conn = get_db_connection()
    cities = conn.execute("SELECT DISTINCT city FROM listings").fetchall()
    types = conn.execute("SELECT DISTINCT house_type FROM listings").fetchall()
    conn.close()
    
    # 把查詢結果轉換成簡單的 list 形式
    cities = [city['city'] for city in cities]
    types = [type_['house_type'] for type_ in types]
    
    return cities, types


# 瀏覽頁面路由
@app.route('/browse', methods=['GET', 'POST'])
def browse():
    filter_type = request.form.get('type')
    filter_city = request.form.get('city')
    min_rent = request.form.get('min_rent')
    max_rent = request.form.get('max_rent')
    
    # 查詢資料庫資料
    listings = query_listings(filter_type, filter_city, min_rent, max_rent)
    
    # 取得篩選條件選項
    cities, types = get_filter_options()

    return render_template('browse.html', listings=listings, filter_type=filter_type, filter_city=filter_city, 
                           min_rent=min_rent, max_rent=max_rent, cities=cities, types=types)



@app.route('/detail/<int:id>')
def detail(id):
    conn = get_db_connection()
    listing = conn.execute("SELECT * FROM listings WHERE id = ?", (id,)).fetchone()

    if not listing:
        conn.close()
        return render_template('house_not_exist.html')

    
    listing = dict(listing)
    city = listing['city']
    district = listing['district']
    

    # 計算區域的平均價格
    avg_district_price = get_avg_district_price(district, conn)
    
    # 使用機器學習模型預測價格
    predicted_price = predict_price(listing)



    # 取得所有同城市的房屋列表
    all_listings = conn.execute(
        "SELECT * FROM listings WHERE city = ? AND id != ?",
        (city, id)
    ).fetchall()
    all_listings = [dict(listing) for listing in all_listings]

    # 同街區租屋
    
    same_district_listings = [house for house in all_listings if house['district'] == district]

    # knn推薦：同城市的房源
    recommended_listings = knn_similar_listings(all_listings, listing)

    conn.close()

    # 使用 map_utils 生成地圖
    address = listing['location'].split('/')[0]
    map_html, place_count = generate_map(address)

    return render_template(
        'detail.html',
        listing=listing,
        similar_listings=all_listings,
        predicted_price=predicted_price[0],
        avg_district_price=round(avg_district_price, 3),
        map_html=map_html,
        place_count=place_count,

        district_listings    = same_district_listings,   
        recommended_listings = recommended_listings,  
    )





def get_similar_listings(city, district, exclude_id):
    conn = get_db_connection()

    # 查詢同城市、同區域的其他房源，並排除當前房源（exclude_id）
    query = "SELECT * FROM listings WHERE city = ? AND district = ? AND id != ?"
    similar_listings = conn.execute(query, (city, district, exclude_id)).fetchall()

    conn.close()

    return similar_listings

def get_avg_district_price(district, conn):
    """計算該區域的平均價格"""
    avg_price = conn.execute("SELECT AVG(price) FROM listings WHERE district = ?", (district,)).fetchone()[0]
    return avg_price

 

# Search Implement
@app.route('/search', methods=['GET', 'POST'])
def search():
    search_query = request.form.get('query', '').strip() if request.method == 'POST' else ''
    listings = []

    if search_query:
         
        conn = get_db_connection()
        query = """
            SELECT id, title, description, image, house_type, city ,price
            FROM listings
            WHERE title LIKE ? OR description LIKE ? OR city LIKE ?
        """
        search_term = f"%{search_query}%"
        listings = conn.execute(query, (search_term, search_term, search_term)).fetchall()
        conn.close()
    return render_template('search.html', query=search_query, listings=listings)
 


@app.route('/recommender')
def recommender():
    try :
        id = session['house_index']
        conn = get_db_connection()
        listing = conn.execute("SELECT * FROM listings WHERE id = ?", (id,)).fetchone()

        if not listing:
            conn.close()
            return render_template('house_not_exist.html')

        listing = dict(listing)
        city = listing['city']
        
        # 取得所有同城市的房屋列表
        all_listings = conn.execute(
            "SELECT * FROM listings WHERE city = ? AND id != ?",
            (city, id)
        ).fetchall()
        all_listings = [dict(listing) for listing in all_listings]

        # knn推薦：同城市的房源 
        recommended_listings = knn_similar_listings(all_listings, listing)

        conn.close()
    except:
        recommended_listings = []

    return render_template('recommender.html' ,listings = recommended_listings )



@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊頁面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if register_user(username, password, email):
            flash('註冊成功！請登入。', 'success')
            return redirect(url_for('login'))
        else:
            flash('帳號已被使用！請選擇其他帳號。', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global house_index 
    """登入頁面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['house_index'] = user['browse_list']
            flash('登入成功！', 'success')
            return redirect(url_for('manage'))
        else:
            flash('帳號或密碼錯誤', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

@app.route('/manage')
def manage():
    """租屋管理頁面"""
    if 'user_id' not in session:
        flash('請先登入！', 'warning')
        return redirect(url_for('login'))
    
    user_id  = session['user_id']
    username = session['username']
    return render_template('manage.html', username=username)









if __name__ == '__main__':
    app.run(debug=True, port=5001)



