# pages/7_Portfolio_Overview.py

import streamlit as st
import pandas as pd
from data.db_utils import get_holdings, get_transactions, get_dividends, update_holding_current_price
from utils.calculations import compute_current_shares, calculate_weighted_avg_price, calculate_total_value, calculate_invested_value

def color_pl(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "color: #2ecc71; font-weight: 600;"   # green
    elif val < 0:
        return "color: #e74c3c; font-weight: 600;"   # red
    return ""

def color_pct(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "color: #2ecc71;"
    elif val < 0:
        return "color: #e74c3c;"
    return ""


st.set_page_config(page_title="Portfolio Overview", layout="wide")
st.title("📊 Portfolio Overview")

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add some first!")
    st.stop()

df_holdings = pd.DataFrame(holdings)

# --- Update current price manually ---
st.subheader("Update Current Price")
symbols = df_holdings["symbol"].tolist()
selected_symbol = st.selectbox("Select symbol to update price", symbols)
current_price_input = st.number_input(
    f"Enter current price for {selected_symbol}",
    min_value=0.0,
    value=float(df_holdings[df_holdings["symbol"] == selected_symbol]["current_price"].iloc[0]),
    format="%.2f"
)
if st.button("Update Price"):
    ok = update_holding_current_price(selected_symbol, current_price_input)
    if ok:
        st.success(f"Updated {selected_symbol} price to {current_price_input}")
        df_holdings.loc[df_holdings["symbol"] == selected_symbol, "current_price"] = current_price_input

# --- Compute full portfolio summary ---
summaries = []
for idx, row in df_holdings.iterrows():
    symbol = row["symbol"]
    current_price = row.get("current_price", 0.0)
    asset_type = row.get("asset_type", "stock")
    fund_type = row.get("fund_type", "")
    currency = row.get("currency", "USD")


    # Shares & weighted avg price
    cur_shares = compute_current_shares(symbol)
    df_tx = pd.DataFrame(get_transactions(symbol))
    weighted_avg_price = calculate_weighted_avg_price(df_tx.assign(purchase_price=df_tx["price"])) if not df_tx.empty else 0.0
    cost_basis = calculate_invested_value(cur_shares, weighted_avg_price)

    # Dividends
    divs = get_dividends(symbol)
    if divs:
        df_div = pd.DataFrame(divs)
        for c in ["num_shares", "amount_per_share", "tax"]:
            df_div[c] = pd.to_numeric(df_div[c], errors="coerce").fillna(0.0)
        total_dividends = (df_div["num_shares"] * df_div["amount_per_share"]).sum() - df_div["tax"].sum()
    else:
        total_dividends = 0.0

    # Portfolio values
    total_value = calculate_total_value(cur_shares, current_price)
    unrealized = total_value - cost_basis
    total_gain = unrealized + total_dividends
    roi_pct = (total_gain / cost_basis * 100) if cost_basis > 0 else 0.0

    show_dividends = (
        asset_type == "stock"
        or (asset_type == "index_fund" and fund_type == "income")
    )

    dividend_value = total_dividends if show_dividends else 0.0
    dividend_yield = (dividend_value * 100 / total_value if total_value > 0 else 0.0)



    summaries.append({
        "symbol": symbol,
        "asset_type": asset_type,
        "fund_type": fund_type,
        "currency": currency,
        "shares": cur_shares,
        "weighted_avg_price": weighted_avg_price,
        "cost_basis": cost_basis,
        "current_price": current_price,
        "total_value": total_value,
        "unrealized_pl": unrealized,
        "dividends": dividend_value,
        "total_gain": unrealized + dividend_value,
        "roi_pct": roi_pct,
        "dividend_yield": dividend_yield
    })


summary_df = pd.DataFrame(summaries)

# --- Display portfolio summary ---
st.subheader("📘 Holdings Summary")
display_cols = [
    "symbol",
    "asset_type",
    "fund_type",
    "currency",
    "shares",
    "weighted_avg_price",
    "cost_basis",
    "current_price",
    "total_value",
    "unrealized_pl",
    "dividends",
    "dividend_yield",
    "roi_pct",
    "total_gain"
]

styled_summary = (
    summary_df[display_cols]
    .style
    .map(color_pl, subset=["unrealized_pl", "total_gain"])
    .map(color_pct, subset=["dividend_yield", "roi_pct"])
    .format({
        "dividend_yield": "{:.2f}%",
        "roi_pct": "{:.2f}%",
        "unrealized_pl": "{:,.2f}",
        "total_gain": "{:,.2f}",
    })
)

st.dataframe(styled_summary, width="stretch")


# --- Portfolio totals ---
st.subheader("📊 Portfolio Totals by Currency")

for currency, df_cur in summary_df.groupby("currency"):
    st.markdown(f"### {currency}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invested", f"{df_cur['cost_basis'].sum():,.2f}")
    col2.metric("Current Value", f"{df_cur['total_value'].sum():,.2f}")
    col3.metric("Dividends", f"{df_cur['dividends'].sum():,.2f}")
    col4.metric("Total P/L", f"{df_cur['total_gain'].sum():,.2f}")

st.divider()
st.subheader("💸 Income-Generating Assets")

income_df = summary_df[
    (summary_df["asset_type"] == "stock") |
    (
        (summary_df["asset_type"] == "index_fund") &
        (summary_df["fund_type"] == "income")
    )
]

if not income_df.empty:
    styled_income = (
        income_df[
            [
                "symbol",
                "asset_type",
                "currency",
                "total_value",
                "dividends",
                "dividend_yield",
                "roi_pct",
            ]
        ]
        .style
        .map(color_pl, subset=["dividends"])
        .map(color_pct, subset=["dividend_yield", "roi_pct"])
        .format({
            "dividend_yield": "{:.2f}%",
            "roi_pct": "{:.2f}%",
            "dividends": "{:,.2f}",
        })
    )

    st.dataframe(styled_income, width="stretch")

else:
    st.info("No income-generating assets found.")

# --- FX-Normalized Portfolio View ---
with st.container():
    st.markdown("---")
    st.subheader("🌍 FX-Normalized Portfolio (Optional)")

    base_currency = st.selectbox(
        "Select base currency",
        options=sorted(summary_df["currency"].unique().tolist()),
        index=0
    )

    st.markdown("#### Enter FX rates (to base currency)")

    fx_rates = {}
    for cur in summary_df["currency"].unique():
        if cur == base_currency:
            fx_rates[cur] = 1.0
            st.write(f"**{cur} → {base_currency}: 1.0 (base)**")
        else:
            fx_rates[cur] = st.number_input(
                f"{cur} → {base_currency}",
                min_value=0.000001,
                value=1.0,
                step=0.01,
                format="%.6f",
                key=f"fx_{cur}_to_{base_currency}"
            )

    fx_df = summary_df.copy()
    fx_df["fx_rate"] = fx_df["currency"].map(fx_rates)

    for col in ["cost_basis", "total_value", "dividends", "total_gain"]:
        fx_df[f"{col}_fx"] = fx_df[col] * fx_df["fx_rate"]

    fx_df["roi_pct_fx"] = (
        fx_df["total_gain_fx"] / fx_df["cost_basis_fx"] * 100
    ).where(fx_df["cost_basis_fx"] > 0, 0.0)

    fx_display_cols = [
        "symbol",
        "asset_type",
        "fund_type",
        "currency",
        "shares",
        "cost_basis_fx",
        "total_value_fx",
        "dividends_fx",
        "roi_pct_fx",
        "total_gain_fx",
    ]

    fx_display_df = fx_df[fx_display_cols].copy()

    fx_display_df = fx_display_df.rename(columns={
        "cost_basis_fx": f"Invested ({base_currency})",
        "total_value_fx": f"Current Value ({base_currency})",
        "dividends_fx": f"Dividends ({base_currency})",
        "roi_pct_fx": f"ROI % ({base_currency})",
        "total_gain_fx": f"Total P/L ({base_currency})",
    })

    fx_invested = fx_df["cost_basis_fx"].sum()
    fx_current_value = fx_df["total_value_fx"].sum()
    fx_dividends = fx_df["dividends_fx"].sum()
    fx_total_pl = fx_df["total_gain_fx"].sum()
    fx_roi_pct = (fx_total_pl / fx_invested * 100) if fx_invested else 0.0



    with st.expander("FX Rates Used"):
        for cur, rate in fx_rates.items():
            st.write(f"{cur} → {base_currency}: {rate}")

    show_fx_table = st.checkbox("Show FX-normalized holdings summary", value=True)

    if show_fx_table:
        pl_col = f"Total P/L ({base_currency})"
        roi_col = f"ROI % ({base_currency})"

        styled_fx = (
            fx_display_df
            .style
            .map(color_pl, subset=[pl_col])
            .map(color_pct, subset=[roi_col])
            .format({
                f"Invested ({base_currency})": "{:,.2f}",
                f"Current Value ({base_currency})": "{:,.2f}",
                f"Dividends ({base_currency})": "{:,.2f}",
                f"Total P/L ({base_currency})": "{:,.2f}",
                roi_col: "{:.2f}%",
            })
        )

        st.dataframe(styled_fx, width="stretch")


        st.subheader(f"📊 Portfolio Totals ({base_currency})")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Invested", f"{fx_invested:,.2f}")
        col2.metric("Current Value", f"{fx_current_value:,.2f}")
        col3.metric("Dividends", f"{fx_dividends:,.2f}")
        col4.metric(
            "Total P/L",
            f"{fx_total_pl:,.2f}",
            delta=f"{fx_total_pl:,.2f} [{fx_roi_pct:,.2f}%]",
            delta_color="normal" if fx_total_pl >= 0 else "inverse",
        )


