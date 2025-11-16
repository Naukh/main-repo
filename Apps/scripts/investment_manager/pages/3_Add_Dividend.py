import streamlit as st
from data import db_utils
from datetime import date

st.title("Add Dividend")

holdings = db_utils.get_holdings()
symbols = [h['symbol'] for h in holdings]

if not symbols:
    st.warning("No holdings found. Add a stock first!")
else:
    with st.form("add_dividend_form"):
        symbol = st.selectbox("Select Stock", symbols)
        amount = st.number_input("Dividend Amount", min_value=0.0, step=0.01)
        currency = st.selectbox("Currency", ["USD", "SEK", "EUR"])
        dividend_date = st.date_input("Dividend Date", value=date.today())
        
        submitted = st.form_submit_button("Add Dividend")
        
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                db_utils.add_dividend(symbol, amount, currency, str(dividend_date))
                st.success(f"Dividend of {amount} {currency} added for {symbol}.")
