import os
import csv

from flask import Flask
from models import *

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///temp.db'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


def main():
    db.create_all()
    f = open('books.csv')
    reader = csv.reader(f)
    next(reader, None)  # skip the header
    for isbn, title, author, pub in reader:
        if not isbn:
            continue
        book = Book(isbn=isbn, title=title, author=author, pub=pub)
        db.session.add(book)
        print("adding:", isbn)
    db.session.commit()  # extremely slow... I don't know why


if __name__ == '__main__':
    with app.app_context():
        main()
