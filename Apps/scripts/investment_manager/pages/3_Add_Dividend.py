import streamlit as st
from datetime import date
from data.db_utils import (
    get_holdings,
    process_dividend,    
)

st.title("Add Dividend")

# --- Load holdings for dropdown ---
holdings = get_holdings()

if not holdings:
    st.warning("No holdings found. Please add a stock first.")
    st.stop()

symbols = [h["symbol"] for h in holdings]

symbol = st.selectbox("Select Stock", symbols)

# Get selected holding to pre-fill currency
selected_holding = next(h for h in holdings if h["symbol"] == symbol)
currency = selected_holding["currency"]

st.write(f"**Currency:** {currency}")

# --- Dividend Inputs ---
amount_per_share = st.number_input(
    "Dividend per Share",
    min_value=0.0,
    format="%.4f"
)

tax = st.number_input(
    "Tax Paid (Total)",
    min_value=0.0,
    format="%.2f"
)

date = st.date_input("Dividend Date")

# --- Submit ---
if st.button("Add Dividend"):
    success = process_dividend(
        symbol=symbol,
        amount_per_share=amount_per_share,
        tax=tax,
        currency=currency,
        date=str(date)
    )

    if success:
        st.success(
            f"Dividend added for **{symbol}** "
            f"({amount_per_share} {currency}/share, tax {tax} {currency})."
        )
    else:
        st.error("Error: Could not process dividend (holding not found).")