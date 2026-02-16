from pathlib import Path

BASE_URL = "https://www.elseptimoarte.net"
ESTRENOS_URL = BASE_URL + "/estrenos/2025/"
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "movies.bd"