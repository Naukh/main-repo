# utils/calculations.py

"""
Centralized portfolio calculation functions.
All math for totals, averages, P/L, and dividends lives here.
"""

import sqlite3
from pathlib import Path
import pandas as pd
from data.db_utils import get_holdings, get_connection, get_dividends, get_transactions
from datetime import datetime


# -----------------------------
#   BASIC CALCULATIONS
# -----------------------------

def calculate_total_value(shares: float, current_price: float) -> float:
    """Total market value of shares."""
    return float(shares) * float(current_price)


def calculate_invested_value(shares: float, purchase_price: float) -> float:
    """Total money originally invested."""
    return float(shares) * float(purchase_price)


def calculate_weighted_avg_price(df: pd.DataFrame) -> float:
    """
    Weighted average purchase price for a group of holdings of the same symbol.
    Expects columns: 'shares', 'purchase_price'
    """
    if df.empty or df["shares"].sum() == 0:
        return 0.0

    weighted_avg = (df["shares"] * df["purchase_price"]).sum() / df["shares"].sum()
    return float(weighted_avg)



def calculate_gain_loss(
    shares: float,
    purchase_price: float,
    current_price: float,
    dividends_received: float
) -> float:
    """
    Gain/Loss = Current Value - Invested + Dividends
    """
    invested = calculate_invested_value(shares, purchase_price)
    current_value = calculate_total_value(shares, current_price)
    return current_value - invested + dividends_received

def compute_portfolio_summary(price_map: dict) -> pd.DataFrame:
    """
    Minimal version: compute total shares, cost basis, and total value
    using transactions only.
    """
    summaries = []
    for symbol, current_price in price_map.items():
        txs = get_transactions(symbol)
        if not txs:
            shares = 0.0
            invested = 0.0
        else:
            df_tx = pd.DataFrame(txs)
            df_tx["shares"] = pd.to_numeric(df_tx["shares"], errors="coerce").fillna(0)
            df_tx["price"] = pd.to_numeric(df_tx["price"], errors="coerce").fillna(0)
            df_tx["type"] = df_tx["type"].astype(str)

            buys = df_tx[df_tx["type"] == "buy"]
            sells = df_tx[df_tx["type"] == "sell"]

            shares = buys["shares"].sum() - sells["shares"].sum()
            invested = (buys["shares"] * buys["price"]).sum() - (sells["shares"] * sells["price"]).sum()

        total_value = shares * current_price
        total_gain = total_value - invested  # minimal version, ignoring dividends for now

        summaries.append({
            "symbol": symbol,
            "shares": shares,
            "cost_basis": invested,
            "current_price": current_price,
            "total_value": total_value,
            "total_gain": total_gain
        })

    return pd.DataFrame(summaries)


def load_transactions(symbol=None) -> pd.DataFrame:
    conn = get_connection()
    cursor = conn.cursor()
    if symbol:
        cursor.execute(
            "SELECT * FROM transactions WHERE UPPER(symbol)=? ORDER BY date ASC",
            (symbol.upper(),)
        )
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY date ASC")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        df = pd.DataFrame(rows)
        # Ensure numeric columns exist
        for c in ["shares", "price"]:
            if c not in df.columns:
                df[c] = 0
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        # Ensure type column exists
        if "type" not in df.columns:
            df["type"] = ""
        else:
            df["type"] = df["type"].astype(str)
        return df
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["id", "symbol", "shares", "price", "date", "type"])


def compute_current_shares(symbol: str) -> float:
    """
    Compute total shares owned for a symbol from transactions (buys - sells)
    """
    df = pd.DataFrame(get_transactions())
    if df.empty:
        return 0.0
    
    # Filter for symbol (case-insensitive)
    df = df[df["symbol"].str.upper() == symbol.upper()]
    if df.empty:
        return 0.0
    
    # Ensure numeric
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce").fillna(0)
    df["type"] = df["type"].astype(str).str.lower()
    
    buys = df[df["type"] == "buy"]["shares"].sum()
    sells = df[df["type"] == "sell"]["shares"].sum()
    
    return float(buys - sells)


# -----------------------------
#   DIVIDEND CALCULATIONS
# -----------------------------

def calculate_net_dividend(num_shares: float, amount_per_share: float, tax: float) -> float:
    """
    Return net dividend after tax.
    """
    gross = float(num_shares) * float(amount_per_share)
    return gross - float(tax)


def total_dividends_for_symbol(div_df: pd.DataFrame) -> float:
    """
    Accept a dataframe of dividends for one symbol.
    Must have columns: num_shares, amount_per_share, tax
    """
    if div_df.empty:
        return 0.0
    gross = (div_df["num_shares"] * div_df["amount_per_share"]).sum()
    tax = div_df["tax"].sum()
    return gross - tax


# -----------------------------
#   PORTFOLIO AGGREGATIONS
# -----------------------------

def aggregate_symbol(group: pd.DataFrame) -> dict:
    """
    Aggregates holdings dataframe grouped by symbol.

    Expected columns:
    - shares
    - purchase_price
    - current_price
    - total_value
    - gain_loss
    - dividends_received
    - currency
    """
    total_shares = group["shares"].sum()
    w_avg_price = calculate_weighted_avg_price(group)
    current_price = group["current_price"].iloc[-1] if not group["current_price"].isna().all() else 0

    return {
        "symbol": group["symbol"].iloc[0],
        "shares": total_shares,
        "purchase_price": w_avg_price,
        "current_price": current_price,
        "total_value": group["total_value"].sum(),
        "dividends_received": group["dividends_received"].sum(),
        "gain_loss": group["gain_loss"].sum(),
        "currency": group["currency"].iloc[0]
    }
