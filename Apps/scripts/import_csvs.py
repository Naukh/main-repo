import os
import sqlite3
import pandas as pd
from glob import glob
import hashlib
import argparse

# Paths
BASE_DIR = os.path.dirname(__file__)
CSV_DIR = os.path.join(BASE_DIR, "..", "data", "Monthly_budget_file")
DB_PATH = os.path.join(BASE_DIR, "..", "data", "budget.db")

def get_month_from_filename(fname):
    """Extract YYYY-MM from a filename like '2023-02.csv'"""
    base = os.path.splitext(os.path.basename(fname))[0]
    if len(base) == 7 and base[:4].isdigit() and base[4] == "-" and base[5:].isdigit():
        return base
    return None

def get_latest_month(conn):
    """Get the latest month from the DB entries table"""
    cur = conn.cursor()
    cur.execute("SELECT month FROM entries ORDER BY month DESC LIMIT 1")
    row = cur.fetchone()
    return row[0] if row else None

def read_csv_safely(path):
    """Read a CSV using utf-8-sig, fallback to cp1252 if needed."""
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp1252")

def get_existing_months(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM entries WHERE month IS NOT NULL")
    return {r[0] for r in cur.fetchall() if r[0]}

def row_checksum(row):
    """Generate a checksum string for a row"""
    r = row.to_dict()  # convert Series → dict
    key = f"{r.get('EntryType','')}_{r.get('Category','')}_{r.get('Subcategory','')}_{r.get('Description','')}_{r.get('Budgeted',0)}_{r.get('Actual',0)}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def import_csv_to_db(csv_path, conn, allow_update_latest=False, allow_update_old=False):
    """Import a CSV into the entries table."""
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

    df = df[expected_cols].copy()
    df["EntryType"] = df["EntryType"].str.lower()

    cur = conn.cursor()
    cur.execute("SELECT * FROM entries WHERE month = ?", (month,))
    existing_rows = cur.fetchall()

    # Determine if updates are allowed
    update_allowed = allow_update_latest or allow_update_old

    if existing_rows and not update_allowed:
        print(f"Month {month} already imported. Skipping.")
        return

    if existing_rows and update_allowed:
        print(f"Updating month {month} ...")
        existing_df = pd.read_sql_query(
            "SELECT entry_type AS EntryType, date AS Date, category AS Category, "
            "subcategory AS Subcategory, description AS Description, "
            "budgeted AS Budgeted, actual AS Actual, account AS Account, notes AS Notes "
            "FROM entries WHERE month = ?",
            conn,
            params=(month,)
        )

        # Add checksum columns for comparison
        df["_checksum"] = df.apply(row_checksum, axis=1)
        existing_df["_checksum"] = existing_df.apply(row_checksum, axis=1)

        # Detect changed or new rows
        changed_df = df[~df["_checksum"].isin(existing_df["_checksum"])].copy()

        if not changed_df.empty:
            print(f"Found {len(changed_df)} new/changed rows for {month}")
            # Delete affected rows
            for _, r in changed_df.iterrows():
                conn.execute("""
                    DELETE FROM entries
                    WHERE month = ? AND category = ? AND subcategory = ? AND description = ?
                """, (month, r["Category"], r["Subcategory"], r["Description"]))
            conn.commit()

            # Insert changed rows
            records = [
                (r["EntryType"], r["Date"], month, r["Category"], r["Subcategory"],
                 r["Description"], r["Budgeted"], r["Actual"], r["Account"], r["Notes"])
                for _, r in changed_df.iterrows()
            ]
            if records:
                conn.executemany("""
                    INSERT INTO entries (
                        entry_type, date, month, category, subcategory,
                        description, budgeted, actual, account, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
                conn.commit()
                print(f"Inserted {len(records)} updated rows for {month}")
        else:
            print(f"No changes detected for {month}.")
        return

    # Insert new month entirely
    records = [
        (r["EntryType"], r["Date"], month, r["Category"], r["Subcategory"],
         r["Description"], r["Budgeted"], r["Actual"], r["Account"], r["Notes"])
        for _, r in df.iterrows()
    ]
    conn.executemany("""
        INSERT INTO entries (
            entry_type, date, month, category, subcategory,
            description, budgeted, actual, account, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()
    print(f"Imported {len(records)} rows from {os.path.basename(csv_path)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--update-old",
        action="store_true",
        help="Allow updating previously imported months if any changes are detected."
    )
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print("Database not found. Run create_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    csv_files = sorted(glob(os.path.join(CSV_DIR, "*.csv")))
    if not csv_files:
        print("No CSV files found in:", CSV_DIR)
        return

    existing_months = get_existing_months(conn)
    latest_month = get_latest_month(conn)
    print(f"Existing months in DB: {sorted(existing_months)}")
    print(f"Latest month in DB: {latest_month}")

    for csv_path in csv_files:
        month = get_month_from_filename(csv_path)
        if not month:
            continue

        allow_update_latest = (month == latest_month)
        allow_update_old = args.update_old and (month in existing_months and month != latest_month)

        import_csv_to_db(
            csv_path,
            conn,
            allow_update_latest=allow_update_latest,
            allow_update_old=allow_update_old
        )

    conn.close()
    print("Import process completed.")

if __name__ == "__main__":
    main()
