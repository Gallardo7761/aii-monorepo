from bs4 import BeautifulSoup
import re
import urllib.request
from datetime import datetime
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import Tk

# --- CONSTANTS ------------------------------------------
BASE_URL = "https://www.elseptimoarte.net"
ESTRENOS_URL = BASE_URL + "/estrenos/2025/"
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "movies.bd"

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
        buscar_menu.add_command(label="Título", command=lambda: self.callback("buscar_titulo"))
        buscar_menu.add_command(label="Fecha", command=lambda: self.callback("buscar_fecha"))
        buscar_menu.add_command(label="Género", command=lambda: self.callback("buscar_genero"))
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
    movies_attr = [
        DBAttr("title", "TEXT", "NOT NULL"),
        DBAttr("original_title", "TEXT", "NOT NULL"),
        DBAttr("country", "TEXT", "NOT NULL"),
        DBAttr("date", "DATE", "NOT NULL"),
        DBAttr("director", "TEXT", "NOT NULL"),
        DBAttr("genres", "TEXT", "NOT NULL")
    ]
    
    genres_attr = [
        DBAttr("genre", "TEXT")
    ]

    dbm.create_table("movies", movies_attr)
    dbm.create_table("genres", genres_attr)
    
def persist_movies():
    f = urllib.request.urlopen(ESTRENOS_URL)
    bs = BeautifulSoup(f, "lxml")
    list_items = bs.find("ul", class_="elements").find_all("li")
    for li in list_items: 
        f = urllib.request.urlopen(BASE_URL+li.a['href'])
        bs = BeautifulSoup(f, "lxml")
        data = bs.find("main", class_="informativo").find("section",class_="highlight").div.dl
        original_title = data.find("dt", string=lambda s: s and "Título original" in s).find_next_sibling("dd").get_text(strip=True)
        country = "".join(data.find("dt", string=lambda s: s and "País" in s).find_next_sibling("dd").stripped_strings)
        title = data.find("dt", string=lambda s: s and "Título" in s).find_next_sibling("dd").get_text(strip=True)
        date = datetime.strptime(data.find("dt",string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
        
        genres_director = bs.find("div",id="datos_pelicula")
        genres_str = genres_director.find("p", class_="categorias").get_text(strip=True)
        genres_list = [g.strip() for g in genres_str.split(",") if g.strip()]
        for g in genres_list:
            existing = dbm.exists("genres", "genre", g)
            if not existing:
                dbm.insert("genres", {"genre": g})
        director = "".join(genres_director.find("p",class_="director").stripped_strings)
        
        dbm.insert("movies", {
            "title": title,
            "original_title": original_title,
            "country": country,
            "date": date,
            "director": director,
            "genres": genres_str
        })
        
    return dbm.count("movies"), dbm.count("genres")

def main():        
    create_tables()
    root = Tk()
    ui = WinesUI(root)
    
    def handle_action(action):
        match(action):
            case "cargar":
                resp = messagebox.askyesno(title="Cargar", message="Quieres cargar todos los datos de nuevo?")
                if resp:
                    dbm.clear("movies")
                    dbm.clear("genres")
                    movies_count, genres_count = persist_movies()
                    ui.info(f"Hay {movies_count} películas y {genres_count} géneros")
            case "listar":
                movies = dbm.get_all("movies")
                ui.show_list(movies, ["title", "original_title", "country", "date", "director", "genres"])
            case "buscar_titulo":
                def search_title(title):
                    movies = [movie for movie in dbm.get_all("movies") if title.lower() in movie["title"].lower()]
                    ui.show_list(movies, ["title", "country", "director"])
                ui.ask_text("Buscar por titulo: ", search_title)
            case "buscar_fecha":
                def search_date(date):
                    d = datetime.strptime(date, "%d-%m-%Y")
                    movies = [movie for movie in dbm.get_all("movies") 
                            if d < datetime.strptime(movie["date"], "%Y-%m-%d %H:%M:%S")]
                    ui.show_list(movies, ["title", "date"])
                ui.ask_text("Buscar por fecha: ", search_date)
            case "buscar_genero":
                genres = [g for g in dbm.get_singleton("genres")]
                genres.sort()
                def search_genre(genre):
                    movies = [movie for movie in dbm.get_all("movies") if genre in movie["genres"]]
                    ui.show_list(movies, ["title", "date"])
                ui.ask_spinbox("Selecciona género: ", genres, search_genre)
    
    ui.callback = handle_action
    root.mainloop()
    dbm.close()
            
if __name__ == "__main__":
    main()