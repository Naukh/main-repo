# pages/2_Update_Stock.py

import streamlit as st
from data.db_utils import get_holdings, update_holding_symbol_currency, get_transactions, update_transaction_symbol, get_dividends, update_dividend_symbol

st.title("📝 Update Stock")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No stocks to update. Add holdings first.")
    st.stop()

# Select holding to update
symbols = [h["symbol"] for h in holdings]
selected_symbol = st.selectbox("Select stock to update", symbols)
holding = next(h for h in holdings if h["symbol"] == selected_symbol)

st.subheader(f"Update {selected_symbol}")

# --- Edit symbol / currency / notes ---
with st.form("update_stock_form"):
    new_symbol = st.text_input("Stock Symbol", value=holding["symbol"])
    new_currency = st.selectbox("Currency", ["PKR", "SEK", "USD", "EUR"], index=["PKR", "SEK", "USD", "EUR"].index(holding["currency"]))
    new_notes = st.text_area("Notes / Comments (optional)", value=holding.get("notes", ""))

    submitted = st.form_submit_button("Update Stock")
    if submitted:
        # Update holding first
        success_holding = update_holding_symbol_currency(holding["id"], new_symbol, new_currency, new_notes)

        # Update all transactions with this symbol
        txs = get_transactions()
        txs_to_update = [t for t in txs if t["symbol"] == selected_symbol]
        tx_success = True
        for tx in txs_to_update:
            if not update_transaction_symbol(tx["id"], new_symbol):
                tx_success = False

        # Update all dividends with this symbol
        divs = get_dividends(selected_symbol)
        div_success = True
        for div in divs:
            if not update_dividend_symbol(div["id"], new_symbol):
                div_success = False

        if success_holding and tx_success and div_success:
            st.success(f"Stock '{selected_symbol}' updated to '{new_symbol}' with currency {new_currency}.")
            st.rerun()
        else:
            st.error("Failed to update all records. Check logs for details.")
