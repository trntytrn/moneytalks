import os
import unittest

from psycopg import connect

from db import DBHandler

class TestDBHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_handler = DBHandler(
            dbname=os.environ['TEST_DB_NAME'],
            user=os.environ['TEST_DB_USER'],
            password=os.environ['TEST_DB_PASSWORD'],
            host=os.environ['TEST_DB_HOST'],
            port=os.environ['TEST_DB_PORT']
        )

    @classmethod
    def tearDownClass(cls):
        cls.db_handler.close()

    def test_init_db(self):
        self.db_handler.cur.execute("SELECT to_regclass('public.history')")
        table_exists = self.db_handler.cur.fetchone()[0]
        self.assertEqual(table_exists, 'history')

    def test_insert_and_fetch_history(self):
        user_id = "test_user"
        role = "user"
        content = "This is a test message."

        self.db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, role, content))
        self.db_handler.conn.commit()

        self.db_handler.cur.execute('SELECT role, content FROM history WHERE user_id = %s', (user_id,))
        history = self.db_handler.cur.fetchall()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][0], role)
        self.assertEqual(history[0][1], content)

if __name__ == '__main__':
    unittest.main()
