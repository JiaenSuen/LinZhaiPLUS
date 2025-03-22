import xgboost as xgb
import pandas as pd
import joblib
import re
import json
from sklearn.preprocessing import LabelEncoder

# 載入已訓練的模型
model = xgb.Booster()
model.load_model("model/trained_model.xgb")

# 載入已儲存的 LabelEncoder
le_city = joblib.load('model/le_city.pkl')
le_house_type = joblib.load('model/le_house_type.pkl')

# 改進 Pattern 資料提取邏輯
def extract_pattern_info(pattern, keyword):
    if isinstance(pattern, str):
        match = re.search(rf'(\d+){keyword}', pattern)
        return int(match.group(1)) if match else 0
    return 0

# 預處理房屋資料
def preprocess_listing(listing):
    # 確保 listing 是字典型別
    if not isinstance(listing, dict):
        raise ValueError("Listing should be a dictionary.")
    
    # 將所有欄位名稱轉換為首字母大寫，並處理底線
    listing = {key.replace('_', '').capitalize(): value for key, value in listing.items()}

    # 確保 'HouseType' 欄位存在並處理
    if 'Housetype' not in listing:
        raise ValueError("'HouseType' not found in listing data.")
    
    # 處理城市欄位，將城市名轉換為數字編碼
    listing['City'] = le_city.transform([listing['City']])[0]

    # 處理房屋類型欄位，確保 'HouseType' 使用正確的欄位名稱
    listing['HouseType'] = le_house_type.transform([listing['Housetype']])[0]

    # 處理模式與環境欄位
    listing['Rooms'] = extract_pattern_info(listing['Pattern'], '房')
    listing['LivingRooms'] = extract_pattern_info(listing['Pattern'], '廳')
    listing['Bathrooms'] = extract_pattern_info(listing['Pattern'], '衛')
    listing['Balconies'] = extract_pattern_info(listing['Pattern'], '陽台')
    listing['Kitchens'] = extract_pattern_info(listing['Pattern'], '廚房')

    # 確保環境資料是扁平的
    try:
        if isinstance(listing['Environment'], str):
            listing['Environment'] = json.loads(listing['Environment'])
        elif not isinstance(listing['Environment'], list):
            listing['Environment'] = []  
    except json.JSONDecodeError:
        listing['Environment'] = []  

    
    flat_environment = []
    for sublist in listing['Environment']:
        if isinstance(sublist, list):
            flat_environment.extend(sublist)
        else:
            flat_environment.append(sublist)

    env_set = set(flat_environment)
    
    # 訓練時模型的所有環境特徵
    expected_env_features = ['Env_有對外窗', 'Env_有中庭', 'Env_樓中樓', 'Env_陽台', 'Env_為邊間']
    
    # 為缺失的環境特徵設為 0
    for feature in expected_env_features:
        listing[feature] = 1 if feature in flat_environment else 0

    # 確保列出必要的欄位，這裡要包含所有環境特徵
    necessary_columns = ['Size', 'Age', 'Bedroom', 'City', 'HouseType', 'Rooms', 'LivingRooms', 'Bathrooms', 'Balconies', 'Kitchens']
    necessary_columns.extend(expected_env_features)  # 添加所有期望的環境特徵
    
    # 返回經過預處理並選擇必要特徵的資料
    return {key: listing[key] for key in necessary_columns if key in listing}




# 預測價格
def predict_price(listing):
    # 預處理資料
    processed_listing = preprocess_listing(listing)
    
    # 將字典轉換為 DataFrame
    data = pd.DataFrame([processed_listing])

    # 轉換為 XGBoost 所需的 DMatrix 格式
    dmatrix = xgb.DMatrix(data)

    # 計算預測結果（假設你已經訓練了模型）
    predicted_price = model.predict(dmatrix)
    
    return predicted_price
