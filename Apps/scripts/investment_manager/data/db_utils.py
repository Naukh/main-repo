import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "portfolio.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Initialization ---
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
        holding_id INTEGER,
        num_shares REAL NOT NULL,
        amount_per_share REAL NOT NULL,
        tax REAL DEFAULT 0,
        currency TEXT DEFAULT '',
        date TEXT NOT NULL,
        FOREIGN KEY (holding_id) REFERENCES holdings(id)
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
    cursor.execute("""
        INSERT INTO holdings (symbol, shares, purchase_price, purchase_date, currency)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol.upper(), shares, purchase_price, purchase_date, currency.upper()))
    conn.commit()
    conn.close()


def get_holdings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holdings")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_holding(holding_id, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    cursor = conn.cursor()
    columns = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [holding_id]
    cursor.execute(f"UPDATE holdings SET {columns} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_holding(holding_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holdings WHERE id=?", (holding_id,))
    conn.commit()
    conn.close()


# --- Dividends CRUD ---
def process_dividend(symbol, amount_per_share, tax=0, currency="", date=None, holding_id=None, num_shares=None):
    """
    Insert dividend record.
    Updates holding's dividends_received, total_value, gain_loss.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Determine num_shares if not provided and holding_id exists
    if holding_id and num_shares is None:
        cursor.execute("SELECT shares FROM holdings WHERE id=?", (holding_id,))
        row = cursor.fetchone()
        num_shares = row["shares"] if row else 0
    elif num_shares is None:
        # Apply to all holdings of symbol if holding_id not specified
        cursor.execute("SELECT id, shares FROM holdings WHERE symbol=?", (symbol.upper(),))
        rows = cursor.fetchall()
        if rows:
            # Apply to first holding by default if not specified
            holding_id = rows[0]["id"]
            num_shares = rows[0]["shares"]
        else:
            num_shares = 0

    # Insert dividend record
    cursor.execute("""
        INSERT INTO dividends (symbol, holding_id, num_shares, amount_per_share, tax, currency, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (symbol.upper(), holding_id, num_shares, amount_per_share, tax, currency, date))
    dividend_id = cursor.lastrowid

    # Update holding's dividends_received
    net_div = (num_shares * amount_per_share) - tax
    if holding_id:
        cursor.execute("SELECT shares, purchase_price, current_price, dividends_received FROM holdings WHERE id=?", (holding_id,))
        row = cursor.fetchone()
        if row:
            new_div = (row["dividends_received"] or 0) + net_div
            total_value = (row["shares"] * (row["current_price"] or 0))
            gain_loss = total_value - (row["shares"] * row["purchase_price"]) + new_div
            cursor.execute("""
                UPDATE holdings
                SET dividends_received=?, total_value=?, gain_loss=?
                WHERE id=?
            """, (new_div, total_value, gain_loss, holding_id))

    conn.commit()
    conn.close()
    return dividend_id


def get_dividends(symbol=None):
    conn = get_connection()
    cursor = conn.cursor()
    if symbol:
        cursor.execute("SELECT * FROM dividends WHERE UPPER(symbol)=?", (symbol.upper(),))
    else:
        cursor.execute("SELECT * FROM dividends")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_dividend_record(dividend_id, num_shares, amount_per_share, tax, currency, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE dividends
        SET num_shares=?, amount_per_share=?, tax=?, currency=?, date=?
        WHERE id=?
    """, (num_shares, amount_per_share, tax, currency, str(date), dividend_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def delete_dividend(dividend_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dividends WHERE id=?", (dividend_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success
