import sqlite3

def get_user(phone):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT phone, mobile, name FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    return {"phone": row[0], "mobile": row[1], "name": row[2]} if row else None

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
    tasks = cursor.fetchall()
    conn.close()
    return [t[0] for t in tasks]

# def get_tasks_update(phone):
#     conn = sqlite3.connect("user_data.db")
#     cursor = conn.cursor()
#
#     if status:
#         cursor.execute("SELECT task, status FROM tasks WHERE phone = ? AND status = ?", (phone, status))
#     else:
#         cursor.execute("SELECT task FROM tasks WHERE phone = ?", (phone,))
#
#     tasks = cursor.fetchall()
#     conn.close()
#     return tasks,status  # returns list of tuples (task, status)
def get_tasks_update(phone):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT task, status FROM tasks WHERE phone = ?", (phone,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_tasks_update_status_data(phone):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE task, SET status = 'Done' WHERE phone = ?", (phone,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

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

def update_task_status(phone, index, status):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Convert index to integer
    try:
        index = int(index)
    except ValueError:
        print("❌ Invalid index. Must be a number.")
        conn.close()
        return

    cursor.execute("SELECT id FROM tasks WHERE phone = ?", (phone,))
    ids = cursor.fetchall()

    if 0 <= index < len(ids):
        task_id = ids[index][0]
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()
    else:
        print("❌ Task index out of range.")

    conn.close()


