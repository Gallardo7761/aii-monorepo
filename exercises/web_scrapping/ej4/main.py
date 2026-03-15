from bs4 import BeautifulSoup
import re
import urllib.request
from datetime import datetime
import locale
from pathlib import Path
from tkinter import Tk
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import sqlite3

# --- CONSTANTS ------------------------------------------
BASE_URL = "https://recetas.elperiodico.com"
RECIPES_URL = BASE_URL + "/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "recipes.bd"

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
        
class RecipesUI():
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
        listar_menu.add_command(label= "Recetas", command = lambda:  self.callback("listar_recetas"))
        self.menu.add_cascade(label="Listar", menu=listar_menu)

        # Menu Buscar
        buscar_menu = tk.Menu(self.menu, tearoff=0)
        buscar_menu.add_command(label="Receta por autor", command=lambda: self.callback("buscar_autor"))
        buscar_menu.add_command(label="Receta por fecha", command=lambda: self.callback("buscar_fecha"))
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
    recipes_attr = [
        DBAttr("title", "TEXT", "NOT NULL"),
        DBAttr("difficulty", "TEXT", "DEFAULT NULL"),
        DBAttr("units", "INTEGER", "DEFAULT NULL"),
        DBAttr("duration", "INTEGER", "DEFAULT NULL"),
        DBAttr("author", "TEXT", "NOT NULL"),
        DBAttr("updated_at", "DATE", "NOT NULL")
    ]

    dbm.create_table("recipes", recipes_attr)
    
def parse_duration(duration):
    if not duration:
        return None

    duration = duration.strip().lower()

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)h", duration)
    m_match = re.search(r"(\d+)m", duration)

    if h_match:
        hours = int(h_match.group(1))

    if m_match:
        minutes = int(m_match.group(1))

    return hours * 60 + minutes

def parse_duration_inverse(minutes):
    if minutes is None:
        return None
    m = minutes % 60
    h = (minutes - m) // 60
    return f"{h}h {m}m" if h != 0 else f"{m}m"

def persist_recipes():
    f = urllib.request.urlopen(RECIPES_URL)
    bs = BeautifulSoup(f, "lxml")
    results = bs.find_all("div", attrs={"data-js-selector": "resultado"})
    for div in results:
        title_a = div.a
        title = title_a.string.strip()
        info_div = div.find("div", class_="info_snippet")
        difficulty = info_div.find("span").get_text(strip=True) if info_div and info_div.find("span") else None
        properties = div.find("div", class_="properties")
        duration = properties.find("span", class_="duracion").string.strip() if properties and properties.find("span", class_="duracion") else None
        units = properties.find("span", class_="unidades").string.strip() if properties and properties.find("span", class_="unidades") else None
        details_link = title_a["href"]
        f2 = urllib.request.urlopen(details_link)
        bs2 = BeautifulSoup(f2, "lxml")
        details = bs2.find("div", class_="autor").find("div", class_="nombre_autor")
        author = details.find("a").string
        date_str = details.find("span").string.replace("Actualizado: ", "")
        updated_at = datetime.strptime(date_str, "%d %B %Y")
                
        dbm.insert("recipes", {
            "title": title,
            "difficulty": difficulty,
            "units": units,
            "duration": parse_duration(duration),
            "author": author,
            "updated_at": updated_at
        })
        
    return dbm.count("recipes")
        
def main():
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")        
    create_tables()
    root = Tk()
    ui = RecipesUI(root)

    def handle_action(action):
        match(action):
            case "cargar":
                resp = messagebox.askyesno(title="Cargar", message="Quieres cargar todos los datos de nuevo?")
                if resp:
                    dbm.clear("recipes")
                    recipes_count = persist_recipes()
                    ui.info(f"Hay {recipes_count} recetas")
            case "listar_recetas":
                recipes = dbm.get_all("recipes")
                for r in recipes:
                    r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
                    r["duration"] = parse_duration_inverse(r["duration"])
                ui.show_list(recipes, ["title", "difficulty", "units", "duration"])
            case "buscar_autor":
                def search_author(author):
                    recipes = [recipe for recipe in dbm.get_all("recipes") if author.lower() in recipe["author"].lower()]
                    for r in recipes:
                        r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
                        r["duration"] = parse_duration_inverse(r["duration"])
                    ui.show_list(recipes, ["title", "difficulty", "units", "duration", "author"])
                ui.ask_text("Buscar por autor: ", search_author)
            case "buscar_fecha":
                def search_date(date):
                    d = datetime.strptime(date, "%d/%m/%Y")
                    recipes = [recipe for recipe in dbm.get_all("recipes") 
                            if d > datetime.strptime(recipe["updated_at"], "%Y-%m-%d %H:%M:%S")]
                    for r in recipes:
                        r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
                        r["duration"] = parse_duration_inverse(r["duration"])
                    ui.show_list(recipes, ["title", "difficulty", "units", "duration", "updated_at"])
                ui.ask_text("Buscar por fecha: ", search_date)
           
    ui.callback = handle_action
    root.mainloop()
    dbm.close()
            
if __name__ == "__main__":
    main()