import sqlite3

DB_PATH = 'database/finance.db'

username = 'admin'  # 🔁 Change this
email = 'rajkumarag543@gmail.com'  # 🔁 Change this

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("UPDATE users SET email=? WHERE username=?", (email, username))
    conn.commit()

print("✅ Email updated successfully.")
