import sqlite3
import os

DB_PATH = "/app/data/users_data.db"
if not os.path.exists("/app"):
    DB_PATH = "data/users_data.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            profile_name TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY (profile_name, key)
        )
    ''')
    conn.commit()
    conn.close()

def save_user_data(profile_name: str, key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_data (profile_name, key, value)
        VALUES (?, ?, ?)
    ''', (profile_name, key, value))
    conn.commit()
    conn.close()

def get_user_data(profile_name: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM user_data WHERE profile_name = ?', (profile_name,))
    rows = cursor.fetchall()
    conn.close()
    return {k: v for k, v in rows}

def get_all_profiles() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT profile_name FROM user_data')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
