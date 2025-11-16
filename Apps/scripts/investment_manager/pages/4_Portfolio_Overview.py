import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, update_holding, get_dividends

st.title("📊 Portfolio Overview")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found.")
    st.stop()

df = pd.DataFrame(holdings)

# Ensure numeric columns exist
for col in ["shares", "purchase_price", "current_price", "total_value", "gain_loss", "dividends_received"]:
    df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

df["currency"] = df.get("currency", "")

# --- Load dividends ---
dividends_all = get_dividends()
div_df = pd.DataFrame(dividends_all) if dividends_all else pd.DataFrame(
    columns=["id","symbol","holding_id","num_shares","amount_per_share","tax","currency","date"]
)

# Ensure holding_id exists (migration-safe)
if "holding_id" not in div_df.columns:
    div_df["holding_id"] = None

# Fill missing num_shares for old dividends
holding_shares_map = df.set_index("id")["shares"].to_dict()
div_df["num_shares"] = div_df.apply(
    lambda d: d["num_shares"] if pd.notna(d.get("num_shares")) and d["num_shares"] > 0
    else holding_shares_map.get(d.get("holding_id"), 0),
    axis=1
)

# Calculate net dividends
div_df["net_dividend"] = div_df["num_shares"] * div_df["amount_per_share"] - div_df["tax"]


# --- Dividend mapping logic ---
# 1. Map dividends where holding_id exists
div_sum_map = div_df[div_df["holding_id"].notna()].groupby("holding_id")["net_dividend"].sum().to_dict()

# 2. Fallback for symbols with missing holding_id
div_sum_by_symbol = div_df.groupby("symbol")["net_dividend"].sum().to_dict()

# Final mapping:
df["dividends_received"] = df.apply(
    lambda row: div_sum_map.get(row["id"]) 
                if row["id"] in div_sum_map 
                else div_sum_by_symbol.get(row["symbol"], 0),
    axis=1
)


# Recalculate total value and gain/loss
df["total_value"] = df["shares"] * df["current_price"]
df["gain_loss"] = df["total_value"] - (df["shares"] * df["purchase_price"]) + df["dividends_received"]

# --- Aggregate per symbol ---
agg_list = []

for symbol, group in df.groupby("symbol"):
    total_shares = group["shares"].sum()
    w_avg_price = (group["shares"] * group["purchase_price"]).sum() / total_shares if total_shares > 0 else 0
    total_value = group["total_value"].sum()
    total_dividends = group["dividends_received"].sum()   # This will now include dividends even if holding_id missing
    total_gain_loss = group["gain_loss"].sum()
    current_price = group["current_price"].iloc[-1] if not group["current_price"].isna().all() else 0
    currency = group["currency"].iloc[0] if not group["currency"].isna().all() else ""
    
    agg_list.append({
        "symbol": symbol,
        "shares": total_shares,
        "purchase_price": w_avg_price,
        "current_price": current_price,
        "total_value": total_value,
        "dividends_received": total_dividends,
        "gain_loss": total_gain_loss,
        "currency": currency
    })

agg_df = pd.DataFrame(agg_list)


# --- Update current price ---
st.subheader("Update Current Stock Price")
symbols = agg_df["symbol"].tolist()
selected_symbol = st.selectbox("Select Stock", symbols)
selected_row = agg_df[agg_df["symbol"] == selected_symbol].iloc[0]

new_price = st.number_input(
    "New Current Price",
    min_value=0.0,
    value=float(selected_row["current_price"]),
    format="%.4f"
)

if st.button("Update Price"):
    for _, r in df[df["symbol"] == selected_symbol].iterrows():
        update_holding(r["id"], current_price=new_price)
    st.success(f"Updated price for {selected_symbol}")
    st.experimental_rerun()

# --- Holdings summary ---
st.subheader("📘 Holdings Summary")
st.dataframe(agg_df, width="stretch")

# --- Portfolio totals ---
st.subheader("Portfolio Totals")
total_invested = (df["shares"] * df["purchase_price"]).sum()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Invested", f"{total_invested:,.2f}")
col2.metric("Current Value", f"{agg_df['total_value'].sum():,.2f}")
col3.metric("Dividends Received", f"{agg_df['dividends_received'].sum():,.2f}")
col4.metric("Total Gain/Loss", f"{agg_df['gain_loss'].sum():,.2f}")

# --- Dividend History ---
st.subheader("📜 Dividend History")
div_symbol = st.selectbox("Select Stock to View Dividends", symbols, key="dividend_history")
div_rows = div_df[div_df["symbol"].str.upper() == div_symbol.upper()]

if not div_rows.empty:
    display_df = div_rows.copy()
    display_df = display_df.assign(
        Shares=display_df["num_shares"],
        Amount_Per_Share=display_df["amount_per_share"],
        Tax=display_df["tax"],
        Net_Dividend=display_df["net_dividend"],
        Currency=display_df["currency"],
        Date=display_df["date"]
    )
    st.dataframe(display_df[["Date","Amount_Per_Share","Shares","Tax","Net_Dividend","Currency"]], width="stretch")
    st.metric(
        f"Total Net Dividends for {div_symbol}",
        f"{display_df['Net_Dividend'].sum():,.2f} {display_df['Currency'].iloc[0]}"
    )
else:
    st.info(f"No dividend records found for {div_symbol}.")
