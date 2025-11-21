import requests
import certifi
from bs4 import BeautifulSoup
from OpenSSL import crypto
from urllib3.contrib import pyopenssl
import urllib.parse
import setlist
import sqlite_handle

pyopenssl.inject_into_urllib3()# OpenSSLをurllib3に注入

def main():
   url = 'https://gkmsyllabus.meijo-u.ac.jp/camweb/slbssrch.do'
   try:
      resp = requests.get(url, verify=certifi.where(), timeout=15)
   except requests.exceptions.RequestException as e:
      print(f"Error fetching the page: {e}")
      return
   #cookieをjson形式で保存
   cookies = resp.cookies.get_dict()
   #textをパース
   soup = BeautifulSoup(resp.text, 'html.parser')
   #hiddenのtimestampを取得
   timestamp_input = get_timestamp(resp.text)
   #なかったら終わり
   if timestamp_input is None:
      print("timestamp not found in the page.")
      return
   #成功
   print("Successfully fetched the page and parsed timestamp.")
   
   #sqliteの接続を作成
   database = "subjects.db"
   conn = sqlite_handle.create_connection(database)
   if conn is None:
      print("Error! cannot create the database connection.")
      return
   print("Successfully connected to the database.")
   
   #subjectsテーブルを作成
   sql_create_subjects_table = """ CREATE TABLE IF NOT EXISTS subjects (
                                       id integer PRIMARY KEY,
                                       code text NOT NULL,
                                       name text NOT NULL,
                                       place_and_time text,
                                       teachers text,
                                       url text
                                 ); """
   sqlite_handle.create_table(conn, sql_create_subjects_table)
   
   #POST用パラメータを作成
   query_str = "value%28methodname%29=sylkougi_search&buttonName=searchKougi&timestamp=????&value%28nendo%29=2025&value%28searchDetailConditionFlag%29=2&value%28kouginm%29=&value%28searchDetailConditionFlag%29=2&value%28syokunm%29=&value%28searchDetailConditionFlag%29=2&value%28keywords%29=&value%28searchKeywordFlg%29=1&value%28searchDetailConditionFlag%29=2&value%28kkikancd%29=&value%28searchDetailConditionFlag%29=2&value%28grade%29=&value%28searchDetailConditionFlag%29=2&value%28searchDetailConditionFlag%29=2&value%28crclm%29=&value%28searchDetailConditionFlag%29=2&value%28bunya%29="
   first_query = set_params(timestamp_input,query_str)
   
   #ここでPOSTリクエストを送信
   try:
      post_resp = requests.post(url, data=first_query, cookies=cookies, verify=certifi.where(), timeout=15)
      with open("response.html","w",encoding="utf-8") as f:
         f.write(post_resp.text)
      print("POST request successful, response saved to response.html")
   except requests.exceptions.RequestException as e:
      print(f"Error during POST request: {e}")
      return
   #cookieの更新
   cookies = post_resp.cookies.get_dict()
   #ページのtimestampを取得
   timestamp_input = get_timestamp(post_resp.text)
   if timestamp_input is None:
      print("timestamp not found in the POST response page.")
      return
   
   #ページ内の表示数を200にする
   query_str = "buttonName=&timestamp=????&maxDispListCount=200&value%28pageCount%29=&value%28maxCount%29=200&navigateKougiList=dummy&maxDispListCount=10&value%28pageCount%29=&value%28maxCount%29=&dummy=dummy"
   second_query = set_params(timestamp_input,query_str)
   print("Prepared second POST parameters to set display count to 200:")
   
   #POSTリクエストを送信
   try:
      post_resp = requests.post(url,data=second_query,cookies=cookies, verify=certifi.where(), timeout=15)
      print("Second POST request successful, response saved to response.html")
      with open("response.html","w",encoding="utf-8") as f:
         f.write(post_resp.text)
   except requests.exceptions.RequestException as e:
      print(f"Error during second POST request: {e}")
      return
   
   #cookieの更新
   cookies = post_resp.cookies.get_dict()
   #取得したページをパースして科目リストを取得
   subjects = setlist.setlist_parser(post_resp.text)
   #次のページを読み込む
   timestamp_input = get_timestamp(post_resp.text)
   if timestamp_input is None:
      print("timestamp not found for next page.")
      return
   #subjectsをDBに保存
   for subject in subjects:
      subject_id = sqlite_handle.insert_subject(conn, subject)
   print(f"Inserted {len(subjects)} subjects into the database.")
   
   #各ページに対して処理を行う
   for i in range(2,100):
      #次のページのパラメータを作成
      param = setparam_to_nextpage(timestamp_input, i)
      try:
         post_resp = requests.post(url, data=param, cookies=cookies, verify=certifi.where(), timeout=15)
         print(f"POST request for page {i} successful.")
         
         #timestampを更新
         timestamp_input = get_timestamp(post_resp.text)
         if timestamp_input is None:
            print("timestamp not found for next page.")
            return
         subjects = setlist.setlist_parser(post_resp.text)
         print(f"Parsed subjects for page {i}, count: {len(subjects)}")
         
         #subjectsをDBに保存
         for subject in subjects:
            subject_id = sqlite_handle.insert_subject(conn, subject)
         print(f"Inserted {len(subjects)} subjects into the database.")
      except requests.exceptions.RequestException as e:
         print(f"Error during POST request for page {i}: {e}")
         continue
      
   
def setparam_to_nextpage(timestamp_input, page_number):
   query_str = "buttonName=&timestamp=1763703822608&maxDispListCount=200&value%28pageCount%29=3&value%28maxCount%29=200&navigateKougiList=dummy&maxDispListCount=200&value%28pageCount%29=2&value%28maxCount%29=200&dummy=dummy"
   param = set_params(timestamp_input,query_str)
   param['value(pageCount)'] = str(page_number)
   return param
def get_timestamp(text):
   soup = BeautifulSoup(text, 'html.parser')
   timestamp_input = soup.find('input', {'type': 'hidden', 'name': 'timestamp'})
   if timestamp_input:
      return timestamp_input['value']
   return None

def set_params(timestamp_input,query_str):
   #URLデコードして辞書に変換
   query_params = urllib.parse.parse_qs(query_str)
   #timestampを置換
   query_params['timestamp'] = [timestamp_input]
   #値のリストを文字列に変換
   return {k: v[0] for k, v in query_params.items()}
   
   

if __name__ == "__main__":
   main()