import sqlite3
from db_setup import *

def get_user(phone):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT phone, mobile, name FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"phone": row[0], "mobile": row[1], "name": row[2]}
    return None

def create_user(phone, mobile, name):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (phone, mobile, name) VALUES (?, ?, ?)", (phone, mobile, name))
    conn.commit()
    conn.close()

def get_tasks(phone):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT task FROM tasks WHERE phone = ?", (phone,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_task(phone, task):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (phone, task) VALUES (?, ?)", (phone, task))
    conn.commit()
    conn.close()

def update_task(phone, index, new_task):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE phone = ?", (phone,))
    ids = cursor.fetchall()
    if 0 <= index < len(ids):
        task_id = ids[index][0]
        cursor.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_task, task_id))
        conn.commit()
    conn.close()
