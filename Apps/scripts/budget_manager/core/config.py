import os

# Determine writable DB path

DB_FOLDER = "/tmp"  # cloud-writable folder
DB_FILENAME = "budget.db"
DB_PATH = os.path.join(DB_FOLDER, DB_FILENAME)

# Table name
TABLE_NAME = "entries"
