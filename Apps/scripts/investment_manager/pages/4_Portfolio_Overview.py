import streamlit as st
import pandas as pd
from data.db_utils import (
    get_holdings,
    update_holding,
)

st.title("Portfolio Overview")

# --- Load holdings ---
holdings = get_holdings()

if not holdings:
    st.info("No holdings found. Add stocks in the 'Add Stock' page.")
    st.stop()

# Convert to DataFrame for clean table rendering
df = pd.DataFrame(holdings)

# --- Top Section: Update Current Price ---
st.subheader("Update Current Stock Price")

symbols = df["symbol"].tolist()

symbol = st.selectbox("Select Stock", symbols)

# Get row for selected symbol
row = df[df["symbol"] == symbol].iloc[0]
current_price = row["current_price"]

new_price = st.number_input(
    "New Current Price",
    min_value=0.0,
    value=float(current_price) if current_price else 0.0,
    format="%.4f"
)

if st.button("Update Price"):
    update_holding(row["id"], purchase_price=None)  # no change
    # update price separately to avoid confusion
    from data.db_utils import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    # calculate updated total_value & gain_loss
    shares = row["shares"]
    purchase_price = row["purchase_price"]
    dividends_received = row["dividends_received"]

    total_value = shares * new_price
    cost_basis = shares * purchase_price
    gain_loss = (total_value - cost_basis) + dividends_received

    cursor.execute(
        "UPDATE holdings SET current_price=?, total_value=?, gain_loss=? WHERE id=?",
        (new_price, total_value, gain_loss, row["id"])
    )

    conn.commit()
    conn.close()

    st.success(f"Updated current price for {symbol}")

    # Refresh after update
    st.rerun()


# --- Clean Portfolio Table ---
st.subheader("📘 Holdings Summary")

display_df = df.copy()

# Hide internal columns
drop_cols = ["id"]
for col in drop_cols:
    if col in display_df:
        display_df = display_df.drop(columns=col)

# Format values if needed
display_df["total_value"] = display_df["total_value"].fillna(0)
display_df["gain_loss"] = display_df["gain_loss"].fillna(0)

st.dataframe(display_df, width="stretch")

# --- Portfolio Totals ---
st.subheader("Portfolio Totals")

total_invested = (df["shares"] * df["purchase_price"]).sum()
total_value = df["total_value"].fillna(0).sum()
total_dividends = df["dividends_received"].sum()
total_gain_loss = df["gain_loss"].fillna(0).sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Invested", f"{total_invested:,.2f}")
col2.metric("Current Value", f"{total_value:,.2f}")
col3.metric("Dividends Received", f"{total_dividends:,.2f}")
col4.metric("Total Gain/Loss", f"{total_gain_loss:,.2f}")
