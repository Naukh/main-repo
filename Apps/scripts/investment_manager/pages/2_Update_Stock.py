import streamlit as st
from data.db_utils import get_holdings, update_holding_current_price

st.title("🛠 Update Stock Details")

holdings = get_holdings()
symbols = [h["symbol"] for h in holdings]

if not symbols:
    st.info("No stocks to update. Add some first!")
    st.stop()

selected_symbol = st.selectbox("Select stock to update", symbols)
holding = next(h for h in holdings if h["symbol"] == selected_symbol)

# Editable fields
new_currency = st.selectbox("Currency", ["PKR", "SEK", "USD", "EUR"], index=["PKR","SEK","USD","EUR"].index(holding["currency"]))
new_notes = st.text_area("Notes", value=holding.get("notes",""))
current_price = st.number_input("Current Price", min_value=0.0, value=float(holding.get("current_price",0.0)), format="%.2f")

if st.button("Save Changes"):
    update_holding_current_price(selected_symbol, current_price)
    # TODO: Add update for currency and notes in DB
    st.success(f"{selected_symbol} updated successfully.")
