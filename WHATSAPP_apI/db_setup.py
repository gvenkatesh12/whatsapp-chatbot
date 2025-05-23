import sqlite3

def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            mobile TEXT,
            name TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            task TEXT,
            FOREIGN KEY(phone) REFERENCES users(phone)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
