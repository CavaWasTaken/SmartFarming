from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import psycopg2 
from psycopg2 import sql
import bcrypt

def get_db_connection():
    return psycopg2.connect(
        dbname="smartfarm_db",  # db name
        user="iotproject",  # username postgre sql
        password="WeWillDieForIoT", # password postgre sql
        host="localhost",    # host,
        port="5433" # port
    )



app = Flask(__name__)
CORS(app)


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert user data into PostgreSQL
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute(sql.SQL("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"), [username, email, hashed_password])
        conn.commit()
            
        user_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"user_id": user_id, "username": username}), 201  # Success response
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Error response


if __name__ == "__main__":
    app.run(debug=True)
