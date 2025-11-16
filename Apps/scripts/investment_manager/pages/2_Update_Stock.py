import streamlit as st
from data import db_utils

st.title("Update / Remove Stock")

# Fetch all holdings
holdings = db_utils.get_holdings()
symbols = [h['symbol'] for h in holdings]

if not symbols:
    st.info("No stocks in your portfolio. Add some first!")
else:
    selected_symbol = st.selectbox("Select Stock to Update", symbols)
    stock = next((h for h in holdings if h['symbol'] == selected_symbol), None)

    if stock:
        st.subheader(f"Current Info for {stock['symbol']}")
        st.write(f"Shares: {stock['shares']}")
        st.write(f"Purchase Price: {stock['purchase_price']} {stock['currency']}")
        st.write(f"Currency: {stock['currency']}")

        with st.form("update_stock_form"):
            new_shares = st.number_input("Update Number of Shares", min_value=0.0, step=0.01, value=stock['shares'])
            new_purchase_price = st.number_input("Update Purchase Price", min_value=0.0, step=0.01, value=stock['purchase_price'])
            new_currency = st.selectbox("Update Currency", ["USD", "SEK", "EUR", "PKR"], index=["USD","SEK","EUR", "PKR"].index(stock['currency']))

            submitted = st.form_submit_button("Update Stock")
            if submitted:
                db_utils.update_holding(stock['id'], shares=new_shares, purchase_price=new_purchase_price, currency=new_currency)
                st.success(f"{stock['symbol']} updated successfully!")

        st.markdown("---")
        st.subheader("Remove Stock")
        if st.button(f"Delete {stock['symbol']} from Portfolio"):
            db_utils.delete_holding(stock['id'])
            st.warning(f"{stock['symbol']} removed from portfolio!")
