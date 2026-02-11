from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import re

URL = "https://www.vinissimus.com/es/vinos/tinto/?cursor=0"

def main():        
    req = Request(
        URL, 
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; Konqueror/3.5.8; Linux)"
        }
    )

    doc = BeautifulSoup(
        urlopen(req), 
        "lxml"
    )
    
    for child in doc.find_all("div", class_="list large"):
        name = child.find("h2", class_=["title"])
        print(name)
        
if __name__ == "__main__":
    main()