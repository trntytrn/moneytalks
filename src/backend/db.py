import os

from psycopg import connect, Connection, Cursor

class DBHandler:
    def __init__(self, dbname: str, user: str, password: str, host: str, port: str):
        self.conn: Connection = connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cur: Cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS history (
                user_id TEXT,
                role TEXT,
                content TEXT
            )
        ''')
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()