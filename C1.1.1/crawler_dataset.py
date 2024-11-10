import requests
from bs4 import BeautifulSoup
import pandas as pd


def crawler_set(page=1)->dict:
    link_list  = []
    title_list = []
    for i in range(1,page+1):
        url = 'https://www.rakuya.com.tw/sell/result?zipcode=802&typecode=R1&sort=101&page='+str(page)
        response  = requests.get(url)
        html = response.content.decode()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        items = soup.select('a[href*="/sell_item/info"]')


        for item in items:
            link = item['href'] 
            link_list.append(link) 
            title = item.select_one('h2').text.strip()   
            title_list.append(title) 
            if title:
                print(f"名稱 : {title}")
                print(f"連結 : {link}\n")
    return {
        "Title" : title_list,
        "Link"  : link_list
    }

contain = crawler_set(5)
house_set = pd.DataFrame( { 
    'Title' :  contain['Title'],
    'Link'  :  contain['Link'],
})
house_set.to_csv(path_or_buf='House_Set.csv', index=False)