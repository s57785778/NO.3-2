from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_NAME = 'mydb.db'

# Setup logging
logging.basicConfig(filename='error.log', level=logging.ERROR)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'userid' not in session:
        return redirect('/login')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM member WHERE iid = ?", (session['userid'],))
    user = cursor.fetchone()
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            if not username.isalnum() or len(username) > 10:
                raise ValueError("Invalid username format")
            if not password.isalnum():
                raise ValueError("Invalid password format")

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM member WHERE idno = ? AND pwd = ?", (username, password))
            user = cursor.fetchone()
            if user:
                session['userid'] = user['iid']
                return redirect('/')
            else:
                error = '請輸入正確的帳號密碼'
                return render_template('login.html', error=error)
        except Exception as e:
            logging.error(f"Exception in /login: {e}")
            return render_template('error.html'), 500
    return render_template('login.html')

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if 'userid' not in session:
        return redirect('/login')
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            name = request.form['name']
            birthdate = request.form['birthdate']
            bloodtype = request.form['bloodtype']
            phone = request.form['phone']
            email = request.form['email']
            identity_card = request.form['identity_card']
            password = request.form['password']

            if not identity_card.isalnum() or len(identity_card) > 10:
                raise ValueError("Invalid identity card format")
            if not password.isalnum():
                raise ValueError("Invalid password format")

            cursor.execute("""
                UPDATE member 
                SET nm = ?, birth = ?, blood = ?, phone = ?, email = ?, idno = ?, pwd = ?
                WHERE iid = ?
            """, (name, birthdate, bloodtype, phone, email, identity_card, password, session['userid']))
            conn.commit()
            return redirect('/')
        except Exception as e:
            logging.error(f"Exception in /edit: {e}")
            return render_template('error.html'), 500
    cursor.execute("SELECT * FROM member WHERE iid = ?", (session['userid'],))
    user = cursor.fetchone()
    return render_template('edit.html', user=user)

@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect('/')

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
