import pandas as pd

from data.db_utils import get_holdings, get_transactions
from utils.calculations import (
    compute_current_shares,
    calculate_weighted_avg_price,
    calculate_total_value,
    calculate_invested_value,
)


def build_portfolio_summary():
    """
    Builds a portfolio-level summary used by:
    - Portfolio Overview page
    - Reports → Allocation tab

    Returns a DataFrame with ONE ROW PER HOLDING containing:
    - symbol
    - asset_type
    - fund_type
    - currency
    - shares
    - avg_price
    - invested_value
    - current_price
    - total_value
    """

    holdings = get_holdings()
    if not holdings:
        return pd.DataFrame()

    summary_rows = []

    for h in holdings:
        symbol = h["symbol"]
        currency = h.get("currency", "USD")
        asset_type = h.get("asset_type", "stock")
        fund_type = h.get("fund_type", "")
        current_price = float(h.get("current_price", 0.0))

        # -----------------------------
        # Shares & transactions
        # -----------------------------
        shares = compute_current_shares(symbol)

        txs = get_transactions(symbol)
        df_tx = pd.DataFrame(txs) if txs else pd.DataFrame()

        if not df_tx.empty:
            df_tx["price"] = pd.to_numeric(df_tx["price"], errors="coerce").fillna(0.0)
            avg_price = calculate_weighted_avg_price(
                df_tx.assign(purchase_price=df_tx["price"])
            )
        else:
            avg_price = 0.0

        invested_value = calculate_invested_value(shares, avg_price)
        total_value = calculate_total_value(shares, current_price)

        summary_rows.append({
            "symbol": symbol,
            "asset_type": asset_type,
            "fund_type": fund_type,
            "currency": currency,
            "shares": shares,
            "avg_price": avg_price,
            "invested_value": invested_value,
            "current_price": current_price,
            "total_value": total_value,
        })

    summary_df = pd.DataFrame(summary_rows)

    # Ensure numeric safety
    numeric_cols = [
        "shares",
        "avg_price",
        "invested_value",
        "current_price",
        "total_value",
    ]
    for col in numeric_cols:
        summary_df[col] = pd.to_numeric(summary_df[col], errors="coerce").fillna(0.0)

    return summary_df
