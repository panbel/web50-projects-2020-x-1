# web50-projects-2020-x-1
Project 1 for CS50 Web - Book Review Site

application.py has the main code for the flask app.
database.db has 3 tables: 1 for users (with hashed passwords), 1 with all the books, and 1 with all the review information.
helpers.py and import.py have some additional commands and functions that are used in the main application.py program.
The "static" folder contains a scss which is automatically converted to css to make the website prettier.
The "templates" folder contains all the html templates.

I used sqlite instead of SQLALCHEMY because I couldn't get it to work in my laptop. I also didn't use Heroku and instead downloaded and used "DB Browser (SQLite)" to my laptop.
