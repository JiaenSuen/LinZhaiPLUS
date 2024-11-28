import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import requests
#台北市內湖區堤頂大道二段/杜拜大樓
# 初始化地理編碼服務 (使用 Nominatim)
geolocator = Nominatim(user_agent="my_geo_app")

# 搜尋範圍的半徑 (單位：公尺)
SEARCH_RADIUS = 500   

# 地點類型 (可選擇更多 OSM 支援的類型)
PLACE_CATEGORIES = [
    "amenity",        # 便利設施
    "shop",           # 商店
    "leisure",        # 娛樂設施
    "tourism",        # 旅遊相關
    "education",      # 教育設施
    "healthcare",     # 醫療設施
]

def get_coordinates(address):
    """
    透過 Nominatim 將地址轉換為地理座標
    """
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        raise Exception(f"無法找到該地址的座標：{address}")

def search_osm_data(lat, lng, category, radius=SEARCH_RADIUS):
    """
    使用 OSM Overpass API 搜尋附近指定類別的地點
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node[{category}](around:{radius},{lat},{lng});
      way[{category}](around:{radius},{lat},{lng});
      relation[{category}](around:{radius},{lat},{lng});
    );
    out center;
    """
    response = requests.get(overpass_url, params={'data': query})
    if response.status_code == 200:
        data = response.json()
        elements = data.get("elements", [])
        locations = [(e.get('lat'), e.get('lon')) for e in elements if 'lat' in e and 'lon' in e]
        return locations
    else:
        raise Exception(f"OSM API 請求失敗：{response.status_code}")

def main():
    # 輸入地址，具體到門牌號
    address = input("請輸入地址：")  # 例如："台北市中山區新生北路三段21號"

    try:
        # 獲取經緯度
        lat, lng = get_coordinates(address)
        print(f"地址座標：{lat}, {lng}")

        # 繪製地圖
        my_map = folium.Map(location=[lat, lng], zoom_start=18)

        # 標記輸入的地址
        folium.Marker(location=[lat, lng], popup=address, icon=folium.Icon(color="red")).add_to(my_map)

        # 使用 MarkerCluster 添加各類地點
        for category in PLACE_CATEGORIES:
            locations = search_osm_data(lat, lng, category)
            print(f"類別 {category}: {len(locations)} 個")
            cluster = MarkerCluster(name=category).add_to(my_map)
            for loc in locations:
                folium.Marker(location=loc, popup=category, icon=folium.Icon(color="blue")).add_to(cluster)

        # 顯示地圖
        my_map.save("map.html")
        print("地圖已生成，請打開 map.html 文件以查看地圖。")

    except Exception as e:
        print(f"發生錯誤：{e}")

if __name__ == "__main__":
    main()
 