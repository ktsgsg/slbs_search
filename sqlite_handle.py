import sqlite3
import setlist

def create_connection(db_file):
   """ create a database connection to the SQLite database
      specified by db_file
   :param db_file: database file
   :return: Connection object or None
   """
   conn = None
   try:
      conn = sqlite3.connect(db_file)
      return conn
   except sqlite3.Error as e:
      print(e)

   return conn

def create_table(conn, create_table_sql):
   """ create a table from the create_table_sql statement
   :param conn: Connection object
   :param create_table_sql: a CREATE TABLE statement
   :return:
   """
   try:
      c = conn.cursor()
      c.execute(create_table_sql)
   except sqlite3.Error as e:
      print(e)
      
def insert_subject(conn, subject:setlist.subject):
   """
   Create a new subject into the subjects table
   :param conn:
   :param subject:
   :return: subject id
   """
   sql = ''' INSERT INTO subjects(code,name,place_and_time,teachers,url)VALUES(?,?,?,?,?) '''
   cur = conn.cursor()
   cur.execute(sql, (subject.code, subject.name, subject.place_and_time, subject.teachers, subject.url))
   conn.commit()
   return cur.lastrowid

def select_all_code_and_url(conn):
   """
   Query all rows in the subjects table
   :param conn: the Connection object
   :return:
   """
   cur = conn.cursor()
   cur.execute("SELECT url FROM subjects")
   conn.commit()
   rows = cur.fetchall()
   
   return rows