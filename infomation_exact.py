import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlite_handle
import certifi
import ssl

def create_legacy_compatible_ssl_context():
   # Some legacy servers reject modern default TLS settings.
   ctx = ssl.create_default_context(cafile=certifi.where())
   if hasattr(ssl, "TLSVersion"):
      ctx.minimum_version = ssl.TLSVersion.TLSv1
   try:
      # Lower OpenSSL security level to allow legacy cipher suites if needed.
      ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
   except ssl.SSLError:
      pass
   return ctx




def url_listup(filename):
   conn = sqlite_handle.create_connection(filename)
   urls = sqlite_handle.select_all_url(conn)
   return urls

async def fetch_subject_info(urls,max_concurrent_requests=5):
   # SSL コンテキストの作成
   ssl_context = create_legacy_compatible_ssl_context()

   # コネクタの作成
   connector = aiohttp.TCPConnector(ssl=ssl_context)
   async with aiohttp.ClientSession(connector=connector) as session:
      tasks = []
      results = []
      for url in urls:
         task = asyncio.create_task(fetch_subject_info_from_url(session, "https://gkmsyllabus.meijo-u.ac.jp"+url[0]))
         tasks.append(task)
         if len(tasks) >= max_concurrent_requests:
            results.append(await asyncio.gather(*tasks))
            tasks = []
      if tasks:
         results.append(await asyncio.gather(*tasks))
      return results

async def fetch_subject_info_from_url(session:aiohttp.ClientSession, url):
   print(f"Fetching subject info from URL: {url}")
   async with session.get(url) as response:
      return await response.text()
   
def do_fetchs(urls):
   loop = asyncio.get_event_loop()
   results = loop.run_until_complete(fetch_subject_info(urls))
   return results
