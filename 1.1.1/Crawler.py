import requests
import pandas as pd
from bs4 import BeautifulSoup
import selenium
import re
from datetime import datetime

start = datetime.now()
formatted_time_start = start.strftime('%Y-%m-%d %H:%M:%S')


 
 
house_data_df = pd.DataFrame(columns=['Name', 'Price', 'Size', 'Age', 'Floors', 'Bedroom', 'Location', 'Tags', 'Time'])


class House_Data :
    def __init__(self,name,size,age,price, floors, bedroom, loc,tags ) -> None:
        self.Name = name
        self.Price= price
        self.Size = size
        self.Age  = age
        self.Floors = floors
        self.Bedroom = bedroom
        self.Location = loc
        self.Tags = tags
 


    def to_dict(self):
        return {
            'Name': self.Name,
            'Price': self.Price + ' NT$',
            'Size': self.Size + ' 坪',
            'Age': self.Age + ' 年',
            'Floors': self.Floors,
            'Bedroom': self.Bedroom,
            'Location': self.Location,
            'Tags': ', '.join(self.Tags)
        }

    def to_df(self):
        return pd.DataFrame([self.to_dict()])


def crawler(link):
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
    size      = re.search(r'"object_main_size":(\d+\.?\d*)', data).group(1)
    floor     = re.search(r'"object_floor":(\d+)', data).group(1)
    bedroom   = re.search(r'"bedrooms":(\d+)', data).group(1)
    loc       = re.search(r'"item_category":"(.*?)"', data).group(1)
    tags      = re.search(r'"object_tag":"(.*?)"',data).group(1).split(',')
    # -----資訊整理-----


    
    thehouse = House_Data(
        name=item_name,
        price=price,
        size=size,
        age=age,
        floors=floor,
        bedroom=bedroom,
        loc=loc,
        tags=tags
    )

    print(f"""
    {title}

    Name     : {item_name} 
    Price    : {price} 
    Age      : {age}
    Size     : {size}
    Floors   : {floor}
    Bedroom  : {bedroom}
    Location : {loc} 
    Tags     : {tags}

    """)
    global house_data_df
    house_data_df = pd.concat([house_data_df, thehouse.to_df()], ignore_index=True)

     
     

house_df = pd.read_csv('House_Set.csv')
for title ,link in zip(house_df['Title'], house_df['Link']):
    crawler(link)

end = datetime.now()
formatted_time_end = end.strftime('%Y-%m-%d %H:%M:%S')

print(f"""
      

    Alright ~ Done !!  
      Time Spent :  {end-start}
    -- {formatted_time_end}  --
""")
house_data_df.to_csv('House_Info_Data.csv')