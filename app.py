from flask import Flask, render_template, request, redirect, session, url_for, make_response, send_file

import sqlite3
from datetime import datetime
from xhtml2pdf import pisa
from io import BytesIO
from itsdangerous import URLSafeTimedSerializer
from flask import flash
import smtplib


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to something unique
# For generating and verifying reset tokens
s = URLSafeTimedSerializer(app.secret_key)
DB_PATH = 'database/finance.db'

# ----- INIT DB -----
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Transactions table (linked to user_id)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
                # Reminder table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')
        app = Flask(__name__)

        import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    sender_email = "rajkumarag543@gmail.com"           # ✅ Your email
    sender_password = "qjehbgbvmjobzplr"                # ✅ App password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    from flask import flash



# ----- ROUTES -----
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    month = request.args.get('month')
    year = request.args.get('year')

    where_clause = "WHERE user_id = ?"
    params = [user_id]

    if month and year:
        where_clause += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.extend([month.zfill(2), year])

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(f"SELECT * FROM transactions {where_clause} ORDER BY date DESC", params)
        transactions = cursor.fetchall()

        income = conn.execute(f"SELECT SUM(amount) FROM transactions {where_clause} AND type='Income'", params).fetchone()[0] or 0
        expense = conn.execute(f"SELECT SUM(amount) FROM transactions {where_clause} AND type='Expense'", params).fetchone()[0] or 0

        # 🔥 Add this — Properly aligned reminder block
        cursor = conn.execute("SELECT * FROM reminders WHERE user_id=? AND due_date >= date('now') ORDER BY due_date", (user_id,))
        reminders = cursor.fetchall()

    return render_template('index.html',
                           transactions=transactions,
                           income=income,
                           expense=expense,
                           reminders=reminders,
                           selected_month=month,
                           selected_year=year)


  


@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        user_id = session['user_id']
        date = request.form['date']
        t_type = request.form['type']
        category = request.form['category']
        amount = float(request.form['amount'])
        notes = request.form['notes']
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO transactions (user_id, date, type, category, amount, notes) VALUES (?, ?, ?, ?, ?, ?)",
                         (user_id, date, t_type, category, amount, notes))
        return redirect('/')
    return render_template('add.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect('/')
            else:
                return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    month = request.args.get('month')
    year = request.args.get('year')

    where_clause = "WHERE user_id = ?"
    params = [user_id]

    if month and year:
        where_clause += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.extend([month.zfill(2), year])

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(f"""
            SELECT category, 
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS total_income,
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS total_expense
            FROM transactions
            {where_clause}
            GROUP BY category
        """, params)
        data = cursor.fetchall()

        # Total income/expense
        income_total = conn.execute("SELECT SUM(amount) FROM transactions " + where_clause + " AND type='Income'", params).fetchone()[0] or 0
        expense_total = conn.execute("SELECT SUM(amount) FROM transactions " + where_clause + " AND type='Expense'", params).fetchone()[0] or 0
        net_total = income_total - expense_total

    categories = [row[0] for row in data]
    income_values = [row[1] for row in data]
    expense_values = [row[2] for row in data]

    return render_template('dashboard.html',
                           categories=categories,
                           income=income_values,
                           expense=expense_values,
                           income_total=income_total,
                           expense_total=expense_total,
                           net_total=net_total,
                           selected_month=month,
                           selected_year=year)


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import make_response

@app.route('/export-pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    month = request.args.get('month')
    year = request.args.get('year')

    where_clause = "WHERE user_id = ?"
    params = [user_id]

    if month and year:
        where_clause += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.extend([month.zfill(2), year])

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(f"SELECT date, type, category, amount, notes FROM transactions {where_clause} ORDER BY date DESC", params)
        transactions = cursor.fetchall()

        income = conn.execute(f"SELECT SUM(amount) FROM transactions {where_clause} AND type='Income'", params).fetchone()[0] or 0
        expense = conn.execute(f"SELECT SUM(amount) FROM transactions {where_clause} AND type='Expense'", params).fetchone()[0] or 0
        net = income - expense

    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "Finance Report")

    p.setFont("Helvetica", 12)
    if month and year:
        p.drawString(200, 780, f"Month: {month}/{year}")

    # Totals
    p.drawString(50, 750, f"Total Income: ₹{income}")
    p.drawString(250, 750, f"Total Expense: ₹{expense}")
    p.drawString(450, 750, f"Profit: ₹{net}")

    # Table Header
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 720, "Date")
    p.drawString(110, 720, "Type")
    p.drawString(170, 720, "Category")
    p.drawString(300, 720, "Amount")
    p.drawString(370, 720, "Notes")

    # Transactions
    y = 700
    p.setFont("Helvetica", 9)
    for t in transactions:
        if y < 50:
            p.showPage()
            y = 800
        p.drawString(50, y, t[0])
        p.drawString(110, y, t[1])
        p.drawString(170, y, t[2])
        p.drawString(300, y, f"₹{t[3]}")
        p.drawString(370, y, t[4] or "")
        y -= 18

    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Finance_Report.pdf", mimetype='application/pdf')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
                return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username already taken. Try again."
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE email=?", (email,))
            user = cursor.fetchone()
            if user:
                try:
                    token = s.dumps(email, salt='password-reset')
                    reset_link = url_for('reset_password', token=token, _external=True)

                    # Send email
                    subject = "Reset your password"
                    body = f"Click the link to reset your password:\n{reset_link}"
                    send_email(email, subject, body)

                    flash("✅ Reset link sent to your email.")
                except Exception as e:
                    print(f"❌ Email failed: {e}")
                    flash("❌ Failed to send email. Please try again.")
            else:
                flash("❌ Email not found.")
        return redirect('/forgot-password')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiry
    except:
        return "Reset link expired or invalid."

    if request.method == 'POST':
        new_password = request.form['password']
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        flash("✅ Password reset successful. Please login.")
        return redirect('/login')

    return render_template('reset_password.html')





# ----- MAIN -----
if __name__ == '__main__':
    init_db()
    # DO NOT run app here — Render uses gunicorn

