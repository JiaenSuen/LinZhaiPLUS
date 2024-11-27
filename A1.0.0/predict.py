import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import re

# 1. 讀取資料
data = pd.read_csv("House_Rent_Info.csv")

# 2. 特徵處理
# 改進 Pattern 資料提取邏輯
def extract_pattern_info(pattern, keyword):
    if isinstance(pattern, str):
        match = re.search(rf'(\d+){keyword}', pattern)
        return int(match.group(1)) if match else 0
    return 0

data['Rooms']       = data['Pattern'].apply(lambda x: extract_pattern_info(x, '房'))
data['LivingRooms'] = data['Pattern'].apply(lambda x: extract_pattern_info(x, '廳'))
data['Bathrooms']   = data['Pattern'].apply(lambda x: extract_pattern_info(x, '衛'))
data['Balconies']   = data['Pattern'].apply(lambda x: extract_pattern_info(x, '陽台'))
data['Kitchens']    = data['Pattern'].apply(lambda x: extract_pattern_info(x, '廚房'))

# 處理 Environment (多熱編碼)
data['Environment'] = data['Environment'].apply(lambda x: eval(x) if isinstance(x, str) else [])
env_set = set(tag for sublist in data['Environment'] for tag in sublist)

for tag in env_set:
    data[f'Env_{tag}'] = data['Environment'].apply(lambda x: 1 if tag in x else 0)

# 處理 Tags (多熱編碼)
data['Tags'] = data['Tags'].apply(lambda x: eval(x) if isinstance(x, str) else [])
tag_set = set(tag for sublist in data['Tags'] for tag in sublist)

for tag in tag_set:
    data[f'Tag_{tag}'] = data['Tags'].apply(lambda x: 1 if tag in x else 0)

# 將字串型特徵進行 Label Encoding
for col in ['City', 'Location', 'HouseType']:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col])

# 填補缺失值
data.fillna(0, inplace=True)

# 3. 特徵與標籤
X = data.drop(['Name', 'Price', 'Pattern', 'Environment', 'Tags', 'Url'], axis=1)
y = data['Price']

# 4. 資料分割
 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=42)

Test = X_test.copy()  
Test['Price'] = y_test  

Test = Test.sort_values("Price")  

# 重新分開 X_test 和 y_test
X_test = Test.drop('Price', axis=1)  # 去掉 'Price' 欄位，保留特徵
y_test = Test['Price']  # 單獨取出 Price 欄位作為標籤

# 將數據轉換為 DMatrix 格式
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# 5. 模型訓練 (使用 XGBoost)
params = {
    "tree_method": "hist",
    "device": "cuda",
    "objective": "reg:squarederror",
    "random_state": 42
}
model = xgb.train(params, dtrain, num_boost_round=100)

# 6. 預測與評估
y_pred = model.predict(dtest)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse}")
print(f"R²: {r2}")

# 7. 視覺化
plt.figure(figsize=(10, 6))
plt.plot(range(len(y_test)), y_test, label='Actual Price' )
plt.plot(range(len(y_test)), y_pred, label='Predicted Price' )
plt.xlabel('Sample Index')
plt.ylabel('Price')
plt.title('Actual vs Predicted Prices')
plt.legend()
plt.grid()
plt.show()
