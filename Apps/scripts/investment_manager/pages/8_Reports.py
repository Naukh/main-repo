# pages/8_Reports.py

import streamlit as st
import pandas as pd
import plotly.express as px

from data.db_utils import get_holdings, get_transactions, get_dividends
from utils.calculations import compute_current_shares, calculate_weighted_avg_price, calculate_total_value, calculate_invested_value
from utils.portfolio_summary import build_portfolio_summary

# Helper functions
import plotly.express as px

def render_allocation_chart(
    df,
    label_col,
    value_col,
    title,
    chart_type,
    color_palette
):
    colors = px.colors.qualitative.__dict__.get(color_palette, px.colors.qualitative.Set2)

    if chart_type == "Pie":
        fig = px.pie(
            df,
            names=label_col,
            values=value_col,
            title=title,
            hole=0.4,
            color_discrete_sequence=colors
        )
        fig.update_layout(height=420)

    else:
        y_max = df[value_col].max() * 1.15
        fig = px.bar(
            df,
            x=label_col,
            y=value_col,
            title=title,
            text=df[value_col].round(2).astype(str) + "%",
            color=label_col,
            color_discrete_sequence=colors
        )
        fig.update_layout(
            yaxis=dict(title="Allocation %", range=[0, y_max]),
            height=420,
            showlegend=False
        )

    st.plotly_chart(fig, width="stretch")



summary_df = build_portfolio_summary()

st.set_page_config(page_title="Reports", layout="wide")
st.title("📑 Reports")

tabs = st.tabs([
    "📈 Performance",
    "💸 Income",
    "📊 Allocation",
    "🧾 Transactions",
])

# --- Load holdings ---
holdings = get_holdings()
if not holdings:
    st.info("No holdings found. Add some first!")
    st.stop()

df_holdings = pd.DataFrame(holdings)

# -----------------------------
# Performance Report (placeholder)
# -----------------------------

with tabs[0]:
    st.subheader("📈 Cumulative Portfolio Performance")

    summaries = []
    for idx, row in df_holdings.iterrows():
        symbol = row["symbol"]
        current_price = row.get("current_price", 0.0)
        currency = row.get("currency", "USD")
        asset_type = row.get("asset_type", "stock")
        fund_type = row.get("fund_type", "")

        # Shares & weighted avg price
        cur_shares = compute_current_shares(symbol)
        df_tx = pd.DataFrame(get_transactions(symbol))
        weighted_avg_price = calculate_weighted_avg_price(df_tx.assign(purchase_price=df_tx["price"])) if not df_tx.empty else 0.0
        invested_value = calculate_invested_value(cur_shares, weighted_avg_price)

        # Dividends
        divs = get_dividends(symbol)
        if divs:
            df_div = pd.DataFrame(divs)
            for c in ["num_shares", "amount_per_share", "tax"]:
                df_div[c] = pd.to_numeric(df_div[c], errors="coerce").fillna(0.0)
            total_dividends = (df_div["num_shares"] * df_div["amount_per_share"]).sum() - df_div["tax"].sum()
        else:
            total_dividends = 0.0

        # Include only income-generating assets for dividends
        show_dividends = (asset_type == "stock") or (asset_type == "index_fund" and fund_type == "income")
        dividend_value = total_dividends if show_dividends else 0.0

        # Portfolio values
        total_value = calculate_total_value(cur_shares, current_price)
        unrealized = total_value - invested_value
        total_gain = unrealized + dividend_value
        roi_pct = (total_gain / invested_value * 100) if invested_value else 0.0

        summaries.append({
            "symbol": symbol,
            "asset_type": asset_type,
            "fund_type": fund_type,
            "currency": currency,
            "invested": invested_value,
            "current_value": total_value,
            "dividends": dividend_value,
            "total_gain": total_gain,
            "roi_pct": roi_pct
        })

    perf_df = pd.DataFrame(summaries)

    # --- Show FX-normalized totals ---
    st.subheader("🌍 FX-Normalized Performance (Optional)")

    base_currency = st.selectbox(
        "Select base currency",
        options=sorted(perf_df["currency"].unique().tolist()),
        index=0
    )

    fx_rates = {}
    for cur in perf_df["currency"].unique():
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

    fx_df = perf_df.copy()
    fx_df["fx_rate"] = fx_df["currency"].map(fx_rates)

    for col in ["invested", "current_value", "dividends", "total_gain"]:
        fx_df[f"{col}_fx"] = fx_df[col] * fx_df["fx_rate"]

    # --- Display table with conditional formatting ---
    def color_pl(val):
        if pd.isna(val):
            return ""
        if val > 0:
            return "color: #2ecc71; font-weight: 600;"
        elif val < 0:
            return "color: #e74c3c; font-weight: 600;"
        return ""

    def color_pct(val):
        if pd.isna(val):
            return ""
        if val > 0:
            return "color: #2ecc71;"
        elif val < 0:
            return "color: #e74c3c;"
        return ""

    fx_display_cols = [
        "symbol", "asset_type", "fund_type", "currency",
        "invested_fx", "current_value_fx", "dividends_fx", "total_gain_fx"
    ]
    fx_display_df = fx_df[fx_display_cols].rename(columns={
        "invested_fx": f"Invested ({base_currency})",
        "current_value_fx": f"Current Value ({base_currency})",
        "dividends_fx": f"Dividends ({base_currency})",
        "total_gain_fx": f"Total P/L ({base_currency})"
    })
    fx_display_df[f"ROI% ({base_currency})"] = fx_df["total_gain_fx"] / fx_df["invested_fx"] * 100

    styled_fx = (
        fx_display_df
        .style
        .map(color_pl, subset=[f"Total P/L ({base_currency})"])
        .map(color_pct, subset=[f"ROI% ({base_currency})"])
        .format({f"Invested ({base_currency})": "{:,.2f}",
                 f"Current Value ({base_currency})": "{:,.2f}",
                 f"Dividends ({base_currency})": "{:,.2f}",
                 f"Total P/L ({base_currency})": "{:,.2f}",
                 f"ROI% ({base_currency})": "{:.2f}%"})
    )

    st.dataframe(styled_fx, width="stretch")

    # --- Totals ---
    st.subheader(f"📊 Portfolio Totals ({base_currency})")
    col1, col2, col3, col4 = st.columns(4)
    total_invested = fx_df["invested_fx"].sum()
    total_current = fx_df["current_value_fx"].sum()
    total_div = fx_df["dividends_fx"].sum()
    total_pl = fx_df["total_gain_fx"].sum()
    total_roi = (total_pl / total_invested * 100) if total_invested else 0.0

    col1.metric("Invested", f"{total_invested:,.2f}")
    col2.metric("Current Value", f"{total_current:,.2f}")
    col3.metric("Dividends", f"{total_div:,.2f}")
    col4.metric("Total P/L", f"{total_pl:,.2f}", delta=f"{total_roi:.2f}%")



