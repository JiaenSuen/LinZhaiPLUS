import subprocess
import sys

exe1 = 'Crawler_url_set.py'
exe2 = 'Crawler_Info.py'
result_exe1 = subprocess.run(['python', exe1], capture_output=True, encoding='utf-8', errors='ignore')

 
if result_exe1.returncode == 0:
    print( exe1 + "  執行成功")
 
    result_exe2 = subprocess.run(['python', exe2], capture_output=True, encoding='utf-8', errors='ignore')
    if result_exe2.returncode == 0:
        print(exe2 + " 執行成功")
    else:
        print(exe2 + " 執行失敗")
        print(result_exe2.stderr)   
else:
    print(exe1 + " 執行失敗")
    print(result_exe1.stderr)   
