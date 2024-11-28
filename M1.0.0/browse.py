from selenium import webdriver
from PIL import Image
import time
import os
options = webdriver.ChromeOptions()
options.add_argument('headless')  


driver = webdriver.Chrome(options=options)


driver.set_window_size(1920, 1080)  



# 假設 HTML 文件位於當前工作目錄
file_path = os.path.abspath('map.html')  # 轉換為絕對路徑
driver.get(f'file://{file_path}')
time.sleep(3)
driver.save_screenshot('map.png')  


driver.quit()

 

 
