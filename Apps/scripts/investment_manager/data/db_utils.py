# data/db_utils.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "portfolio.db"


# ---------------------------------------------------------
# connection helper
# ---------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        currency TEXT NOT NULL DEFAULT 'USD',
        notes TEXT,
        current_price REAL DEFAULT 0.0
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        price REAL NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('buy','sell'))
    );

    CREATE TABLE IF NOT EXISTS dividends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        num_shares REAL NOT NULL,
        amount_per_share REAL NOT NULL,
        tax REAL DEFAULT 0,
        gross_amount REAL,
        net_amount REAL,
        currency TEXT DEFAULT '',
        date TEXT NOT NULL
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


# ---------------------------------------------------------
# HOLDINGS CRUD
# ---------------------------------------------------------

def add_holding(symbol: str, currency="USD", notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO holdings (symbol, currency, notes)
        VALUES (?, ?, ?)
    """, (symbol.upper(), currency.upper(), notes))
    conn.commit()
    conn.close()


def get_holdings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holdings ORDER BY symbol ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_holding(symbol: str, currency=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    if currency is not None:
        updates.append("currency=?")
        values.append(currency.upper())

    if notes is not None:
        updates.append("notes=?")
        values.append(notes)

    if not updates:
        return

    values.append(symbol.upper())
    cursor.execute(f"""
        UPDATE holdings SET {", ".join(updates)}
        WHERE symbol=?
    """, values)

    conn.commit()
    conn.close()


def delete_holding(symbol: str):
    """Deletes holding but **keeps** transaction history unless user deletes manually."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holdings WHERE symbol=?", (symbol.upper(),))
    conn.commit()
    conn.close()

def update_holding_current_price(symbol: str, price: float) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE holdings SET current_price = ? WHERE symbol = ?",
            (price, symbol.upper())
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating current price: {e}")
        return False
    finally:
        conn.close()



# ---------------------------------------------------------
# TRANSACTION CRUD
# ---------------------------------------------------------

def add_transaction(symbol, shares, price, date, type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (symbol, shares, price, date, type)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol.upper(), shares, price, date, type))
    conn.commit()
    conn.close()


def update_transaction(tx_id: int, symbol: str, tx_type: str, shares: float, price: float, tx_date: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE transactions
            SET symbol = ?, type = ?, shares = ?, price = ?, date = ?
            WHERE id = ?
            """,
            (symbol.upper(), tx_type.lower(), shares, price, tx_date, tx_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating transaction: {e}")
        return False
    finally:
        conn.close()


def delete_transaction(tx_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return False
    finally:
        conn.close()

def get_transactions(symbol=None):
    conn = get_connection()
    cursor = conn.cursor()

    if symbol:
        cursor.execute(
            "SELECT * FROM transactions WHERE UPPER(symbol)=? ORDER BY date ASC",
            (symbol.upper(),),
        )
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY date ASC")

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------
# DIVIDENDS CRUD
# ---------------------------------------------------------

def add_dividend(symbol, num_shares, amount_per_share, tax, currency, date):
    conn = get_connection()
    cursor = conn.cursor()

    net_amount = (num_shares * amount_per_share) - tax
    gross_amount = num_shares * amount_per_share

    cursor.execute("""
        INSERT INTO dividends (symbol, num_shares, amount_per_share, tax, gross_amount, net_amount, currency, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol.upper(), num_shares, amount_per_share, tax,
        gross_amount, net_amount,
        currency.upper() if currency else "",
        date
    ))

    conn.commit()
    conn.close()



def delete_dividend(div_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dividends WHERE id=?", (div_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_dividends(symbol=None):
    conn = get_connection()
    cursor = conn.cursor()

    if symbol:
        cursor.execute("""
            SELECT * FROM dividends
            WHERE UPPER(symbol)=?
            ORDER BY date ASC
        """, (symbol.upper(),))
    else:
        cursor.execute("SELECT * FROM dividends ORDER BY date ASC")

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_dividend_record(div_id: int, num_shares, amount_per_share, tax, currency, date):
    """
    Update a dividend record by ID.
    Also updates gross_amount and net_amount automatically.
    """
    conn = get_connection()
    cursor = conn.cursor()

    gross_amount = num_shares * amount_per_share
    net_amount = gross_amount - tax

    cursor.execute("""
        UPDATE dividends
        SET num_shares=?, amount_per_share=?, tax=?, gross_amount=?, net_amount=?, currency=?, date=?
        WHERE id=?
    """, (
        num_shares, amount_per_share, tax, gross_amount, net_amount,
        currency.upper() if currency else "", date, div_id
    ))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# -----------------------------
# Update stock symbol, currency, notes in holdings
# -----------------------------
def update_holding_symbol_currency(stock_id: int, new_symbol: str, new_currency: str, new_notes: str = "") -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE holdings
            SET symbol = ?, currency = ?, notes = ?
            WHERE id = ?
        """, (new_symbol, new_currency, new_notes, stock_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating stock:", e)
        return False


# -----------------------------
# Update transaction symbol by transaction ID
# -----------------------------
def update_transaction_symbol(tx_id: int, new_symbol: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions
            SET symbol = ?
            WHERE id = ?
        """, (new_symbol, tx_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating transaction symbol:", e)
        return False


# -----------------------------
# Update dividend symbol by dividend ID
# -----------------------------
def update_dividend_symbol(div_id: int, new_symbol: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE dividends
            SET symbol = ?
            WHERE id = ?
        """, (new_symbol, div_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating dividend symbol:", e)
        return False
# ---------------------------------------------------------
