import os

# Determine writable DB path
if os.getenv("STREAMLIT_APP_TMPDIR"):
    # Streamlit Cloud environment
    DB_FOLDER = os.getenv("STREAMLIT_APP_TMPDIR")
else:
    # Local environment
    DB_FOLDER = "db"

DB_FILENAME = "budget.db"
DB_PATH = os.path.join(DB_FOLDER, DB_FILENAME)

# Table name
TABLE_NAME = "entries"
