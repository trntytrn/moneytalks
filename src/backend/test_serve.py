import os
import unittest
import json
import dotenv

from openai import APITimeoutError

from serve import app, db_handler

class TestServe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dotenv.load_dotenv(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '.env'))
        db_handler.init_db()
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_chat_endpoint(self):
        user_id = "test_user"
        user_message = "What should I do with my monthly paycheck?"

        response = self.client.post("/chat", json={"user_id": user_id, "message": user_message})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("msg", data)
        self.assertEqual(data["status"], 0)

    def test_chat_endpoint_timeout(self):
        user_id = "test_user"
        user_message = "This message will cause a timeout."

        with unittest.mock.patch('src.backend.serve.client.chat.completions.create', side_effect=APITimeoutError):
            response = self.client.post("/chat", json={"user_id": user_id, "message": user_message})
            data = json.loads(response.data)

            self.assertEqual(response.status_code, 200)
            self.assertIn("msg", data)
            self.assertEqual(data["msg"], "OpenAI API request timed out, try again in a few seconds")

if __name__ == '__main__':
    unittest.main()