# -----------------------------
# Income Report (placeholder)
# -----------------------------
with tabs[1]:
    st.subheader("💸 Dividends / Income Received")

    # --- Gather all dividends ---
    all_dividends = []
    for row in df_holdings.itertuples():
        divs = get_dividends(row.symbol)
        if divs:
            df_div = pd.DataFrame(divs)
            for c in ["num_shares", "amount_per_share", "tax"]:
                df_div[c] = pd.to_numeric(df_div[c], errors="coerce").fillna(0.0)
            df_div["total_dividend"] = df_div["num_shares"] * df_div["amount_per_share"] - df_div["tax"]
            df_div["symbol"] = row.symbol
            df_div["currency"] = row.currency
            df_div["asset_type"] = row.asset_type
            df_div["fund_type"] = row.fund_type
            all_dividends.append(df_div)

    if not all_dividends:
        st.info("No dividends recorded yet.")
    else:
        income_df = pd.concat(all_dividends, ignore_index=True)
        income_df["date"] = pd.to_datetime(income_df["date"])
        income_df.sort_values("date", inplace=True)

        st.markdown("### Dividends Received (All Holdings)")

        # --- FX normalization ---
        st.subheader("🌍 FX-Normalized Dividends (Optional)")
        base_currency = st.selectbox(
            "Select base currency",
            options=sorted(income_df["currency"].unique()),
            index=0,
            key="income_fx_base_currency"
        )

        st.markdown("#### Enter FX rates to convert to base currency")
        fx_rates = {}
        for cur in sorted(income_df["currency"].unique()):
            fx_rates[cur] = 1.0 if cur == base_currency else st.number_input(
                f"{cur} → {base_currency}",
                min_value=0.000001,
                value=1.0,
                step=0.01,
                format="%.6f",
                key=f"income_fx_{cur}_to_{base_currency}"
            )

        # Compute FX-normalized dividends
        income_df["fx_rate"] = income_df["currency"].map(fx_rates)
        income_df["total_dividend_fx"] = income_df["total_dividend"] * income_df["fx_rate"]

        # --- Display table ---
        def color_income(val):
            if val > 0:
                return "color: #2ecc71; font-weight: 600;"
            return ""

        display_cols = [
            "date", "symbol", "asset_type", "fund_type", "currency",
            "total_dividend", "total_dividend_fx"
        ]
        income_display_df = income_df[display_cols].copy()
        income_display_df.rename(columns={
            "total_dividend": "Dividend (Original Currency)",
            "total_dividend_fx": f"Dividend ({base_currency})"
        }, inplace=True)

        styled_income = (
            income_display_df
            .style
            .map(color_income, subset=["Dividend (Original Currency)", f"Dividend ({base_currency})"])
            .format({
                "Dividend (Original Currency)": "{:,.2f}",
                f"Dividend ({base_currency})": "{:,.2f}"
            })
        )

        st.dataframe(styled_income, width="stretch")

        # --- Totals ---
        st.subheader(f"📊 Total Dividends")
        # Original currency totals grouped by currency
        orig_totals = income_df.groupby("currency")["total_dividend"].sum()
        for cur, total in orig_totals.items():
            st.metric(f"Total Dividends ({cur})", f"{total:,.2f}")

        # FX-normalized total
        total_div_fx = income_df["total_dividend_fx"].sum()
        st.metric(f"Total Dividends ({base_currency})", f"{total_div_fx:,.2f}")



