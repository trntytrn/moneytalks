import os
import dotenv
from datetime import datetime
from openai import OpenAI, APITimeoutError
from flask import Flask, make_response, request
from flask_cors import CORS
from db import DBHandler
import jwt

ROOT_PATH = os.path.abspath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir))

app = Flask(__file__) # init flask app
CORS(app) # support cors

client: OpenAI = None # init openai api client
db_handler: DBHandler = None

SYSTEM_PROMPT = {
    "role": "system",
    "content": "Hello! You are MoneyTalksAI. You are an assistant for providing professional financial advice. You should focus on providing primarily budgeting and investment advice, but you can provide any advice within the realm of finance."
}

SECRET_KEY = None

def get_user_goals(user_id):
    goals: dict[str, str] = {
        "long_term_goal": None,
        "short_term_goal": None
    }
    try:
        db_handler.cur.execute('SELECT long_term_goal FROM users WHERE user_id = %s', (user_id,))
        lt_goal = db_handler.cur.fetchone()
        db_handler.cur.execute('SELECT short_term_goal FROM users WHERE user_id = %s', (user_id,))
        st_goal = db_handler.cur.fetchone()
        if lt_goal:
            goals.update({"long_term_goal": lt_goal})
        if st_goal:
            goals.update({"short_term_goal": st_goal})
        return goals
    except Exception as e:
        print(f"Error retrieving user goals: {e}")
        return None

@app.route("/chat", methods = ["POST"])
def chat():
    user_id = str(request.json.get("user_id"))
    user_message = request.json.get("message")

    user_goals = get_user_goals(user_id)
    if user_goals:
        system_prompt = SYSTEM_PROMPT.copy()
        system_prompt["content"] += f" The user's goals are (in dictionary format): {user_goals}\n\nKeep in mind these goals when providing advice and guidance."
    else:
        system_prompt = SYSTEM_PROMPT
    db_handler.cur.execute('SELECT role, content FROM history WHERE user_id = %s', (user_id,))
    history = db_handler.cur.fetchall()
    print(history)

    if not history:
        history = [system_prompt]
    else:
        history = [{"role": role, "content": content} for role, content in history]

    history.append({"role": "user", "content": user_message})
    db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, "user", user_message))

    try:
        _r = client.chat.completions.create(
            model="gpt-4o",
            messages=history,
            timeout=15
        )
        response_message = _r.choices[0].message.content
        history.append({"role": "assistant", "content": response_message})
        db_handler.cur.execute('INSERT INTO history (user_id, role, content) VALUES (%s, %s, %s)', (user_id, "assistant", response_message))
        db_handler.conn.commit()
        return make_response({"status": 0, "msg": response_message})
    except APITimeoutError:
        return make_response({"status": 0, "msg": "OpenAI API request timed out, try again in a few seconds"})

@app.route("/update-payday", methods = ["POST"])
def update_payday():
    user_id = request.json.get("user_id")
    next_payday = request.json.get("next_payday")
    payday_frequency = request.json.get("payday_frequency")

    if not user_id or not next_payday or not payday_frequency:
        return make_response({"status": 1, "msg": "Missing required fields"}, 400)

    try:
        next_payday_date = datetime.strptime(next_payday, "%Y-%m-%d")
        db_handler.cur.execute('''
            UPDATE users
            SET next_payday = %s, payday_frequency = %s
            WHERE user_id = %s
        ''', (next_payday_date, payday_frequency, user_id))
        db_handler.conn.commit()
        return make_response({"status": 0, "msg": "Payday information updated successfully"})
    except Exception as e:
        return make_response({"status": 1, "msg": str(e)}, 500)

@app.route("/create-user", methods=["POST"])
def create_user():
    user_id = request.json.get("user_id")
    username = request.json.get("username")
    email = request.json.get("email")
    password = request.json.get("password")

    if not user_id or not username or not email or not password:
        return make_response({"status": 1, "msg": "Missing required fields"}, 400)

    try:
        db_handler.cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = db_handler.cur.fetchone()
        if existing_user:
            return make_response({"status": 1, "msg": "User with this email already exists"}, 400)

        db_handler.cur.execute('''
            INSERT INTO users (user_id, username, email, password)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, username, email, password))
        db_handler.conn.commit()
        return make_response({"status": 0, "msg": "User created successfully"})
    except Exception as e:
        return make_response({"status": 1, "msg": str(e)}, 500)

@app.route("/validate-token", methods=["POST"])
def validate_token():
    token = request.headers.get('Authorization').split(' ')[1]
    if not token:
        return make_response({"valid": False}, 401)

    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return make_response({"valid": True})
    except jwt.ExpiredSignatureError:
        return make_response({"valid": False}, 401)
    except jwt.InvalidTokenError:
        return make_response({"valid": False}, 401)

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return make_response({"message": "Missing required fields"}, 400)

    try:
        db_handler.cur.execute('SELECT user_id, password FROM users WHERE username = %s', (username,))
        user = db_handler.cur.fetchone()
        if user and user['password'] == password:
            user_id = user['user_id']
            token = jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")
            return make_response({"token": token})
        else:
            return make_response({"message": "Invalid credentials"}, 401)
    except Exception as e:
        return make_response({"message": str(e)}, 500)

@app.route("/clear-history", methods=["POST"])
def clear_history():
    user_id = str(request.json.get("user_id"))

    if not user_id:
        return make_response({"status": 1, "msg": "Missing user ID"}, 400)

    try:
        db_handler.cur.execute('DELETE FROM history WHERE user_id = %s', (user_id,))
        db_handler.conn.commit()
        return make_response({"status": 0, "msg": "Chat history cleared successfully"})
    except Exception as e:
        return make_response({"status": 1, "msg": str(e)}, 500)

if __name__ == "__main__":
    dotenv.load_dotenv(os.path.join(ROOT_PATH, ".env"))
    SECRET_KEY = os.environ['SECRET_KEY']
    db_handler = DBHandler(os.environ['DB_NAME'], os.environ['DB_USER'], os.environ['DB_PASSWORD'], os.environ['DB_HOST'], os.environ['DB_PORT'])
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    app.run(port=3000, debug=True)