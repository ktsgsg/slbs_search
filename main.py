import os
import subprocess
import requests
from bs4 import BeautifulSoup
import time

def main():
   rslt =subprocess.run(['zsh', 'slbs1.http'], capture_output=True, text=True).stdout
   cookie = rslt.splitlines()[13].split(';')[0].split(':')[1]
   print('cookie:', cookie)
   #ファイルに書き込み
   source = BeautifulSoup(rslt, 'html.parser')
   timestamp = source.find('input', {'name': 'timestamp'})['value']
   print('timestamp:', timestamp)
   with open('slbs2.http','r') as f:
      data = f.read()
   data = data.replace('????', timestamp)
   with open('slbs2_alt.http','w') as f:
      f.write(data)
   time.sleep(1) #待機
   rslt2 =subprocess.run(['zsh', 'slbs2_alt.http'], capture_output=True, text=True).stdout
   #print(rslt2)

if __name__ == "__main__":
   main()