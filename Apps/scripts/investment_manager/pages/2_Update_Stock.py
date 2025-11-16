import streamlit as st
from data.db_utils import get_holdings, update_holding, delete_holding

st.title("Update / Remove Stock Holdings")

holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add stocks first.")
    st.stop()

# Unique stock symbols
symbols = sorted({row["symbol"].upper() for row in holdings})
selected_symbol = st.selectbox("Select Stock", symbols)

# Get all purchases for this stock
symbol_rows = [r for r in holdings if r["symbol"].upper() == selected_symbol]

# Optional: let user select specific purchase
if len(symbol_rows) > 1:
    purchase_dates = [r["purchase_date"] or "Unknown Date" for r in symbol_rows]
    selected_date = st.selectbox("Select Purchase Date", purchase_dates)
    selected_row = symbol_rows[purchase_dates.index(selected_date)]
else:
    selected_row = symbol_rows[0]

st.write(f"Selected Purchase: {selected_row}")

# Update fields
new_shares = st.number_input("Shares", min_value=0.0, value=selected_row["shares"])
new_price = st.number_input("Purchase Price", min_value=0.0, value=selected_row["purchase_price"])
new_currency = st.text_input("Currency", value=selected_row["currency"])

if st.button("Update"):
    update_holding(
        id=selected_row["id"],
        shares=new_shares,
        purchase_price=new_price,
        currency=new_currency
    )
    st.success("Stock purchase updated!")
    st.rerun()

if st.button("Delete"):
    delete_holding(selected_row["id"])
    st.success("Stock purchase deleted!")
    st.rerun()
