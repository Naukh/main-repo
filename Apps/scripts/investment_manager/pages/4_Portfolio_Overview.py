import streamlit as st
import pandas as pd
from data import db_utils

st.title("Portfolio Overview")

holdings = db_utils.get_holdings()

if not holdings:
    st.info("No stocks in your portfolio. Add some first!")
else:
    # Example: update current_price manually for now (or fetch via yfinance later)
    for h in holdings:
        h['current_price'] = st.number_input(f"Current price for {h['symbol']} ({h['currency']})", min_value=0.0, step=0.01, value=h.get('current_price') or 0.0)
        h['total_value'] = h['shares'] * h['current_price']
        h['gain_loss'] = h['total_value'] - (h['shares'] * h['purchase_price'])
        h['roi'] = db_utils.calculate_roi(h)

    df = pd.DataFrame(holdings)
    st.dataframe(df[['symbol','shares','purchase_price','currency','current_price','total_value','dividends_received','gain_loss','roi']])
    
    st.metric("Total Portfolio Value", f"{df['total_value'].sum():.2f}")
