import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from requests import get

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
        isbn = request.form['isbn'] or ''
        title = request.form['title'] or ''
        author = request.form['author'] or ''
        books = db.execute(
            'SELECT * FROM books WHERE UPPER(isbn) LIKE UPPER(:isbn) '
            'AND UPPER(title) LIKE UPPER(:title) '
            'AND UPPER(author) LIKE UPPER(:author)',
            {'isbn': '%'+isbn+'%', 'title': '%'+title+'%', 'author': '%'+author+'%'}
        ).fetchall()
        return render_template('index.html', books=books)
    return render_template('index.html', fresh_page=True)


def good_reads(isbn):
    payload = {'isbns': isbn, 'key': 'QZSdf0LA2UVqQ2hVodMrA'}
    res = get('https://www.goodreads.com/book/review_counts.json', params=payload)
    if res.status_code != 200:
        return None
    data = res.json()
    return data['books'][0]


@app.route("/<book_id>", methods=['GET', 'POST'])
def book_page(book_id):
    # fetch book info
    book = db.execute('SELECT * FROM books WHERE id=:book_id', {'book_id': book_id}).fetchone()
    reviews = db.execute('SELECT * FROM reviews WHERE book_id=:book_id', {'book_id': book_id}).fetchall()
    book_info = good_reads(book['isbn'])
    rating = book_info['average_rating'] if book_info else None
    number = book_info['ratings_count'] if book_info else None
    link = 'https://www.goodreads.com/book/isbn/' + book['isbn'] if book_info else None

    # i. GET request
    if request.method == 'GET':
        return render_template('book.html',
                               book=book,
                               reviews=reviews,
                               rating=rating,
                               number = number,
                               link=link)

    # ii. POST request
    # - not logged in
    error = None
    if 'name' not in session:
        error = 'You must be logged in to review book.'
        return render_template('book.html',
                               book=book,
                               reviews=reviews,
                               rating=rating,
                               number=number,
                               link=link,
                               error=error)
    # - logged in
    else:
        user_rating = request.form['rating']
        comment = request.form['comment']
        if not comment:
            error = "Comment section can't be empty."
            return render_template('book.html',
                                   book=book,
                                   reviews=reviews,
                                   rating=rating,
                                   number=number,
                                   link=link,
                                   error=error)
        # check previous review
        for review in reviews:
            if review['user_name'] == session['name']:
                error = 'You can only leave one review per a book.'
                return render_template('book.html',
                                       book=book,
                                       reviews=reviews,
                                       rating=rating,
                                       number=number,
                                       link=link,
                                       error=error)
        db.execute(
            'INSERT INTO reviews (book_id, user_name, rating, comment) VALUES'
            '(:book_id, :user_name, :rating, :comment)',
            {'book_id': book_id, 'user_name': session['name'], 'rating': user_rating, 'comment': comment}
        )
        db.commit()
        # update reviews
        reviews = db.execute('SELECT * FROM reviews WHERE book_id=:book_id', {'book_id': book_id}).fetchall()
        return render_template('book.html',
                               book=book,
                               reviews=reviews,
                               rating=rating,
                               number=number,
                               link=link)


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

