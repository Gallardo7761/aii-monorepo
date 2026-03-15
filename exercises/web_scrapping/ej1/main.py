from bs4 import BeautifulSoup
import re
from tkinter import Tk
from tkinter import messagebox
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import sqlite3

# --- CONSTANTS ------------------------------------------
URL = "https://www.vinissimus.com/es/vinos/tinto/?cursor="
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH =  DATA_DIR / "books.csv"
DB_PATH = DATA_DIR / "books.bd"

# --- HELPER CLASSES -------------------------------------
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
        
    def get_singleton(self, singleton_table):
        try:
            cursor = self.conn.execute(f"SELECT * FROM {singleton_table}")
            return [row[0] for row in cursor.fetchall()]
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
            
    def clear(self, table_name):
        query = f"DELETE FROM {table_name};"
        
        try:
            with self.conn:
                self.conn.execute(query)
        except Exception as e:
            print("Error clearing table: ", e)

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

class WinesUI():
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
        datos_menu.add_command(label="Listar", command=lambda: self.callback("listar"))
        datos_menu.add_separator()
        datos_menu.add_command(label="Salir", command=self.root.quit)
        self.menu.add_cascade(label="Datos", menu=datos_menu)

        # Menu Buscar
        buscar_menu = tk.Menu(self.menu, tearoff=0)
        buscar_menu.add_command(label="Denominación", command=lambda: self.callback("buscar_denominacion"))
        buscar_menu.add_command(label="Precio", command=lambda: self.callback("buscar_precio"))
        buscar_menu.add_command(label="Uva", command=lambda: self.callback("buscar_uva"))
        self.menu.add_cascade(label="Buscar", menu=buscar_menu)

        # Callback externo desde el punto de entrada
        self.callback = None
        
    def show_list(self, items, fields, title="Listado"):
        mw = tk.Toplevel(self.root)
        mw.title(title)
        listbox = tk.Listbox(mw, width=80, height=20)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(mw)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        for item in items:
            row = " | ".join(str(item[field]) for field in fields)
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

def init_ssl():
    import os, ssl
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
        ssl._create_default_https_context = ssl._create_unverified_context

def create_tables():
    wines_attr = [
        DBAttr("name", "TEXT", "NOT NULL"),
        DBAttr("price", "INTEGER", "NOT NULL"),
        DBAttr("origin", "TEXT", "NOT NULL"),
        DBAttr("cellar", "TEXT", "NOT NULL"),
        DBAttr("type", "TEXT", "NOT NULL")
    ]
    
    types_attr = [
        DBAttr("type", "TEXT")
    ]
    
    dbm.create_table("wines", wines_attr)
    dbm.create_table("types", types_attr)
    
def extract_wines():
    l = []
    
    for i in range(0,3):
        f = urllib.request.urlopen(URL+str(i*36))
        doc = BeautifulSoup(f, "lxml")
        page = doc.find_all("div", class_="product-list-item")
        l.extend(page)
   
    return l

def persist_wines(wines):
    types = set()
    
    for wine in wines:
        details = wine.find("div",class_=["details"])
        name = details.a.h2.string.strip()
        price = list(wine.find("p",class_=["price"]).stripped_strings)[0]
        origin  = details.find("div",class_=["region"]).string.strip()
        cellar = details.find("div", class_=["cellar-name"]).string.strip() 
        grapes = "".join(details.find("div",class_=["tags"]).stripped_strings)
        for g in grapes.split("/"):
            types.add(g.strip())
        disc = wine.find("p",class_=["price"]).find_next_sibling("p",class_="dto")
        if disc:
            price = list(disc.stripped_strings)[0]
            
        dbm.insert("wines", {"name": name, "price": float(price.replace(',', '.')), "origin": origin, "cellar": cellar, "type": grapes})
    
    for type in types:
        dbm.insert("types", {"type": type})
        
    return dbm.count("wines"), dbm.count("types")

def main():        
    create_tables()
    root = Tk()
    ui = WinesUI(root)
    
    def handle_action(action):
        match(action):
            case "cargar":
                resp = messagebox.askyesno(title="Cargar", message="Quieres cargar todos los datos de nuevo?")
                if resp:
                    dbm.clear("wines")
                    dbm.clear("types")
                    wines = extract_wines()
                    wines_count, types_count = persist_wines(wines)
                    ui.info(f"Hay {wines_count} vinos y {types_count} uvas.")
            case "listar":
                wines = dbm.get_all("wines")
                ui.show_list(wines, ["name", "price", "origin", "cellar", "type"])
            case "buscar_denominacion":
                origins = list({wine["origin"] for wine in dbm.get_all("wines")})
                origins.sort()
                def search_origin(origin):
                    wines = [wine for wine in dbm.get_all("wines") if wine["origin"] == origin]
                    ui.show_list(wines, ["name", "price", "origin", "cellar", "type"])
                ui.ask_spinbox("Buscar por denominación: ", origins, search_origin)
            case "buscar_precio":
                def search_price(price):
                    wines = [wine for wine in dbm.get_all("wines") if float(wine["price"]) <= float(price)]
                    wines.sort(key=lambda w: float(w["price"]))
                    ui.show_list(wines, ["name", "price", "origin", "cellar", "type"])
                ui.ask_text("Selecciona precio: ", search_price)
            case "buscar_uva":
                types = [t for t in dbm.get_singleton("types")]
                types.sort()
                def search_type(type):
                    wines = [wine for wine in dbm.get_all("wines") if type in wine["type"]]
                    ui.show_list(wines, ["name", "price", "origin", "cellar", "type"])
                ui.ask_spinbox("Selecciona tip de uva: ", types, search_type)
    
    ui.callback = handle_action
    root.mainloop()
    dbm.close()
        
if __name__ == "__main__":
    main()