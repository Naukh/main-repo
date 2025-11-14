import sqlite3
from .config import DB_PATH, TABLE_NAME
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import random

# -------------------------------
# Database helpers
# -------------------------------

def get_conn():
    return sqlite3.connect(DB_PATH)

def ensure_db_exists():
    """Create database folder, DB file, and table if missing."""
    folder = os.path.dirname(DB_PATH)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
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
# Seed sample data
# -------------------------------

def seed_sample_data():
    """Seed database with multi-month sample entries."""
    ensure_db_exists()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear existing data
    cur.execute(f"DELETE FROM {TABLE_NAME}")
    conn.commit()

    categories = {
        "Food": ["Groceries", "Dining Out"],
        "Transport": ["Fuel", "Taxi", "Bus"],
        "Income": ["Salary", "Freelance"],
        "Entertainment": ["Movies", "Games"],
        "Utilities": ["Electricity", "Internet"],
    }

    today = date.today()

    for month_offset in range(0, 6):
        # Correctly compute the first day of each past month
        month_date = today.replace(day=1) - relativedelta(months=month_offset)
        month_str = f"{month_date.year}-{month_date.month:02d}"

        for cat, subcats in categories.items():
            for subcat in subcats:
                # Randomly decide whether to insert an entry
                if random.random() > 0.5:
                    entry_type = "income" if cat == "Income" else "budget"
                    # Random day in that month
                    entry_date = month_date.replace(day=random.randint(1, 28))
                    description = f"Sample {subcat} {'income' if entry_type=='income' else 'expense'}"
                    budgeted = round(random.uniform(50, 500), 2) if entry_type == "budget" else 0
                    actual = round(random.uniform(50, 500), 2) if entry_type == "budget" else budgeted
                    account = random.choice(["Cash", "Bank", "Card"])
                    notes = ""

                    cur.execute(
                        f"""
                        INSERT INTO {TABLE_NAME} 
                        (entry_type, date, month, category, subcategory, description, budgeted, actual, account, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (entry_type, entry_date.isoformat(), month_str, cat, subcat, description, budgeted, actual, account, notes)
                    )

    conn.commit()
    conn.close()
    print("Seeded sample data for multiple months.")
# -------------------------------
# Fetch entries
# -------------------------------

def fetch_entries(month=None, category=None, subcategory=None, entry_type=None):
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
    conn = get_conn()
    cur = conn.cursor()
    q = f"DELETE FROM {TABLE_NAME} WHERE id IN ({','.join(['?']*len(ids))})"
    cur.execute(q, ids)
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted
