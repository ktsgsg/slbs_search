import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlite_handle
import certifi
import ssl
import re
import json

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
   datas = sqlite_handle.select_all_code_and_url(conn)
   return datas

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


def normalize_text(text):
   return re.sub(r"\s+", " ", text).strip()


def cell_text(cell):
   return normalize_text(cell.get_text("\n", strip=True))


def detect_list_table(table):
   rows = table.find_all("tr")
   headers = []
   items = []

   for row in rows:
      cells = row.find_all("td", recursive=False)
      if not cells:
         continue

      texts = [cell_text(c) for c in cells]
      if not any(texts):
         continue

      header_candidates = [t for t in texts if t.startswith("【") and t.endswith("】")]
      if header_candidates and len(header_candidates) >= 1:
         headers = [h.strip("【】") for h in header_candidates]
         continue

      first = texts[0]
      number_match = re.match(r"^(\d+)\.$", first)
      if not number_match:
         continue

      values = texts[1:]
      if not any(values):
         continue

      entry = {"no": int(number_match.group(1))}
      if headers and len(headers) == len(values):
         for key, value in zip(headers, values):
            entry[key] = value
      else:
         for idx, value in enumerate(values, start=1):
            entry[f"col{idx}"] = value
      items.append(entry)

   if not items:
      return None

   return {
      "headers": headers,
      "items": items,
   }


def parse_subject_info_html(html_content, subject_id=None):
   soup = BeautifulSoup(html_content, "html.parser")

   form = soup.find("form", {"name": "sylbsActionForm"})
   if form is None:
      return {"id": subject_id, "fields": {}, "lists": {}}

   fields = {}
   lists = {}

   tables = form.find_all("table", class_="syllabus_detail")
   for table in tables:
      for row in table.find_all("tr"):
         cells = row.find_all("td", recursive=False)
         if len(cells) < 3:
            continue

         label = cell_text(cells[0])
         if not label:
            continue

         value_cell = cells[-1]
         nested_tables = value_cell.find_all("table")
         detected = None
         for nested_table in nested_tables:
            detected = detect_list_table(nested_table)
            if detected is not None:
               break

         if detected is not None:
            lists[label] = detected
            continue

         value = cell_text(value_cell)
         fields[label] = value

   return {
      "id": subject_id,
      "fields": fields,
      "lists": lists,
   }


def parse_subject_info_file(file_path, subject_id=None):
   with open(file_path, "r", encoding="utf-8") as f:
      return parse_subject_info_html(f.read(), subject_id=subject_id)


def save_subject_info_json_from_html(html_content, output_json_path, subject_id=None, indent=2):
   data = parse_subject_info_html(html_content, subject_id=subject_id)
   with open(output_json_path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=indent)
   return data


def save_subject_info_json(input_html_path, output_json_path, subject_id=None, indent=2):
   data = parse_subject_info_file(input_html_path, subject_id=subject_id)
   with open(output_json_path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=indent)
   return data