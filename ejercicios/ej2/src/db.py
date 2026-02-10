import sqlite3
from pathlib import Path

class DBManager:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        
    def init(self):
        try:
            with self.conn:
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS books (
                        isbn INTEGER PRIMARY KEY,
                        title TEXT,
                        author TEXT,
                        year DATE,
                        publisher TEXT
                    );
                    """
                )
        except Exception as e:
            print("Error creating table:", e)
        
    def insert(self, item):
        try:
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO books (isbn, title, author, year, publisher)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (item.isbn, item.title, item.author, item.year, item.publisher)
                )
        except Exception as e:
            print("Error inserting book:", e)
            
    def close(self):
        self.conn.close()