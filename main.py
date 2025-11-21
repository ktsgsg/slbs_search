import os
import subprocess
import requests
import certifi
from bs4 import BeautifulSoup
import time
import tempfile
from OpenSSL import crypto
from urllib3.contrib import pyopenssl

pyopenssl.inject_into_urllib3()

def main():
   try:
      resp = requests.get('https://gkmsyllabus.meijo-u.ac.jp/camweb/slbssrch.do', verify=certifi.where(), timeout=15)
   except requests.exceptions.RequestException as e:
      print(f"Error fetching the page: {e}")
      return
   print(resp.text)

# 例：既に持っている X509 / PKey オブジェクトを仮定
# cert = crypto.load_certificate(crypto.FILETYPE_PEM, open("client_cert.pem").read())
# pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, open("client_key.pem").read())
# ここでは上のようにロードした cert/pkey を使う想定

def use_cert_and_request(cert_obj, pkey_obj, url):
    # PEM に変換
    cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert_obj)
    key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey_obj)

    # 安全に一時ファイルに書く
    cert_file = tempfile.NamedTemporaryFile(delete=False)
    key_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        cert_file.write(cert_pem)
        cert_file.close()
        key_file.write(key_pem)
        key_file.close()
        os.chmod(key_file.name, 0o600)  # キーファイルは読み取り権限を限定

        session = requests.Session()
        resp = session.get(url, cert=(cert_file.name, key_file.name), verify=certifi.where(), timeout=15)
        return resp
    finally:
        # 後片付け：必要に応じてファイルを消す
        os.remove(cert_file.name)
        os.remove(key_file.name)

if __name__ == "__main__":
   main()