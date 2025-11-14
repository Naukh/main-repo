import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # core/
DB_FOLDER = os.path.join(BASE_DIR, "..", "data")
DB_FILENAME = "budget.db"
DB_PATH = os.path.join(DB_FOLDER, DB_FILENAME)

TABLE_NAME = "entries"
