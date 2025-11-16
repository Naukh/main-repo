import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, update_holding

st.title("📊 Portfolio Overview")

# --- Load holdings ---
holdings = get_holdings()

if not holdings:
    st.info("No holdings found. Add stocks in the 'Add Stock' page.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(holdings)

# Ensure numeric columns are proper dtype
numeric_cols = ["shares", "purchase_price", "current_price", "total_value", "dividends_received", "gain_loss"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

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
    value=float(current_price),
    format="%.4f"
)

if st.button("Update Price"):
    try:
        update_holding(int(row["id"]), current_price=new_price)
        st.success(f"Updated current price for {symbol}")
        st.rerun()
    except ValueError as e:
        st.error(str(e))

# --- Clean Portfolio Table ---
st.subheader("📘 Holdings Summary")

display_df = df.copy()

# Hide internal columns
display_df = display_df.drop(columns=[c for c in ["id"] if c in display_df])

# Fill NaN and convert to numeric explicitly to avoid FutureWarnings
display_df["total_value"] = pd.to_numeric(display_df["total_value"], errors="coerce").fillna(0)
display_df["gain_loss"] = pd.to_numeric(display_df["gain_loss"], errors="coerce").fillna(0)

st.dataframe(display_df, use_container_width=True)

# --- Portfolio Totals ---
st.subheader("Portfolio Totals")

total_invested = (df["shares"] * df["purchase_price"]).sum()
total_value = df["total_value"].sum()
total_dividends = df["dividends_received"].sum()
total_gain_loss = df["gain_loss"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Invested", f"{total_invested:,.2f}")
col2.metric("Current Value", f"{total_value:,.2f}")
col3.metric("Dividends Received", f"{total_dividends:,.2f}")
col4.metric("Total Gain/Loss", f"{total_gain_loss:,.2f}")
