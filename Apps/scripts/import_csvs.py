import os
import sqlite3
import pandas as pd
from glob import glob

# Paths
BASE_DIR = os.path.dirname(__file__)
CSV_DIR = os.path.join(BASE_DIR, "..", "data", "Monthly_budget_file")  # adjust if needed
DB_PATH = os.path.join(BASE_DIR, "..", "data", "budget.db")

def get_month_from_filename(fname):
    """Extract YYYY-MM from a filename like '2023-02.csv'"""
    base = os.path.splitext(os.path.basename(fname))[0]  # remove .csv
    if len(base) == 7 and base[:4].isdigit() and base[4] == "-" and base[5:].isdigit():
        return base
    return None

def import_csv_to_db(csv_path, conn, allow_update=False):
    month = get_month_from_filename(csv_path)
    if not month:
        print(f"Skipping {csv_path}: could not infer month")
        return

    df = read_csv_safely(csv_path)
    df = df.where(pd.notnull(df), None)
    expected_cols = ["EntryType","Date","Category","Subcategory","Description",
                     "Budgeted","Actual","Account","Notes"]
    if not all(c in df.columns for c in expected_cols):
        print(f"Skipping {csv_path}: invalid format")
        return

    # --- Smart update if month already exists ---
    cur = conn.cursor()
    cur.execute("SELECT * FROM entries WHERE month = ?", (month,))
    existing = cur.fetchall()

    if existing and not allow_update:
        print(f"Month {month} already imported, skipping.")
        return

    if allow_update:
        print(f"Updating month {month} ...")
        existing_df = pd.read_sql_query(
            "SELECT entry_type, category, subcategory, description, budgeted, actual FROM entries WHERE month = ?",
            conn, params=(month,)
        )

        # Detect changed or new rows
        merged = df.merge(
            existing_df,
            how="outer",
            left_on=["EntryType","Category","Subcategory","Description"],
            right_on=["entry_type","category","subcategory","description"],
            indicator=True,
            suffixes=("_new", "_db")
        )

        changed = merged[
            (merged["_merge"] == "left_only") |
            ((merged["Budgeted"] != merged["budgeted"]) |
             (merged["Actual"] != merged["actual"]))
        ]

        if not changed.empty:
            print(f"Found {len(changed)} changed/new rows for {month}")
            # Delete existing rows for these keys, then reinsert
            for _, r in changed.iterrows():
                conn.execute("""
                    DELETE FROM entries
                    WHERE month = ? AND category = ? AND subcategory = ? AND description = ?
                """, (month, r["Category"], r["Subcategory"], r["Description"]))
            conn.commit()

            # Reinsert updated rows
            import_csv_to_db(csv_path, conn, allow_update=False)
            print(f"Updated {month} successfully.")
        else:
            print(f"No changes detected for {month}.")
        return

    # --- Normal insert ---
    records = [
        (
            (r["EntryType"].lower() if r["EntryType"] else None),
            r["Date"], month,
            r["Category"], r["Subcategory"], r["Description"],
            r["Budgeted"], r["Actual"], r["Account"], r["Notes"]
        )
        for _, r in df.iterrows()
    ]
    conn.executemany("""
        INSERT INTO entries (
            entry_type, date, month, category, subcategory,
            description, budgeted, actual, account, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()
    print(f"Imported {len(records)} rows from {os.path.basename(csv_path)}")


def read_csv_safely(path):
    """Read a CSV using utf-8-sig, fallback to cp1252 if needed."""
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp1252")
    
def get_existing_months(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM entries WHERE month IS NOT NULL")
    rows = cur.fetchall()
    return {r[0] for r in rows if r[0]}



def main():
    if not os.path.exists(DB_PATH):
        print("Database not found. Run create_db.py first.")
        return

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)

    # Collect all CSV files
    csv_files = glob(os.path.join(CSV_DIR, "*.csv"))
    if not csv_files:
        print("No CSV files found in:", CSV_DIR)
        return

    # Get already imported months from DB
    existing_months = get_existing_months(conn)

    # Sort CSV files chronologically
    csv_files = sorted(csv_files)
    latest_csv = csv_files[-1]
    latest_month = get_month_from_filename(latest_csv)

    print(f"Existing months in DB: {sorted(existing_months)}")
    print(f"Latest CSV: {os.path.basename(latest_csv)} → {latest_month}")

    # Import logic
    for csv_path in csv_files:
        month = get_month_from_filename(csv_path)
        if not month:
            continue

        # Skip months already in DB (except the latest month)
        if month in existing_months and month != latest_month:
            print(f"Skipping {month}: already imported and locked.")
            continue

        # Allow update only for latest month
        allow_update = (month == latest_month)
        import_csv_to_db(csv_path, conn, allow_update=allow_update)

    conn.close()
    print("Import process completed.")

if __name__ == "__main__":
    main()
