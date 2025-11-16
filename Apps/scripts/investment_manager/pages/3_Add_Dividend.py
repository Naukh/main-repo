import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, process_dividend, get_dividends, delete_dividend, update_dividend_record

st.title("Add / Edit Dividend Payout")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add stocks first.")
    st.stop()

# --- Select Stock ---
symbols = sorted({row["symbol"].upper() for row in holdings})
selected_symbol = st.selectbox("Select Stock", symbols, key="select_stock")

# --- Select specific purchase if multiple ---
symbol_rows = [r for r in holdings if r["symbol"].upper() == selected_symbol]
if len(symbol_rows) > 1:
    purchase_dates = [r.get("purchase_date") or "Unknown Date" for r in symbol_rows]
    selected_date = st.selectbox("Select Purchase Date", purchase_dates, key="select_purchase_date")
    selected_row = symbol_rows[purchase_dates.index(selected_date)]
else:
    selected_row = symbol_rows[0]

st.write(f"Recording dividend for: {selected_symbol} (Purchase Date: {selected_row.get('purchase_date','Unknown')})")

# --- Add New Dividend ---
st.subheader("Add New Dividend")
num_shares = st.number_input(
    "Number of Shares for Dividend",
    min_value=0.0,
    max_value=selected_row["shares"],
    value=selected_row["shares"],
    step=1.0,
    key="add_num_shares"
)
amount_per_share = st.number_input("Amount per Share", min_value=0.0, value=0.0, key="add_amount_per_share")
tax = st.number_input("Tax", min_value=0.0, value=0.0, key="add_tax")
currency = st.text_input("Currency", value=selected_row["currency"], key="add_currency")
date = st.date_input("Date", key="add_date")

# Preview net dividend
st.info(f"Net Dividend will be: {num_shares * amount_per_share - tax:.2f} {currency}")

if st.button("Add Dividend", key="add_dividend_button"):
    dividend_id = process_dividend(
        symbol=selected_symbol,
        num_shares=num_shares,
        amount_per_share=amount_per_share,
        tax=tax,
        currency=currency,
        date=date,
        holding_id=selected_row["id"]
    )
    st.success(f"✅ Dividend recorded! ID: {dividend_id}")
    st.rerun()

# --- Show & Edit Dividend History ---
st.subheader(f"Dividend History for {selected_symbol}")
dividend_rows = get_dividends(selected_symbol)

if dividend_rows:
    df_div = pd.DataFrame(dividend_rows)
    for col in ["num_shares", "amount_per_share", "tax"]:
        if col not in df_div.columns:
            df_div[col] = 0
        df_div[col] = pd.to_numeric(df_div[col], errors="coerce").fillna(0)
    df_div["net_dividend"] = df_div["num_shares"] * df_div["amount_per_share"] - df_div["tax"]

    st.dataframe(df_div[["id","symbol","num_shares","amount_per_share","tax","currency","date","net_dividend"]])

    # --- Edit / Delete ---
    st.subheader("Edit or Delete Dividend Entry")
    selected_div_id = st.selectbox("Select Dividend ID", df_div["id"].tolist(), key="select_dividend_id")
    selected_div_row = df_div[df_div["id"] == selected_div_id].iloc[0]

    edit_num_shares = st.number_input("Number of Shares", value=selected_div_row["num_shares"], min_value=0.0, step=1.0, key=f"edit_num_shares_{selected_div_id}")
    edit_amount_per_share = st.number_input("Amount per Share", value=selected_div_row["amount_per_share"], min_value=0.0, key=f"edit_amount_per_share_{selected_div_id}")
    edit_tax = st.number_input("Tax", value=selected_div_row["tax"], min_value=0.0, key=f"edit_tax_{selected_div_id}")
    edit_currency = st.text_input("Currency", value=selected_div_row["currency"], key=f"edit_currency_{selected_div_id}")
    edit_date = st.date_input("Date", pd.to_datetime(selected_div_row["date"]), key=f"edit_date_{selected_div_id}")

    st.info(f"Updated Net Dividend: {edit_num_shares*edit_amount_per_share - edit_tax:.2f} {edit_currency}")

    if st.button("Update Dividend", key="update_dividend_button"):
        success = update_dividend_record(
            dividend_id=selected_div_id,
            num_shares=edit_num_shares,
            amount_per_share=edit_amount_per_share,
            tax=edit_tax,
            currency=edit_currency,
            date=edit_date
        )
        st.success("Dividend updated!" if success else "Update failed.")
        st.rerun()

    if st.button("Delete Dividend", key="delete_dividend_button"):
        success = delete_dividend(selected_div_id)
        st.success("Deleted!" if success else "Delete failed.")
        st.rerun()
else:
    st.info("No dividends recorded for this stock yet.")
