import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "cat_operator.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

ML_ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "artifacts")
