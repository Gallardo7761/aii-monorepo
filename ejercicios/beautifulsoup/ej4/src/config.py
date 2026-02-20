from pathlib import Path

BASE_URL = "https://recetas.elperiodico.com"
RECIPES_URL = BASE_URL + "/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "recipes.bd"