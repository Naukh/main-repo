# core/db.py
import sqlite3
import os
import pandas as pd
from .config import DB_PATH, TABLE_NAME

# -------------------------------
# Database helpers
# -------------------------------

def get_conn():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def ensure_db_exists():
    """Create database folder, DB file, and table if missing."""
    folder = os.path.dirname(DB_PATH)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT,
            date TEXT,
            month TEXT,
            category TEXT,
            subcategory TEXT,
            description TEXT,
            budgeted REAL,
            actual REAL,
            account TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


# -------------------------------
# Fetch entries
# -------------------------------

def fetch_entries(month=None, category=None, subcategory=None, entry_type=None):
    """Fetch entries with optional filters."""
    conn = get_conn()
    q = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []

    if month:
        q += " AND month=?"
        params.append(month)
    if category:
        q += " AND category=?"
        params.append(category)
    if subcategory:
        q += " AND subcategory=?"
        params.append(subcategory)
    if entry_type:
        q += " AND entry_type=?"
        params.append(entry_type)

    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def fetch_distinct_categories_subcategories():
    """Return all unique categories and (category, subcategory) pairs."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT category FROM {TABLE_NAME} WHERE category IS NOT NULL")
    categories = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT DISTINCT category, subcategory FROM {TABLE_NAME} WHERE subcategory IS NOT NULL")
    cat_sub = [(c, sc) for c, sc in cur.fetchall()]
    conn.close()
    return categories, cat_sub


# -------------------------------
# Insert / update / delete
# -------------------------------

def insert_entry(entry):
    """Insert a single entry into the database."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TABLE_NAME}
        (entry_type, date, month, category, subcategory, description, budgeted, actual, account, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry["entry_type"],
        entry["date"],
        entry["month"],
        entry["category"],
        entry["subcategory"],
        entry["description"],
        entry["budgeted"],
        entry["actual"],
        entry["account"],
        entry["notes"],
    ))
    conn.commit()
    conn.close()

def bulk_update_rows(df):
    """Update multiple rows from a DataFrame."""
    conn = get_conn()
    cur = conn.cursor()
    updated = 0
    for _, r in df.iterrows():
        cur.execute(f"""
            UPDATE {TABLE_NAME}
            SET month=?, entry_type=?, date=?, category=?, subcategory=?,
                description=?, budgeted=?, actual=?, account=?, notes=?
            WHERE id=?
        """, (
            r["month"], r["entry_type"], r["date"], r["category"], r["subcategory"],
            r["description"], r["budgeted"], r["actual"], r["account"], r["notes"], r["id"]
        ))
        updated += cur.rowcount
    conn.commit()
    conn.close()
    return updated

def bulk_delete(ids):
    """Delete multiple rows by their IDs."""
    if not ids:
        return 0
    conn = get_conn()
    cur = conn.cursor()
    q = f"DELETE FROM {TABLE_NAME} WHERE id IN ({','.join(['?']*len(ids))})"
    cur.execute(q, ids)
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


# -------------------------------
# Initialize a new month
# -------------------------------
def initialize_new_month(new_month: str, carry_budget: bool = False):
    """
    Initialize a new month by copying distinct (entry_type, category, subcategory)
    from the latest existing month.

    - new_month: "YYYY-MM"
    - carry_budget: if True, copy the previous budgeted values; otherwise budgeted=0.0
    Returns (success: bool, message: str).
    """
    # basic format guard
    if not isinstance(new_month, str) or len(new_month) != 7 or new_month[4] != "-":
        return False, "new_month must be a string in YYYY-MM format."

    conn = get_conn()
    cur = conn.cursor()

    # 1) check if month already has entries
    cur.execute("SELECT COUNT(1) FROM entries WHERE month = ?", (new_month,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return False, f"Month {new_month} already exists in the database."

    # 2) find the most recent existing month in DB
    cur.execute("SELECT DISTINCT month FROM entries WHERE month IS NOT NULL ORDER BY month DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "No existing data found to copy from."

    latest_month = row[0]

    # 3) fetch distinct entry_type/category/subcategory/budgeted from the latest_month
    #    (this will include incomes such as Salary)
    cur.execute("""
        SELECT DISTINCT entry_type, category, subcategory, COALESCE(budgeted, 0.0)
        FROM entries
        WHERE month = ?
    """, (latest_month,))
    items = cur.fetchall()

    if not items:
        conn.close()
        return False, f"No entries found in latest month {latest_month} to copy."

    # 4) Insert new rows for the new month (actual=0.0). Keep entry_type the same.
    inserted = 0
    for entry_type, category, subcategory, prev_budgeted in items:
        # skip if category is None/empty
        if not category:
            continue

        budgeted_value = float(prev_budgeted) if carry_budget else 0.0

        cur.execute("""
            INSERT INTO entries
            (entry_type, date, month, category, subcategory, description, budgeted, actual, account, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_type,
            None,                 # date not set for auto-created rows
            new_month,
            category,
            subcategory,
            "Auto-created from previous month",
            budgeted_value,
            0.0,                  # actual reset
            "",
            "Initialized automatically"
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return True, f"Initialized {inserted} rows for month {new_month} (from {latest_month})."



