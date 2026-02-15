from bs4 import BeautifulSoup
import re

from db import DBManager, DBAttr
from ui import WinesUI
from req import Requester
from __ssl import init_ssl
from config import *

init_ssl()

dbm = DBManager(DB_PATH)
req = Requester()

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

def main():        
    pass
        
if __name__ == "__main__":
    main()