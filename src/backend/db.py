import os

from psycopg import connect, Connection, Cursor

class DBHandler(object):
    conn: Connection = None
    cur: Cursor = None

    def __init__(self, dbname, user, password, host, port):
        self.conn = connect(
            dbname = dbname,
            user = user,
            password = password,
            host = host,
            port = port
        )
        self.cur = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()