import sqlite3

def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            mobile TEXT,
            name TEXT
        )
    ''')

    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            task TEXT,
            status TEXT,
            FOREIGN KEY(phone) REFERENCES users(phone) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


# def ensure_status_column():
#     conn = sqlite3.connect("user_data.db")
#     cursor = conn.cursor()
#
#     # Check if 'status' column exists
#     cursor.execute("PRAGMA table_info(tasks)")
#     columns = [info[1] for info in cursor.fetchall()]
#
#     if 'status' not in columns:
#         cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT")
#         print("✅ 'status' column added.")
#     else:
#         print("ℹ️ 'status' column already exists.")
#
#     conn.commit()
#     conn.close()


if __name__ == "__main__":
    init_db()
