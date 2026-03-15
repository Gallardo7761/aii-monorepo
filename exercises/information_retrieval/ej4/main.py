import locale
import re
import urllib.request
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import Tk
from tkinter.scrolledtext import ScrolledText
import shutil, re, os

from bs4 import BeautifulSoup
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, ID, NUMERIC
from whoosh.qparser import QueryParser
from whoosh import index, qparser, query

BASE_URL = "https://recetas.elperiodico.com"
RECIPES_URL = BASE_URL + "/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
DATA_DIR = Path(__file__).parent.parent / "index"

def init_ssl():
    import os, ssl
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
        ssl._create_default_https_context = ssl._create_unverified_context

def create_index():
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    
    if not index.exists_in(DATA_DIR, indexname="RecipesIndex"):
        schema = Schema(
            title=TEXT(stored=True),
            difficulty=TEXT(stored=True),
            duration=TEXT(stored=True),
            units=NUMERIC(stored=True, numtype=int),
            author=ID(stored=True),
            updated_at=DATETIME(stored=True),
            features=KEYWORD(stored=True, commas=True), 
            intro=TEXT(stored=True) 
        )
        idx = create_in(DATA_DIR, schema=schema, indexname="RecipesIndex")
        print(f"Created index: {idx.indexname}")
    else:
        print(f"An index already exists")
    
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
    idx = index.open_dir(DATA_DIR, "RecipesIndex")
    writer = idx.writer()
    count = 0
    f = urllib.request.urlopen(RECIPES_URL)
    bs = BeautifulSoup(f, "lxml")
    results = bs.find_all("div", attrs={"data-js-selector": "resultado"})
    for div in results:
        title_a = div.a
        title = div.a.string.strip()
        info_div = div.find("div", class_="info_snippet")
        difficulty = info_div.find("span").get_text(strip=True) if info_div and info_div.find("span") else "Unknown"
        intro = div.find("div", class_="intro").get_text()
        properties = div.find("div", class_="properties")
        duration = properties.find("span", class_="duracion").string.strip() if properties and properties.find("span", class_="duracion") else "Unknown"
        units = int(properties.find("span", class_="unidades").string.strip()) if properties and properties.find("span", class_="unidades") else -1
        details_link = title_a["href"]
        f2 = urllib.request.urlopen(details_link)
        bs2 = BeautifulSoup(f2, "lxml")
        details = bs2.find("div", class_="autor").find("div", class_="nombre_autor")
        author = details.find("a").string
        date_str = details.find("span").string.replace("Actualizado: ", "")
        updated_at = datetime.strptime(date_str, "%d %B %Y")  
        features = bs2.find("div", class_=["properties", "inline"]).get_text(strip=True).replace("Características adicionales:", "") if bs2.find("div", class_=["properties", "inline"]) else "Unknown"   
       
        writer.add_document(
            title=title,
            difficulty=difficulty,
            duration=duration,
            units=units,
            author=author,
            updated_at=updated_at,
            features=features,
            intro=intro
        )
        
        count += 1
        
    writer.commit()
        
    return count

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
        datos_menu.add_command(label="Cargar", command=lambda: self.callback("load"))
        datos_menu.add_command(label="Listar", command=lambda: self.callback("list_recipes"))
        datos_menu.add_separator()
        datos_menu.add_command(label="Salir", command=self.root.quit)
        self.menu.add_cascade(label="Datos", menu=datos_menu)

        # Menu Buscar
        buscar_menu = tk.Menu(self.menu, tearoff=0)
        buscar_menu.add_command(label="Título o Introducción", command=lambda: self.callback("search_title_or_intro"))
        buscar_menu.add_command(label="Fecha", command=lambda: self.callback("search_updated_at"))
        buscar_menu.add_command(label="Características y Título", command=lambda: self.callback("search_features_and_title"))
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
            row = " | ".join(str(item.get(field, "Unknown")) for field in fields)
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

def main():
    init_ssl()
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    
    create_index()
    root = Tk()
    ui = RecipesUI(root)

    def handle_action(action):
        match(action):
            case "load":
                resp = messagebox.askyesno(title="Cargar", message="Quieres cargar todos los datos de nuevo?")
                if resp:
                    recipes_count = persist_recipes()
                    ui.info(f"Se han indexado {recipes_count} recetas")
            case "list_recipes":
                ix = open_dir(DATA_DIR, "RecipesIndex")
                with ix.searcher() as searcher:
                    recipes = searcher.search(query.Every(), limit=None)
                    clear = []
                    for r in recipes:
                        d = dict(r)
                        clear.append(d)
                    print(clear)
                    ui.show_list(clear, ["title", "difficulty", "units", "duration"])
            # case "search_title_or_intro":
            #     def search_author(author):
            #         recipes = [recipe for recipe in dbm.get_all("recipes") if author.lower() in recipe["author"].lower()]
            #         for r in recipes:
            #             r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
            #             r["duration"] = parse_duration_inverse(r["duration"])
            #         ui.show_list(recipes, ["title", "difficulty", "units", "duration", "author"])
            #     ui.ask_text("Buscar por autor: ", search_author)
            # case "search_updated_at":
            #     def search_date(date):
            #         d = datetime.strptime(date, "%d/%m/%Y")
            #         recipes = [recipe for recipe in dbm.get_all("recipes") 
            #                 if d > datetime.strptime(recipe["updated_at"], "%Y-%m-%d %H:%M:%S")]
            #         for r in recipes:
            #             r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
            #             r["duration"] = parse_duration_inverse(r["duration"])
            #         ui.show_list(recipes, ["title", "difficulty", "units", "duration", "updated_at"])
            #     ui.ask_text("Buscar por fecha: ", search_date)
            # case "search_features_and_title":
            #     def search_author(author):
            #         recipes = [recipe for recipe in dbm.get_all("recipes") if author.lower() in recipe["author"].lower()]
            #         for r in recipes:
            #             r["units"] = str(r["units"]) + " personas" if r["units"] is not None else "Unknown personas"
            #             r["duration"] = parse_duration_inverse(r["duration"])
            #         ui.show_list(recipes, ["title", "difficulty", "units", "duration", "author"])
            #     ui.ask_text("Buscar por autor: ", search_author)
           
    ui.callback = handle_action
    root.mainloop()
    
if __name__ == "__main__":
    main()
    