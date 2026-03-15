from pathlib import Path
from tkinter import Tk
import sqlite3
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# --- CONSTANTS ------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH =  DATA_DIR / "books.csv"
DB_PATH = DATA_DIR / "books.bd"

# --- HELPER CLASSES -------------------------------------
class FileReader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, delimiter=";"):
        self.delimiter = delimiter

    def read(self, file):
        results = []
        try:
            with open(file, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                for row in reader:
                    results.append(dict(row))
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
        return results

class DBAttr:
    def __init__(self, name, type_, modifier=""):
        self.name = name
        self.type_ = type_
        self.modifier = modifier

    def sql(self):
        parts = [self.name, self.type_]
        if self.modifier:
            parts.append(self.modifier)
        return " ".join(parts)

class DBManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, path):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def create_table(self, table_name, attributes: list[DBAttr]):
        columns_sql = ",\n    ".join(attr.sql() for attr in attributes)

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        );
        """

        try:
            with self.conn:
                self.conn.execute(query)
        except Exception as e:
            print("Error creating table:", e)

    def get_all(self, table_name):
        try:
            cursor = self.conn.execute(f"SELECT * FROM {table_name};")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print("Error selecting:", e)
            return []

    def get_by(self, table_name, column, value):
        try:
            query = f"SELECT * FROM {table_name} WHERE {column} = ?;"
            cursor = self.conn.execute(query, (value,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print("Error selecting:", e)
            return []

    def insert(self, table_name, data: dict):
        keys = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        query = f"""
        INSERT INTO {table_name} ({keys})
        VALUES ({placeholders});
        """

        try:
            with self.conn:
                self.conn.execute(query, values)
        except Exception as e:
            print("Error inserting:", e)

    def update(self, table_name, data: dict, where_column, where_value):
        set_clause = ", ".join(f"{key} = ?" for key in data.keys())
        values = list(data.values())
        values.append(where_value)

        query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {where_column} = ?;
        """

        try:
            with self.conn:
                self.conn.execute(query, tuple(values))
        except Exception as e:
            print("Error updating:", e)

    def delete(self, table_name, where_column, where_value):
        query = f"DELETE FROM {table_name} WHERE {where_column} = ?;"

        try:
            with self.conn:
                self.conn.execute(query, (where_value,))
        except Exception as e:
            print("Error deleting:", e)

    def exists(self, table_name, where_column, where_value):
        query = f"SELECT 1 FROM {table_name} WHERE {where_column} = ? LIMIT 1;"

        try:
            cursor = self.conn.execute(query, (where_value,))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error checking existence:", e)
            return False

    def count(self, table_name):
        try:
            cursor = self.conn.execute(f"SELECT COUNT(*) as total FROM {table_name};")
            return cursor.fetchone()["total"]
        except Exception as e:
            print("Error counting:", e)
            return 0

    def close(self):
        self.conn.close()

class BooksUI():
    def __init__(self, root, title = "AII"):
        self.root = root
        self.root.title(title)
        self.root.geometry("900x600")
                
        # Menu Principal
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # Menu Datos
        datos_menu = tk.Menu(self.menu, tearoff=0)
        datos_menu.add_command(label="Cargar", command=lambda: self.callback("cargar"))
        datos_menu.add_separator()
        datos_menu.add_command(label="Salir", command=self.root.quit)
        self.menu.add_cascade(label="Datos", menu=datos_menu)

        # Menu Listar
        listar_menu = tk.Menu(self.menu, tearoff=0)
        listar_menu.add_command(label="Completo", command=lambda: self.callback("listar_completo"))
        listar_menu.add_command(label="Ordenado", command=lambda: self.callback("listar_ordenado"))
        self.menu.add_cascade(label="Listar", menu=listar_menu)

        # Menu Buscar
        buscar_menu = tk.Menu(self.menu, tearoff=0)
        buscar_menu.add_command(label="Título", command=lambda: self.callback("buscar_titulo"))
        buscar_menu.add_command(label="Editorial", command=lambda: self.callback("buscar_editorial"))
        self.menu.add_cascade(label="Buscar", menu=buscar_menu)

        # Callback externo desde el punto de entrada
        self.callback = None
        
    def show_list(self, books, fields, title="Listado"):
        mw = tk.Toplevel(self.root)
        mw.title(title)
        listbox = tk.Listbox(mw, width=80, height=20)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(mw)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        for book in books:
            row = " | ".join(str(book[field]) for field in fields)
            listbox.insert("end", row)
            
    def ask_text(self, label, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        entry = ttk.Entry(mw)
        entry.pack(pady=5)
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(entry.get()), mw.destroy()]).pack(pady=10)   
    
    def ask_spinbox(self, label, options, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        spinbox = ttk.Spinbox(mw, values=options, state="readonly", width=40)
        spinbox.pack(pady=5)
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(spinbox.get()), mw.destroy()]).pack(pady=10)
        
    def ask_radiobutton(self, label, options, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        sv = tk.StringVar(value=options[0])
        for option in options:
            tk.Radiobutton(mw, text=option, variable=sv, value=option).pack(anchor="w")
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(sv.get()), mw.destroy()]).pack(pady=10)
        
    def info(slef, message):
        messagebox.showinfo("Información", message) 

# --- MAIN PROGRAM FUNCTIONS -----------------------------
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