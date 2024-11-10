import requests
from bs4 import BeautifulSoup
import pandas as pd
import re 
import sys,os
 

url = 'https://www.rakuya.com.tw/rent/rent_search?search=city&city=99&upd=1&page=' 
def crawler_set(url , page=1)->dict:
    link_list  = []
    title_list = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }
    for i in range(1,page+1):
   
        url = url+str(i)
        response  = requests.get(url)
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
            title_list.append(title)
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


response  = requests.get(url)
html = response.content.decode()
html_content = response.text
soup = BeautifulSoup(html_content, 'html.parser')


pages_data = re.findall(r'\d+', soup.find('p', class_='pages').text)
print(pages_data)

contain = crawler_set(url ,10)
house_set = pd.DataFrame( { 
    'Title' :  contain['Title'],
    'Link'  :  contain['Link'],
})
if not os.path.exists("House_Data"):
    os.makedirs("House_Data")
house_set.to_csv(path_or_buf='House_Data/House_Url_Set.csv',index=False )