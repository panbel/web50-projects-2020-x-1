import sqlite3
import csv


conn = sqlite3.connect('database.db', check_same_thread=False)  
db = conn.cursor()

# To create the table
db.execute("CREATE TABLE IF NOT EXISTS books (ISBN VARCHAR PRIMARY KEY, title TEXT NOT NULL, author VARCHAR NOT NULL, year VARCHAR NOT NULL)")

with open ("books.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    # print(f"csv_headings = {next(reader)}") it didnt give headings
    # print(f"first_line = {next(reader)}")
    for row in reader:
        db.execute("INSERT INTO books (ISBN, title, author, year) VALUES (?, ?, ?, ?)", (row["isbn"], row["title"], row["author"], row["year"]))
        conn.commit()

db.execute("CREATE UNIQUE INDEX idx_isbn ON books (isbn)")
db.execute("CREATE INDEX idx_title ON books (title)")
db.execute("CREATE INDEX idx_author ON books (author)")
db.execute("CREATE INDEX idx_year ON books (year)")
conn.commit()