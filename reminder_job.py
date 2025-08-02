import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import date
import schedule
import time

DB_PATH = 'database/finance.db'

EMAIL_ADDRESS = 'rajkumar543gmail@gmail.com'           # 🔁 Replace with your Gmail
EMAIL_PASSWORD = 'qjeh bgbv mjob zplr'   # 🔁 Replace with app password

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_and_send_reminders():
    today = str(date.today())
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Get due reminders with user email
        cursor.execute("""
            SELECT reminders.title, reminders.notes, users.email 
            FROM reminders 
            JOIN users ON reminders.user_id = users.id 
            WHERE reminders.due_date = ?
        """, (today,))
        reminders = cursor.fetchall()

        for title, notes, email in reminders:
            body = f"Reminder: {title}\n\n{notes}\n\nDue Today: {today}"
            send_email(email, f"Reminder: {title}", body)
            print(f"Sent reminder to {email}: {title}")

# 🔁 Run once now for test
check_and_send_reminders()

# 🔁 If you want to run daily at 8 AM, uncomment below:
# schedule.every().day.at("08:00").do(check_and_send_reminders)
# while True:
#     schedule.run_pending()
#     time.sleep(60)
