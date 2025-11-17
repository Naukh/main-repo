# pages/3_Add_Dividend.py

import streamlit as st
from datetime import datetime
import pandas as pd
from data.db_utils import get_holdings, add_dividend

st.set_page_config(page_title="Add Dividend", layout="wide")
st.title("💵 Add Dividend Entry")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add some stocks first.")
    st.stop()

df = pd.DataFrame(holdings)
symbols = df["symbol"].tolist()

# --- Dividend input form ---
st.subheader("Enter Dividend Details")

selected_symbol = st.selectbox("Select Stock Symbol", symbols)
selected_row = df[df["symbol"] == selected_symbol].iloc[0]

num_shares = st.number_input(
    "Number of shares",
    min_value=0.0,
    value=float(selected_row.get("shares", 0)),
    step=0.01
)

amount_per_share = st.number_input(
    "Dividend amount per share",
    min_value=0.0,
    value=0.0,
    step=0.0001
)

tax = st.number_input("Tax amount", min_value=0.0, value=0.0, step=0.01)
currency = st.text_input("Currency", value=selected_row.get("currency", "USD"))
date = st.date_input("Dividend Date", value=datetime.today())

if st.button("Add Dividend"):
    add_dividend(
        symbol=selected_symbol,
        num_shares=num_shares,
        amount_per_share=amount_per_share,
        tax=tax,
        currency=currency,
        date=str(date)
    )
    st.success(f"Dividend added for {selected_symbol}")
    st.rerun()

# --- Optional: show recent dividends ---
st.subheader("Recent Dividends")
from data.db_utils import get_dividends

recent_divs = get_dividends(selected_symbol)
if recent_divs:
    div_df = pd.DataFrame(recent_divs)
    div_df["date"] = pd.to_datetime(div_df["date"]).dt.strftime("%Y-%m-%d")
    div_df["gross_amount"] = div_df["gross_amount"].fillna(0)
    div_df["net_amount"] = div_df["net_amount"].fillna(0)
    div_df["tax"] = div_df["tax"].fillna(0)
    st.dataframe(div_df.sort_values("date", ascending=False), width="stretch")
else:
    st.info(f"No dividends recorded for {selected_symbol}.")
