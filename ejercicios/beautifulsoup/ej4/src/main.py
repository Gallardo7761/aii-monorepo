from bs4 import BeautifulSoup
import re
from tkinter import Tk
from tkinter import messagebox
import urllib.request
from datetime import datetime
import locale

from db import DBManager, DBAttr
#from ui import RecipesUI
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
    
def persist_recipes():
    f = urllib.request.urlopen(RECIPES_URL)
    bs = BeautifulSoup(f, "lxml")
    results = bs.find_all("div", attrs={"data-js-selector": "resultado"})
    for div in results:
        print(div)
        title_a = div.a
        title = title_a.string.strip()
        info_div = div.find("div", class_="info_snippet")
        difficulty = info_div.find("span").get_text(strip=True) if info_div and info_div.find("span") else None
        properties = div.find("div", class_="properties")
        duration = properties.find("span", class_=["property", "duracion"]).string.strip() if properties and properties.find("span", class_=["property", "duracion"]) else None
        units = properties.find("span", class_=["property", "unidades"]).string.strip() if properties and properties.find("span", class_=["property", "unidades"]) else None
        details_link = title_a["href"]
        f2 = urllib.request.urlopen(details_link)
        bs2 = BeautifulSoup(f2, "lxml")
        details = bs2.find("div", class_="autor").find("div", class_="nombre_autor")
        author = details.find("a").string
        date_str = details.find("span").string
        updated_at = datetime.strptime(date_str, "%d %B %Y")
        
        dbm.insert("recipes", {
            "title": title,
            "difficulty": difficulty,
            "units": units,
            "duration": duration,
            "author": author,
            "updated_at": updated_at
        })
        
        return dbm.count("recipes")
        

def main():        
    create_tables()
    recipes_count = persist_recipes()
    print(recipes_count)
    #root = Tk()
    #ui = RecipesUI(root)
    
    # def handle_action(action):
    
    #ui.callback = handle_action
    #root.mainloop()
    #dbm.close()
    
    print(dbm.get_all("recipes"))
            
if __name__ == "__main__":
    main()