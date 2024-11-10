import requests
import pandas as pd
from bs4 import BeautifulSoup
import selenium
from datetime import datetime
from dataclasses import dataclass, asdict, field
import sys,os,re,io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
start = datetime.now()
formatted_time_start = start.strftime('%Y-%m-%d %H:%M:%S')
 

house_data_df = pd.DataFrame()


@dataclass
class HouseData:
    Name: str
    Price: str
    Size: str
    Age: str
    Floors: str
    Bedroom: str
    City:str
    Location: str
    HouseType: str
    Pattern:str
    Tags: list[str] = field(default_factory=list)
    Environment: list[str] = field(default_factory=list)

    def to_dict(self):
        data = asdict(self)
        data['Tags'] = ', '.join(self.Tags)
        return data

    def to_df(self):
        return pd.DataFrame([self.to_dict()] )


def crawler(link):
    # 對該網站發出租屋請求
    req = requests.get(link)
    html = req.content.decode()
    soup = BeautifulSoup(html,'html.parser')
    title = soup.find('title').text



    content = soup.find('script', string=lambda string: string and 'window.tmpDataLayer' in string)
    data = content.string.strip()   # 擷取JavaScript物件的內容

    
    
    # 用正則表達式提取 item_name 和 price
    item_name = re.search(r'"item_name":"(.*?)"', data).group(1)
    price     = re.search(r'"price":(\d+)', data).group(1)
    age       = re.search(r'"age":(\d+\.?\d*)', data).group(1)
    size      = re.search(r'"item_variant":(\d+\.?\d*)', data).group(1)
    floor     = re.search(r'"object_floor":(\d+)', data)
    floor     = floor.group(1) if floor else 0
    bedroom   = re.search(r'"bedrooms":(\d+)', data).group(1)
    city      = re.search(r'"item_category":"(.*?)"', data).group(1)
    htype     = re.search(r'"item_category5":"(.*?)"', data).group(1)
    tags      = re.search(r'"object_tag":"(.*?)"',data).group(1).split(',')
    
    # Adress
    address_tag = soup.find('h1', class_='txt__address')
    location = address_tag.get_text(strip=True)

    # Pattern and Env Content
    pattern = ''
    environment = None
     
    li_elements = soup.find_all('li')
    for li in li_elements:
        label = li.find('span', class_='list__label')

        # 抓取「格局」資料
        if label and "格局" in label.text:
            pattern = li.find('span', class_='list__content').get_text(strip=True)

        # 抓取「物件環境」資料
        elif label and "物件環境" in label.text:
            b_tags = li.find('span', class_='list__content').find_all('b')
            environment = [b.get_text(strip=True) for b in b_tags]

     

    # -----資訊整理-----

    thehouse = HouseData(
        Name=item_name,      
        Price=price,         
        Size=size,           
        Age=age,            
        Floors=floor,         
        Bedroom=bedroom, 
        City = city,    
        Location=location,        
        HouseType=htype,
        Pattern = pattern,          
        Tags=tags,
        Environment=environment  
    )
    
    print(f"""
    {title}
          
    Name     : {item_name} 
    Price    : {price} 
    Age      : {age}
    Size     : {size}
    Floors   : {floor}
    Bedroom  : {bedroom}
    HouseType: {htype}
    City     : {city}
    Location : {location} 
    Pattern  : {pattern}
    Tags     : {tags}
    Env      : {environment}
    """)
    # 匯入 Data Frame
    global house_data_df
    house_data_df = pd.concat([house_data_df, thehouse.to_df()], ignore_index=True)

     
     
 
house_df = pd.read_csv('House_Data/House_Url_Set.csv')
for title ,link in zip(house_df['Title'], house_df['Link']):
    crawler(link)
 
 
end = datetime.now()
formatted_time_end = end.strftime('%Y-%m-%d %H:%M:%S')

print(f"""\n\n   
    Done...
      Time Spent :  {end-start}
    -- {formatted_time_end}  --
""".encode('ascii', errors='ignore').decode('ascii'))
if not os.path.exists("House_Data"):
    os.makedirs("House_Data")
house_data_df.to_csv('House_Data/House_Rent_Info.csv' ,index=False)

