import os
import requests
import json

from flask import Flask, session, render_template, redirect, request, url_for, g, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import pbkdf2_sha256
import sqlite3
from helpers import login_required
from flask_login import current_user


app = Flask(__name__)
app.secret_key = "8635c8244367b3954287e06f" #Needed it for sessions for some reason
# goodreads key: KwgdSXYK4WTAoN3ZnJElpA

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

# Set up database
#engine = create_engine(os.getenv("DATABASE_URL"))
#db = scoped_session(sessionmaker(bind=engine))
conn = sqlite3.connect('database.db', check_same_thread=False)  
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS users (username VARCHAR PRIMARY KEY, email VARCHAR NOT NULL, password VARCHAR NOT NULL)")
             #AUTOINCREMENT is to prevent the reuse of ROWIDs from previously deleted rows.


@app.before_request  # From: https://www.youtube.com/watch?v=2Zz97NVbH0U&t=492s 
def before_request():  # Had to import g from flask. It creates a global variable so I can then reference a users info in other routes
    g.user = None

    if 'user_id' in session:
        user = db.execute("SELECT * FROM users WHERE user_id=:input", {"input": session['user_id']}).fetchone()  #returns a tuple
        # print(f"user:{user}")
        #fetchall returns a list of tuples
        g.user = user

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=("POST", "GET"))
def register():
    if request.method == "POST":
        session.pop('user_id', None)  #pros do that..

        input_username = request.form.get('username')
        input_email = request.form.get('email')
        input_password_safe = pbkdf2_sha256.hash(request.form.get('password'))
        input_confirm_password_safe = pbkdf2_sha256.hash(request.form.get('confirm_password'))
        if not input_username:
                error = 'Please enter an username!'
        elif not input_email:
                error = 'Please enter an email address!' 
        elif not input_password_safe:
            error = 'Please enter a password!'
        elif not input_confirm_password_safe:
            error = 'Please enter a confirmation password!'
        else:  # If there are no empty fields
            #db.execute("SELECT username FROM users WHERE username=:input", {"input": input_username}) #RETURNS:<sqlite3.Cursor object at 0x040EFEE0>
            username_check = db.execute("SELECT username FROM users WHERE username=:input", {"input": input_username}).fetchall()
            email_check = db.execute("SELECT email FROM users WHERE email=:input", {"input": input_email}).fetchall() #returns empty list
            if len(username_check) != 0:
                error = 'This username has already been taken. Please enter a different username.'
            elif len(email_check) != 0:  #email already exists
                error = 'This email address has already been taken. Please enter a different email address.'
            elif pbkdf2_sha256.verify(request.form.get('confirm_password'), input_password_safe) == False:  # If the passwords dont match
                error = "The confirmation password does not match the password you inserted!"
            else:  # If everything is good!
                error = "You were succesfully registered!"
                db.execute('''INSERT INTO users (
                            username, email, password) VALUES (?, ?, ?)''', (input_username,input_email, input_password_safe)).fetchone()
                conn.commit()  #not db.commit!!
                error = "Registration complete! You may now login."
                return redirect(url_for('login', error=error))
                # render_template("login.html", error= error)
        return render_template('register.html', error=error)
    
    else:  # If method == GET
        return render_template("register.html")
    
        
@app.route("/login", methods=("POST", "GET"))
def login():
    if request.method == "POST":
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        session.pop('username', None)  #pros do that..
        if not input_username:
            error = 'Please enter a username!'
        elif not input_password:
            error = 'Please enter a password!'
        else:  # If both were given
            input_check = db.execute("SELECT * FROM users WHERE username=:input", {"input": input_username}).fetchone()  # Tuple
            #print(input_check)
            if input_check is None:  # if no username matched from the database
                error = "Incorrect username"
            elif pbkdf2_sha256.verify(input_password, input_check[2]) == False:  # If the passwords dont match
                error = "Wrong password"
            else:
                error = "You were sucesfully logged in!"
                print(input_check)
                user_id = input_check[3]
                session["user_id"] = user_id # Not sure if I need this here
                print(session["user_id"])
                # session['username'] = input_username
                return render_template('search.html', error=error)
                # return redirect(url_for('search', error=error))
        return render_template('login.html', error=error)
    
    else:  # If method == "GET"
        return render_template("login.html")


