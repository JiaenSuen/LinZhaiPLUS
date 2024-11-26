import requests
import pandas as pd
from bs4 import BeautifulSoup
import selenium
from datetime import datetime
from dataclasses import dataclass, asdict, field
import sys,os,re,io
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
start = datetime.now()
formatted_time_start = start.strftime('%Y-%m-%d %H:%M:%S')
 

page_url = 'https://www.rakuya.com.tw/rent/rent_search?search=city&city=99&upd=1&page=' 
csv_path = 'House_Data/House_Rent_Info.csv'
house_data_df = pd.DataFrame()


if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path)
    existing_names = set(existing_df['Name'])
else:
    existing_df = pd.DataFrame()
    existing_names = set()


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/58.0.3029.110 Safari/537.3'
}


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
    Url :str = ''

    def to_dict(self):
        data = asdict(self)
        data['Tags'] = ', '.join(self.Tags)
        return data

    def to_df(self):
        return pd.DataFrame([self.to_dict()] )




def find_max_pages() :
    global page_url
    response  = requests.get(page_url)
    html = response.content.decode()
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    pages_data = re.findall(r'\d+', soup.find('p', class_='pages').text)
    return pages_data[1]


def crawler_url_set(url , page=1 , show=False)->dict:
    global headers
    # init list
    link_list  = []
    title_list = []

    # Clean Title Data
    def clean_title(title: str) -> str:
        if not isinstance(title, str):
            return ""
        return ' '.join(title.split())
    

    
    for i in range(1,page+1):
   
        url = url+str(i)
        response  = requests.get(url,headers=headers)
        html = response.content.decode()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.select('h6 > a[href*="/rent/rent_item"]')

        for item in items:
            link = item.get('href')
            if not link:
                continue
            title = item.get_text(strip=True)
            link_list.append(link)
            title_list.append(clean_title(title))
            if show :
                try:
                    print(f"名稱 : {title}  " )
                    print(f"連結 : {link} \n" )
                except:
                    print(f"名稱 : {title}  ".encode('ascii', errors='ignore').decode('ascii'))
                    print(f"連結 : {link} \n".encode('ascii', errors='ignore').decode('ascii'))

    
    return {
        "Title" : title_list,
        "Link"  : link_list
    }



def crawler_house_info(raw_title,link,show=False):
    global existing_names
    global headers

    # 確認是否已存在
    if raw_title in existing_names:
        print(f"[跳過] 已存在資料: {raw_title}")
        return

    # 對該網站發出租屋請求
    req = requests.get(link , headers=headers)
    html = req.content.decode()
    soup = BeautifulSoup(html,'html.parser')
    title = soup.find('title').text



    content = soup.find('script', string=lambda string: string and 'window.tmpDataLayer' in string)
    data = content.string.strip()   # 擷取JavaScript物件的內容

    
    
    # 用正則表達式提取 item_name 和 price
    #item_name = re.search(r'"item_name":"(.*?)"', data) .group(1)
    #item_name = clean_title(item_name)
    item_name = raw_title
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
        Environment=environment,
        Url = link
    )
    
    # 輸出
    if show :
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

     

   
if __name__ == '__main__':
    # Collect Url
    contain = crawler_url_set(page_url ,2)
    house_set = pd.DataFrame( { 
        'Title' :  contain['Title'],
        'Link'  :  contain['Link'],
    })
    print(f"Url Data Collection Is Completed....")

    # 爬取資訊
    #house_df = pd.read_csv('House_Data/House_Url_Set.csv')
    house_df = house_set
    for title ,link in zip(house_df['Title'], house_df['Link']):
        crawler_house_info(title,link)
    
    # 時間紀錄
    end = datetime.now()
    formatted_time_end = end.strftime('%Y-%m-%d %H:%M:%S')
    print(f"""\n\n   
        Done...
        Time Spent :  {end-start}
        -- {formatted_time_end}  --
    """.encode('ascii', errors='ignore').decode('ascii'))

    # 最終儲存
    if not os.path.exists("House_Data"):
        os.makedirs("House_Data")

    if not house_data_df.empty:
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, house_data_df], ignore_index=True)
        else:
            combined_df = house_data_df
        combined_df.to_csv(csv_path, index=False)
        print(f"[完成] 已追加寫入 {len(house_data_df)} 筆資料至 {csv_path}")
    else:
        print("[完成] 無新資料需寫入")

 

