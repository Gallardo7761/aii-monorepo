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