@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/search", methods=("POST", "GET"))
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        choice = request.form.get("choice")
        search_input = request.form.get("search_input")
        query = db.execute(f'SELECT * FROM books WHERE {choice} LIKE ?', ("%"+search_input+"%",)).fetchall()  # partial search!
        #FROM: https://stackoverflow.com/questions/41780944/using-variable-combining-like-and-s-in-sqlite-and-python/41781170#41781170
        #print(query)

        # If I got no matches 
        if len(query) == 0:  
            error = "No book matches your search criteria. Try again."
            return render_template("search.html", error = error)
        return render_template("book_query.html", query = query)  #redirect(url_for("book_query", query = query)) WORKED!

@app.route("/book_query")
@login_required
def book_query(query):
    # Return a list of titles where the search results match
    #query = request.args['query']  # counterpart for url_for()
    return render_template("book_query.html", query = query)


@app.route("/book_details/<book_title>", methods=("POST", "GET"))
# Returns details about a single book
@login_required
#does not need to require login
def book_details(book_title):
    basic_book_details = db.execute("SELECT * FROM books WHERE title=?", (book_title,)).fetchone()
    isbn = basic_book_details[0]
    #print(book_title)
    #print(isbn)
    if request.method == "GET":
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "KwgdSXYK4WTAoN3ZnJElpA", "isbns": isbn}).json()
        reviews = db.execute("SELECT username, review_score, opinion, submission_time FROM reviews WHERE ISBN=?", (isbn,)).fetchall()
        # Give all the details about a specific book title that was selected
        #print(res["books"][0]["average_rating"])  # Had to look at the json output to see how to index
        #print(f"Get reviews {reviews}")
        #print(f"GET basic book details(isbn) {basic_book_details[0]}")
        return render_template("book_details.html", basic_book_details = basic_book_details, advanced_details = res, reviews = reviews)

    else:  # POST:If the person submitted a review

        # First need to check if a review had already been submitted by this user for this book
        check = db.execute("SELECT * FROM reviews WHERE ISBN=? AND username=? ",(isbn, g.user[0],)).fetchall()
        #print(f"Post check {check}")
        if len(check) == 0:
            #print(request.form.get('rating'))
            #print(request.form.get("opinion"))
            db.execute("INSERT INTO reviews (username, ISBN, review_score, opinion) VALUES (?,?,?,?)", (g.user[0], isbn, request.form.get('rating'), request.form.get("opinion")))
            conn.commit()
            error = "Your review was submitted succesfully!"
            return render_template("search.html", error = error)
        else:
            error = "You have already submitted a review for this book. Only one is allowed."
            return render_template("search.html", error = error)


@app.route("/api/<isbn>")
def book_details_api(isbn):
    # Returns details about a single book in json format

    # Make sure book exists. Otherwise return 404 error
    book = db.execute("SELECT * FROM books WHERE ISBN=?", (isbn,))
    row_returned = book.fetchone()
    # # print(type(row))
    # row = book.fetchone()
    if row_returned == None:
        return jsonify({"error": "Invalid isbn"}), 404
        # Get all the relevant book details and return a json object
    else:     
        advanced_details = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "KwgdSXYK4WTAoN3ZnJElpA", "isbns": isbn}).json()
        return jsonify({
            "title": row_returned[1],
            "author": row_returned[2],
            "year": row_returned[3],
            "isbn": row_returned[0],
            "review_count": advanced_details["books"][0]["work_ratings_count"],
            "average_score": advanced_details["books"][0]["average_rating"]
        })


@app.route("/logout")
@login_required
def logout():
    [session.pop(key) for key in list(session.keys())]
    session.clear()  # So that if i logout I need to put my password in to login again! Otherwise I could access anything (/search etc.)
    error = "You were succesfully logged out!"
    return render_template('index.html', error=error)
    # return redirect(url_for('index', error=error))


@app.route('/account')
@login_required
def account():
    if not g.user:  # If the user is not in session, he needs to login (g.user was the global variable)
        return redirect(url_for('login'))

    return render_template('account.html')  # To do: check if i need the above 2 lines. Add an account tab

# $env:FLASK_APP= "application.py"
# $env:DATABASE_URL= "postgres://bjjphsnuxjabfm:0802b24ffd3e4d7a240cb35089d4969cd9b5e54cdfb8c6f45848fd18523764a3@ec2-54-247-94-127.eu-west-1.compute.amazonaws.com:5432/d74hfp6ao6b1hb"
if __name__=='__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    #app.run(debug=True)
    app.run(debug=True)
    # use_reloader=False,