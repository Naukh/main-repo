# pages/6_Add_Index_Fund.py
import streamlit as st
from data.db_utils import add_holding

st.title("📊 Add Index Fund")

with st.form("add_index_fund"):
    symbol = st.text_input("Fund Symbol", placeholder="e.g. VTI, SCHD")
    currency = st.selectbox("Currency", ["PKR", "USD", "EUR", "GBP"])
    fund_type = st.radio("Fund Type", ["growth", "income"])
    notes = st.text_area("Notes (optional)")

    submitted = st.form_submit_button("Add Index Fund")

    if submitted:
        if not symbol:
            st.error("Symbol is required")
        else:
            add_holding(
                symbol=symbol.upper(),
                currency=currency,
                notes=notes,
                asset_type="index_fund",
                fund_type=fund_type
            )
            st.success(f"Index fund {symbol.upper()} added!")
