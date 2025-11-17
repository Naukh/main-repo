# pages/1_Add_Stock.py

import streamlit as st
from data.db_utils import add_holding, get_holdings

st.title("➕ Add New Stock to Portfolio")

# --- Form to add stock ---
with st.form("add_stock_form"):
    st.subheader("Add New Stock")
    symbol = st.text_input("Stock Symbol (e.g., AAPL)").upper()
    currency = st.selectbox("Currency", ["PKR", "SEK", "USD", "EUR"], index=0)
    notes = st.text_area("Notes / Comments (optional)")

    submitted = st.form_submit_button("Add Stock")
    if submitted:
        if not symbol:
            st.error("Symbol is required!")
        else:
            add_holding(symbol, currency=currency, notes=notes)
            st.success(f"Stock {symbol} added successfully!")

# --- Display existing holdings ---
st.subheader("📘 Existing Holdings")
holdings = get_holdings()
if holdings:
    st.table([{k: h[k] for k in ["symbol", "currency", "notes"]} for h in holdings])
else:
    st.info("No stocks in portfolio yet.")
