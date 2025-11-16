import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, update_holding, get_dividends

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

# --- Aggregate multiple purchases per stock ---
def weighted_avg_price(group):
    if group["shares"].sum() == 0:
        return 0
    return (group["shares"] * group["purchase_price"]).sum() / group["shares"].sum()

agg_df = df.groupby("symbol", as_index=False).agg(
    shares=("shares", "sum"),
    purchase_price=("purchase_price", weighted_avg_price),
    current_price=("current_price", "last"),
    total_value=("total_value", "sum"),
    dividends_received=("dividends_received", "sum"),
    gain_loss=("gain_loss", "sum"),
    currency=("currency", "first")
)

# --- Top Section: Update Current Price ---
st.subheader("Update Current Stock Price")

symbols = agg_df["symbol"].tolist()
symbol = st.selectbox("Select Stock", symbols)

# Get aggregated row for selected symbol
row = agg_df[agg_df["symbol"] == symbol].iloc[0]
current_price = row["current_price"]

new_price = st.number_input(
    "New Current Price",
    min_value=0.0,
    value=float(current_price),
    format="%.4f"
)

if st.button("Update Price"):
    # Update all rows of the same symbol in the DB
    symbol_rows = df[df["symbol"] == symbol]
    for _, r in symbol_rows.iterrows():
        try:
            update_holding(int(r["id"]), current_price=new_price)
        except ValueError as e:
            st.error(str(e))

    st.success(f"Updated current price for {symbol}")
    st.rerun()

# --- Clean Portfolio Table ---
st.subheader("📘 Holdings Summary")

display_df = agg_df.copy()

# Fill NaN and ensure numeric
display_df["total_value"] = pd.to_numeric(display_df["total_value"], errors="coerce").fillna(0)
display_df["gain_loss"] = pd.to_numeric(display_df["gain_loss"], errors="coerce").fillna(0)

st.dataframe(display_df, width="stretch")

# --- Portfolio Totals ---
st.subheader("Portfolio Totals")

total_invested = (agg_df["shares"] * agg_df["purchase_price"]).sum()
total_value = agg_df["total_value"].sum()
total_dividends = agg_df["dividends_received"].sum()
total_gain_loss = agg_df["gain_loss"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Invested", f"{total_invested:,.2f}")
col2.metric("Current Value", f"{total_value:,.2f}")
col3.metric("Dividends Received", f"{total_dividends:,.2f}")
col4.metric("Total Gain/Loss", f"{total_gain_loss:,.2f}")

# --- Dividend History Section ---
st.subheader("📜 Dividend History")

div_symbol = st.selectbox("Select Stock to View Dividends", symbols, key="dividend_history")
div_rows = get_dividends(div_symbol)

if not div_rows:
    st.info(f"No dividend records found for {div_symbol}.")
else:
    div_df = pd.DataFrame(div_rows)

    div_df["amount_per_share"] = pd.to_numeric(div_df.get("amount_per_share", 0), errors="coerce").fillna(0)
    div_df["tax"] = pd.to_numeric(div_df.get("tax", 0), errors="coerce").fillna(0)

    shares_held = agg_df[agg_df["symbol"] == div_symbol]["shares"].values[0]
    div_df["shares_held"] = shares_held
    div_df["net_dividend"] = div_df["amount_per_share"] * div_df["shares_held"] - div_df["tax"]

    display_cols = ["date", "amount_per_share", "tax", "shares_held", "net_dividend", "currency"]
    div_df = div_df[display_cols]

    div_df = div_df.rename(columns={
        "date": "Date",
        "amount_per_share": "Amount/Share",
        "tax": "Tax",
        "shares_held": "Shares Held",
        "net_dividend": "Net Dividend",
        "currency": "Currency"
    })

    st.dataframe(div_df, width="stretch")
    total_net = div_df["Net Dividend"].sum()
    st.metric(f"Total Net Dividends for {div_symbol}", f"{total_net:,.2f} {div_df['Currency'].iloc[0]}")
