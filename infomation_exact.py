import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlite_handle

def url_listup(filename):
   conn = sqlite_handle.create_connection(filename)
   urls = sqlite_handle.select_all_url(conn)
   return urls


