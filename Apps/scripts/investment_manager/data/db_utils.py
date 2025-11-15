import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "portfolio.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        purchase_price REAL NOT NULL,
        purchase_date TEXT,
        currency TEXT NOT NULL,
        current_price REAL,
        total_value REAL,
        dividends_received REAL DEFAULT 0,
        gain_loss REAL
    );

    CREATE TABLE IF NOT EXISTS dividends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        date TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        price REAL NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('buy','sell'))
    );

    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        notes TEXT
    );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# --- Holdings CRUD ---

def add_holding(symbol, shares, purchase_price, currency, purchase_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO holdings (symbol, shares, purchase_price, purchase_date, currency) VALUES (?, ?, ?, ?, ?)",
        (symbol.upper(), shares, purchase_price, purchase_date, currency.upper())
    )
    conn.commit()
    conn.close()

def get_holdings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holdings")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_holding(id, shares=None, purchase_price=None, currency=None):
    conn = get_connection()
    cursor = conn.cursor()
    if shares is not None:
        cursor.execute("UPDATE holdings SET shares = ? WHERE id = ?", (shares, id))
    if purchase_price is not None:
        cursor.execute("UPDATE holdings SET purchase_price = ? WHERE id = ?", (purchase_price, id))
    if currency is not None:
        cursor.execute("UPDATE holdings SET currency = ? WHERE id = ?", (currency.upper(), id))
    conn.commit()
    conn.close()

def delete_holding(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holdings WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# --- Dividends CRUD ---

def add_dividend(symbol, amount, currency, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dividends (symbol, amount, currency, date) VALUES (?, ?, ?, ?)",
        (symbol.upper(), amount, currency.upper(), date)
    )
    # Update dividends_received in holdings
    cursor.execute(
        "UPDATE holdings SET dividends_received = dividends_received + ? WHERE symbol = ?",
        (amount, symbol.upper())
    )
    conn.commit()
    conn.close()

def get_dividends(symbol=None):
    conn = get_connection()
    cursor = conn.cursor()
    if symbol:
        cursor.execute("SELECT * FROM dividends WHERE symbol = ?", (symbol.upper(),))
    else:
        cursor.execute("SELECT * FROM dividends")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- ROI Helper ---

def calculate_roi(holding):
    """
    holding: dict with keys symbol, shares, purchase_price, current_price, dividends_received
    Returns ROI as percentage
    """
    invested = holding['shares'] * holding['purchase_price']
    current_value = holding.get('current_price', 0) * holding['shares']
    dividends = holding.get('dividends_received', 0)
    if invested == 0:
        return 0
    roi = ((current_value + dividends - invested) / invested) * 100
    return roi
