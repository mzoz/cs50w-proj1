# Project 1

## Database

- `export DATABASE_URL=your_db_url` to set env variable
- `models.py` has three tables 'books', 'reviews' and 'users'
- `python3 create.py` to create these tables
- `python3 import.py` to copy books info from .csv file to remote database 
- `import_orm.py` implements db orm but is too slow so only present as reference

## App

- `application.py` contains all the code for routing and api requests

## Templates

- page contents are modularized with separate html files for convenience