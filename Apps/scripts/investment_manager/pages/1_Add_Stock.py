import streamlit as st
from data import db_utils
from datetime import date

st.title("Add New Stock")

with st.form("add_stock_form"):
    symbol = st.text_input("Stock Symbol (e.g., AAPL)").upper()
    shares = st.number_input("Number of Shares", min_value=0.0, step=0.01)
    purchase_price = st.number_input("Purchase Price per Share", min_value=0.0, step=0.01)
    currency = st.selectbox("Currency", ["USD", "SEK", "EUR"])
    purchase_date = st.date_input("Purchase Date", value=date.today())
    
    submitted = st.form_submit_button("Add Stock")
    
    if submitted:
        if not symbol or shares <= 0 or purchase_price <= 0:
            st.error("Please fill all fields with valid values.")
        else:
            db_utils.add_holding(symbol, shares, purchase_price, currency, str(purchase_date))
            st.success(f"{symbol} added to your portfolio!")