# -----------------------------
# Allocation Report (placeholder)
# -----------------------------
with tabs[2]:
    st.subheader("📊 Portfolio Allocation")

    st.markdown("### 🎨 Visualization Settings")

    color_palette = st.selectbox(
        "Color palette",
        options=[
            "Set2",
            "Pastel",
            "Bold",
            "Dark2",
            "Safe",
            "Vivid"
        ],
        index=0
    )



    # --- Safety checks ---
    if summary_df is None or summary_df.empty:
        st.info("No portfolio data available.")
        st.stop()

    required_cols = {"currency", "asset_type", "total_value"}
    if not required_cols.issubset(summary_df.columns):
        st.error("Portfolio summary is missing required columns.")
        st.stop()

    # =========================
    # 🌍 FX Normalization
    # =========================
    st.markdown("### 🌍 FX Normalization")

    currencies = sorted(summary_df["currency"].dropna().unique().tolist())

    base_currency = st.selectbox(
        "Select base currency",
        options=currencies,
        key="alloc_base_currency"
    )

    st.markdown("#### Enter FX rates to base currency")

    fx_rates = {}
    for cur in currencies:
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
                key=f"alloc_fx_{cur}_to_{base_currency}"
            )

    # Apply FX conversion
    alloc_df = summary_df.copy()
    alloc_df["fx_rate"] = alloc_df["currency"].map(fx_rates).fillna(1.0)
    alloc_df["total_value_fx"] = alloc_df["total_value"] * alloc_df["fx_rate"]

    total_value_fx = alloc_df["total_value_fx"].sum()
    if total_value_fx == 0:
        st.info("Total FX-normalized portfolio value is zero.")
        st.stop()

    # =========================
    # Allocation by Asset Type
    # =========================
    st.markdown("### Allocation by Asset Type")

    asset_chart_type = st.radio(
        "Chart type (Asset Allocation)",
        ["Bar", "Pie"],
        horizontal=True,
        key="asset_alloc_chart"
    )

    asset_alloc = (
        alloc_df
        .groupby("asset_type", as_index=False)
        .agg(total_value=("total_value_fx", "sum"))
    )

    asset_alloc["allocation_pct"] = asset_alloc["total_value"] / total_value_fx * 100
    asset_alloc["label"] = asset_alloc["asset_type"]

    st.dataframe(
        asset_alloc.style.format({
            "total_value": "{:,.2f}",
            "allocation_pct": "{:.2f}%"
        }),
        width="stretch"
    )

    render_allocation_chart(
        asset_alloc,
        label_col="label",
        value_col="allocation_pct",
        title="Asset Allocation",
        chart_type=asset_chart_type,
        color_palette=color_palette
    )

    # =========================
    # Allocation by Currency
    # =========================
    st.markdown("### Allocation by Currency")

    currency_chart_type = st.radio(
        "Chart type (Currency Allocation)",
        ["Bar", "Pie"],
        horizontal=True,
        key="currency_alloc_chart"
    )

    currency_alloc = (
        alloc_df
        .groupby("currency", as_index=False)
        .agg(total_value=("total_value_fx", "sum"))
    )

    currency_alloc["allocation_pct"] = currency_alloc["total_value"] / total_value_fx * 100
    currency_alloc["label"] = currency_alloc["currency"]

    st.dataframe(
        currency_alloc.style.format({
            "total_value": "{:,.2f}",
            "allocation_pct": "{:.2f}%"
        }),
        width="stretch"
    )

    render_allocation_chart(
        currency_alloc,
        label_col="label",
        value_col="allocation_pct",
        title="Currency Allocation",
        chart_type=currency_chart_type,
        color_palette=color_palette
    )



    # =========================
    # Allocation by Fund Type
    # =========================
    fund_df = alloc_df[alloc_df["asset_type"] == "index_fund"]

    if not fund_df.empty:
        st.markdown("### Allocation by Fund Type")

        fund_chart_type = st.radio(
            "Chart type (Fund Allocation)",
            ["Bar", "Pie"],
            horizontal=True,
            key="fund_alloc_chart"
        )

        fund_alloc = (
            fund_df
            .groupby("fund_type", as_index=False)
            .agg(total_value=("total_value_fx", "sum"))
        )

        fund_alloc["allocation_pct"] = fund_alloc["total_value"] / total_value_fx * 100
        fund_alloc["label"] = fund_alloc["fund_type"]

        st.dataframe(
            fund_alloc.style.format({
                "total_value": "{:,.2f}",
                "allocation_pct": "{:.2f}%"
            }),
            width="stretch"
        )

        render_allocation_chart(
            fund_alloc,
            label_col="label",
            value_col="allocation_pct",
            title="Fund Allocation",
            chart_type=fund_chart_type,
            color_palette=color_palette
        )
    else:
        st.info("No index funds in portfolio.")


# -----------------------------
# Transaction Report (placeholder)
# -----------------------------
with tabs[3]:
    st.subheader("🧾 Transaction Report")
    st.info("Filtered transaction history and exports will appear here.")
