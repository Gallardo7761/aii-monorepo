from bs4 import BeautifulSoup
import re
from tkinter import Tk
from tkinter import messagebox
import urllib.request
from datetime import datetime
import locale

from db import DBManager, DBAttr
from ui import RecipesUI
from __ssl import init_ssl
from config import *

init_ssl()
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

dbm = DBManager(DB_PATH)

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