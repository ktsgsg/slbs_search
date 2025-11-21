from bs4 import BeautifulSoup

def setlist_parser(html_content):
   soup = BeautifulSoup(html_content, 'html.parser')
   form = soup.find('form',id='form')
   divs = form.find_all('div',class_='contents_1')
   for div in divs:
      inputs = div.find('input', {'type': 'hidden', 'name': 'buttonName'})
      if inputs:
         #div内にtableは2つ以上あるが最初のものを取得
         table = div.find('table',class_='list')
         return table_tolist(table)

#見つけたテーブルをリストへ変換
def table_tolist(table:BeautifulSoup):
   #classがcolumn_oddまたはcolumn_evenのtrをすべて取得
   rows = table.find_all('tr', class_=['column_odd', 'column_even'])
   #print('count of rows:', len(rows))
   subjects = []
   for row in rows:
      subjects.append(table_toclass(row))
   return subjects

def table_toclass(tablelist:BeautifulSoup):
   td = tablelist.find_all('td')
   code = td[1].get_text(strip=True)
   name = td[2].get_text(strip=True)
   place_and_time = td[3].string.replace('<br>',',').strip() if td[3].string else ''
   teachers = td[4].get_text(separator=',',strip=True)
   url = td[2].find('a')['href'] if td[2].find('a') else ''
   subject_instance = subject(code,name,place_and_time,teachers,url)
   #print(subject_instance.name)
   return subject_instance
   

class subject:
   def __init__(self,code,name,place_and_time,teachers,url):
      self.code=code
      self.name=name
      self.place_and_time=place_and_time
      if place_and_time=='':
         self.place_and_time='none'
      self.teachers=teachers
      self.url=url