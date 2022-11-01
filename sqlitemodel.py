import sqlite3

class SqliteModel:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.cur = self.conn.cursor()
    def __del__(self):
        self.conn.close()
