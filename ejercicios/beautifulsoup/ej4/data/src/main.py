from bs4 import BeautifulSoup
import re
from tkinter import Tk
from tkinter import messagebox
import urllib.request
from datetime import datetime

from db import DBManager, DBAttr
from ui import WinesUI
from __ssl import init_ssl
from config import *

init_ssl()

dbm = DBManager(DB_PATH)

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
    
def parse_duration(duration):
    duration.strip()
    res = 0
    if duration[-1] == "h":
        duration.replace("h","")
        res = int(duration) * 60
    elif "h" in duration:
        duration.replace("h","")
        duration.replace("m","")
        res = int(duration[0]) + int(duration[1:]) 
    else:
        duration.replace("m","")
        res = int(duration)
    return res

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
                    movies_count = persit_recetas()
                    ui.info(f"Hay {movies_count} recetas")
            case "Recetas":
                recetas = dbm.get_all("recetas")
                ui.show_list(recetas, ["titulo", "dificultad", "comensales", "duracion", "autor", "fecha"])
            case "Receta por autor":
                def search_title(title):
                    movies = [movie for movie in dbm.get_all("recetas") if title.lower() in movie["titulo"].lower()]
                ui.show_list(recetas, ["titulo", "dificultad", "comensales", "duracion", "autor", "fecha"])
                ui.ask_text("Buscar por autor: ", search_title)
            case "Receta por fecha":
                def search_date(date):
                    d = datetime.strptime(date, "%d-%m-%Y")
                    movies = [movie for movie in dbm.get_all("movies") 
                            if d < datetime.strptime(movie["date"], "%Y-%m-%d %H:%M:%S")]
                    ui.show_list(movies, ["title", "date"])
                ui.ask_text("Buscar por fecha: ", search_date)
           
    ui.callback = handle_action
    root.mainloop()
    dbm.close()
            
if __name__ == "__main__":
    main()