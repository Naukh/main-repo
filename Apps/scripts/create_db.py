#!/usr/bin/env python3
"""
Create the SQLite database and schema for the budget app.
Run this once before importing data.
"""

import sqlite3
import os

DB_PATH = os.path.join("..", "data", "budget.db")

def create_database(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create table for all entries (expenses, income, etc.)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL,               -- e.g. '2024-01'
        entry_type TEXT CHECK(entry_type IN ('budget', 'income')),
        date TEXT,                         -- optional specific date
        category TEXT,
        subcategory TEXT,
        description TEXT,
        budgeted REAL DEFAULT 0,
        actual REAL DEFAULT 0,
        account TEXT,
        notes TEXT
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database created (or already exists) at: {db_path}")
    print("Table 'entries' verified.")

if __name__ == "__main__":
    create_database()
