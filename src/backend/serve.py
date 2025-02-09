import os
import dotenv

from psycopg import connect, Connection, Cursor
from openai import OpenAI, APITimeoutError
from flask import Flask, make_response, request
from flask_cors import CORS

from db import DBHandler

ROOT_PATH = os.path.abspath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir))

app = Flask(__file__) # init flask app
CORS(app) # support cors

client: OpenAI = None # init openai api client

db_handler: DBHandler = None

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.json.get("user_id")
    user_message = request.json.get("message")

    db_handler.cur.execute('SELECT role, content FROM history WHERE user_id = %s', (user_id,))
    history = db_handler.cur.fetchall()

    if not history:
        history = [
            {
                "role": "developer",
                "content": "Hello! You are MoneyTalksAI. You are an assistant for providing professional financial advice. You should focus on providing primarily budgeting and investment advice, but you can provide any advice within the realm of finance."
            }
        ]
        db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, "developer", history[0]["content"]))
    else:
        history = [{"role": role, "content": content} for role, content in history]

    history.append({"role": "user", "content": user_message})
    db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, "user", user_message))

    try:
        _r = client.chat.completions.create(
            model = "gpt-4o",
            messages = history,
            timeout = 15
        )
        response_message = _r.choices[0].message.content
        history.append({"role": "assistant", "content": response_message})
        db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, "assistant", response_message))
        db_handler.conn.commit()
        return make_response({"status": 0, "msg": response_message})
    except APITimeoutError:
        return make_response({"status": 0, "msg": "OpenAI API request timed out, try again in a few seconds"})

if __name__ == "__main__":
    dotenv.load_dotenv(os.path.join(ROOT_PATH, ".env"))
    db_handler = DBHandler(os.environ['DB_NAME'], os.environ['DB_USER'], os.environ['DB_PASSWORD'], os.environ['DB_HOST'], os.environ['DB_PORT'])

    client = OpenAI(api_key = os.environ["OPENAI_API_KEY"])

    app.run(port = 3000, debug = True)