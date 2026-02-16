from bs4 import BeautifulSoup
import re
from tkinter import Tk
from tkinter import messagebox
import urllib.request

from db import DBManager, DBAttr
from ui import WinesUI
from __ssl import init_ssl
from config import *

init_ssl()

dbm = DBManager(DB_PATH)

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