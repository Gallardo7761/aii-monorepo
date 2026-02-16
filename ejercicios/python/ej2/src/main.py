from pathlib import Path
from tkinter import Tk

from files import FileReader
from db import DBManager, DBAttr
from ui import BooksUI

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH =  DATA_DIR / "books.csv"
DB_PATH = DATA_DIR / "books.bd"

dbm = DBManager(DB_PATH)
fr = FileReader()

def create_tables():
    book_attrs = [
        DBAttr("isbn", "INTEGER", "PRIMARY KEY"),
        DBAttr("title", "TEXT", "NOT NULL"),
        DBAttr("author", "TEXT"),
        DBAttr("year", "DATE"),
        DBAttr("publisher", "TEXT")
    ]
    
    dbm.create_table("books", book_attrs)

def main():
    create_tables()
    root = Tk()
    ui = BooksUI(root)
    
    def handle_action(action):
        match(action):
            case "cargar":
                books = fr.read(CSV_PATH)
                count = 0
                for book in books:
                    book["isbn"] = int(book["isbn"])
                    if not dbm.exists("books", "isbn", book["isbn"]):
                        dbm.insert("books", book)
                        count += 1
                ui.info(f"{count} libros almacenados.")  
            case "listar_todo":
                books = dbm.get_all("books")
                ui.show_list(books, ["isbn", "title", "author", "year"])
            case "listar_ordenado":
                def sort(attr):
                    books = dbm.get_all("books")
                    def key_fn(x):
                        v = x[attr]
                        if isinstance(v, int):
                            return v
                        elif isinstance(v, str) and v.isdigit():
                            return int(v)
                        else:
                            return float('inf')
                    books.sort(key=key_fn)
                    ui.show_list(books, ["isbn", "title", "author", "year"])
                ui.ask_radiobutton("Ordenar por: ", ["isbn", "year"], sort)
            case "buscar_titulo":
                def search_title(title):
                    books = [book for book in dbm.get_all("books") if title.lower() in book["title"].lower()]
                    ui.show_list(books, ["isbn", "title", "author", "year"])
                ui.ask_text("Buscar por título: ", search_title)
            case "buscar_editorial":
                publishers = list({book["publisher"] for book in dbm.get_all("books")})
                publishers.sort()
                def search_publisher(publisher):
                    books = [book for book in dbm.get_all("books") if book["publisher"] == publisher]
                    ui.show_list(books, ["title", "author", "publisher"])
                ui.ask_spinbox("Selecciona editorial: ", publishers, search_publisher)
    
    ui.callback = handle_action
    root.mainloop()
    dbm.close()
    
if __name__ == "__main__":
    main()