# pages/5_Add_Transaction.py

import streamlit as st
from datetime import datetime
from data.db_utils import get_holdings, add_transaction, get_transactions, update_transaction, delete_transaction
import pandas as pd
from utils.calculations import compute_current_shares
import re

st.title("💰 Add Buy / Sell Transaction")

# --- Load available stocks ---
holdings = get_holdings()
symbols = [h["symbol"] for h in holdings]

if not symbols:
    st.warning("No stocks available. Add stocks first in Add Stock page.")
    st.stop()

# --- Transaction Form ---
with st.form("transaction_form"):
    st.subheader("Record a Transaction")

    symbol = st.selectbox("Select Stock", symbols)
    tx_type = st.radio("Transaction Type", ["buy", "sell"])
    shares = st.number_input("Number of Shares", min_value=0.001, value=1.000, step=0.001)
    price = st.number_input("Price per Share", min_value=0.01, value=1.0, format="%.4f")
    tx_date = st.date_input("Transaction Date", datetime.today())

    submitted = st.form_submit_button("Submit Transaction")

    if submitted:
        # --- Check for sufficient shares if selling ---
        if tx_type == "sell":
            owned_shares = compute_current_shares(symbol)
            if shares > owned_shares:
                st.error(f"Cannot sell {shares} shares. Only {owned_shares} shares available!")
            else:
                add_transaction(symbol, shares, price, tx_date, tx_type)
                st.success(f"Sell transaction for {shares} shares of {symbol} recorded.")
        else:
            # Buy transaction
            add_transaction(symbol, shares, price, tx_date, tx_type)
            st.success(f"Buy transaction for {shares} shares of {symbol} recorded.")

# --- Display transactions ---
st.subheader("📄 Recent Transactions")
txs = get_transactions()

# Filter out invalid rows (shares <=0 or price <=0)
txs = [t for t in txs if t["shares"] > 0 and t["price"] > 0]

if txs:
    df_display = pd.DataFrame(txs)
    # Only show relevant columns including 'id' for clarity
    df_display = df_display[["id", "symbol", "type", "shares", "price", "date"]]
    df_display = df_display.rename(columns={
        "id": "Transaction ID",
        "symbol": "Stock",
        "type": "Type",
        "shares": "Shares",
        "price": "Price",
        "date": "Date"
    })
    st.dataframe(df_display, width="stretch")
else:
    st.info("No transactions recorded yet.")

# ----------- Edit transactions------------------
st.subheader("✏️ Edit Transactions")

txs = get_transactions()
# Filter out invalid transactions
txs = [t for t in txs if t["shares"] > 0 and t["price"] > 0]

if txs:
    # Create options as "SYMBOL (ID: 123)"
    tx_options = [f"{t['symbol']} (ID: {t['id']})" for t in txs]
    selected_option = st.selectbox("Select transaction to edit", tx_options)

    # Extract ID safely using regex
    match = re.search(r"ID:\s*(\d+)", selected_option)
    if match:
        selected_id = int(match.group(1))
    else:
        st.error("Failed to parse transaction ID.")
        st.stop()

    tx = next(t for t in txs if t["id"] == selected_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        edit_symbol = st.text_input("Symbol", value=tx["symbol"], key=f"tx_symbol_{selected_id}")
        edit_type = st.selectbox("Type", ["buy", "sell"], index=0 if tx["type"]=="buy" else 1, key=f"tx_type_{selected_id}")
    with col2:
        edit_shares = st.number_input("Shares", value=float(tx["shares"]), step=1.0, min_value=0.0, key=f"tx_shares_{selected_id}")
        edit_price = st.number_input("Price per Share", value=float(tx["price"]), format="%.4f", key=f"tx_price_{selected_id}")
    with col3:
        edit_date = st.date_input("Date", value=pd.to_datetime(tx["date"]).date(), key=f"tx_date_{selected_id}")

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("Save Transaction Changes", key=f"save_tx_{selected_id}"):
            success = update_transaction(
                tx_id=selected_id,
                symbol=edit_symbol,
                tx_type=edit_type,
                shares=edit_shares,
                price=edit_price,
                tx_date=str(edit_date)
            )
            if success:
                st.success(f"Transaction {selected_id} updated.")
                st.rerun()
            else:
                st.error("Failed to update transaction.")

    with col_del:
        confirm_key = f"del_tx_confirm_{selected_id}"
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False

        st.session_state[confirm_key] = st.checkbox(f"Confirm delete transaction {selected_id}", key=f"check_tx_{selected_id}")
        if st.session_state[confirm_key] and st.button("Delete Transaction", key=f"del_tx_{selected_id}"):
            ok = delete_transaction(selected_id)
            if ok:
                st.success(f"Transaction {selected_id} deleted.")
                st.session_state[confirm_key] = False
                st.rerun()
            else:
                st.error("Delete failed.")
