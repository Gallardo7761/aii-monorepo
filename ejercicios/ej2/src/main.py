from files import read_file
from db import DBManager
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"

def main():
    dbm = DBManager(DATA / "books.bd")
    dbm.init()
    
    file_path =  DATA / "books.csv"
    for book in read_file(file_path):
        dbm.insert(book)
    
if __name__ == "__main__":
    main()