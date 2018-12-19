import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

app.secret_key = os.urandom(16).__repr__()

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        isbn = request.form['isbn'] 


    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        password_confirm = request.form['password-confirm']
        if not name:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not password == password_confirm:
            error = 'Password confirming not consistent.'
        elif db.execute(
            'SELECT * FROM users WHERE name = :name', {'name': name}
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(name)
        if error is None:
            db.execute(
                'INSERT INTO users (name, password) VALUES (:name, :password)',
                {'name': name, 'password': password}
            )
            db.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route("/login", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        password_typed = request.form['password']
        if not name or not password_typed:
            error = 'Fields not filled complete.'

        try:
            password = db.execute(
                'SELECT password FROM users WHERE name = :name', {'name': name}
            ).fetchone().password
        except AttributeError:
            error = f"User '{name}' does not exit."
        else:
            if password != password_typed:
                error = f"Wrong password for '{name}'."
            else:
                session['name'] = name
                session['logged_in'] = True
                flash('Login successful!')
                return redirect(url_for('index'))

    return render_template('login.html', error=error)


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    try:
        is_logged_in = session['logged_in']
    except KeyError:
        return redirect(url_for('index'))
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))

