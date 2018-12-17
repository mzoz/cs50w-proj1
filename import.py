import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open('books.csv')
    reader = csv.reader(f)
    next(reader, None)  # skip the header
    for isbn, title, author, pub in reader:
        if not isbn:
            continue
        db.execute('INSERT INTO books (isbn, title, author, pub) '
                   'VALUES (:isbn, :title, :author, :pub)'
                   , {'isbn': isbn, 'title': title, 'author': author, 'pub': pub})
        print('adding:', isbn, author)
    db.commit()


if __name__ == '__main__':
    main()
