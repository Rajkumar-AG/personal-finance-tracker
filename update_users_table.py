import sqlite3

DB_PATH = 'database/finance.db'  # Change path if needed

with sqlite3.connect(DB_PATH) as conn:
    try:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("✅ Email column added successfully.")
    except Exception as e:
        print("⚠️ Error:", e)
