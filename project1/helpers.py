from functools import wraps
from flask import g, request, redirect, url_for
import sqlite3
import datetime

# From https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

conn = sqlite3.connect('database.db', check_same_thread=False)  
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS reviews (review_id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR NOT NULL, ISBN VARCHAR NOT NULL, review_score TEXT NOT NULL, opinion TEXT, submission_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(username) REFERENCES users(username), FOREIGN KEY(ISBN) REFERENCES books(ISBN))")
conn.commit()
