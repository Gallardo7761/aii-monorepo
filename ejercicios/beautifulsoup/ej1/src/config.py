from pathlib import Path

URL = "https://www.vinissimus.com/es/vinos/tinto/?cursor=0"
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH =  DATA_DIR / "books.csv"
DB_PATH = DATA_DIR / "books.bd"