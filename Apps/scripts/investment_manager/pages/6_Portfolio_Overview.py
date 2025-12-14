# pages/6_Portfolio_Overview.py

import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, get_transactions, get_dividends, update_holding_current_price
from utils.calculations import compute_current_shares, calculate_weighted_avg_price, calculate_total_value, calculate_invested_value

st.set_page_config(page_title="Portfolio Overview", layout="wide")
st.title("📊 Portfolio Overview")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add some first!")
    st.stop()

df_holdings = pd.DataFrame(holdings)

# --- Update current price manually ---
st.subheader("Update Current Price")
symbols = df_holdings["symbol"].tolist()
selected_symbol = st.selectbox("Select symbol to update price", symbols)
current_price_input = st.number_input(
    f"Enter current price for {selected_symbol}",
    min_value=0.0,
    value=float(df_holdings[df_holdings["symbol"] == selected_symbol]["current_price"].iloc[0]),
    format="%.2f"
)
if st.button("Update Price"):
    ok = update_holding_current_price(selected_symbol, current_price_input)
    if ok:
        st.success(f"Updated {selected_symbol} price to {current_price_input}")
        df_holdings.loc[df_holdings["symbol"] == selected_symbol, "current_price"] = current_price_input

# --- Compute full portfolio summary ---
summaries = []
for idx, row in df_holdings.iterrows():
    symbol = row["symbol"]
    current_price = row.get("current_price", 0.0)
    asset_type = row.get("asset_type", "stock")
    fund_type = row.get("fund_type", "")
    currency = row.get("currency", "USD")


    # Shares & weighted avg price
    cur_shares = compute_current_shares(symbol)
    df_tx = pd.DataFrame(get_transactions(symbol))
    weighted_avg_price = calculate_weighted_avg_price(df_tx.assign(purchase_price=df_tx["price"])) if not df_tx.empty else 0.0
    cost_basis = calculate_invested_value(cur_shares, weighted_avg_price)

    # Dividends
    divs = get_dividends(symbol)
    if divs:
        df_div = pd.DataFrame(divs)
        for c in ["num_shares", "amount_per_share", "tax"]:
            df_div[c] = pd.to_numeric(df_div[c], errors="coerce").fillna(0.0)
        total_dividends = (df_div["num_shares"] * df_div["amount_per_share"]).sum() - df_div["tax"].sum()
    else:
        total_dividends = 0.0

    # Portfolio values
    total_value = calculate_total_value(cur_shares, current_price)
    unrealized = total_value - cost_basis
    total_gain = unrealized + total_dividends
    show_dividends = (
        asset_type == "stock"
        or (asset_type == "index_fund" and fund_type == "income")
    )

    dividend_value = total_dividends if show_dividends else 0.0


    summaries.append({
        "symbol": symbol,
        "asset_type": asset_type,
        "fund_type": fund_type,
        "currency": currency,
        "shares": cur_shares,
        "weighted_avg_price": weighted_avg_price,
        "cost_basis": cost_basis,
        "current_price": current_price,
        "total_value": total_value,
        "unrealized_pl": unrealized,
        "dividends": dividend_value,
        "total_gain": unrealized + dividend_value
    })


summary_df = pd.DataFrame(summaries)

# --- Display portfolio summary ---
st.subheader("📘 Holdings Summary")
display_cols = [
    "symbol",
    "asset_type",
    "fund_type",
    "currency",
    "shares",
    "weighted_avg_price",
    "cost_basis",
    "current_price",
    "total_value",
    "unrealized_pl",
    "dividends",
    "total_gain"
]

st.dataframe(
    summary_df[display_cols],
    width="stretch"
)

# --- Portfolio totals ---
st.subheader("📊 Portfolio Totals by Currency")

for currency, df_cur in summary_df.groupby("currency"):
    st.markdown(f"### {currency}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invested", f"{df_cur['cost_basis'].sum():,.2f}")
    col2.metric("Current Value", f"{df_cur['total_value'].sum():,.2f}")
    col3.metric("Dividends", f"{df_cur['dividends'].sum():,.2f}")
    col4.metric("Total P/L", f"{df_cur['total_gain'].sum():,.2f}")

