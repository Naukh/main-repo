# pages/8_Reports.py

import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from data.db_utils import get_holdings, get_transactions, get_dividends
from utils.calculations import compute_current_shares, calculate_weighted_avg_price, calculate_total_value, calculate_invested_value
from utils.portfolio_summary import build_portfolio_summary

# Helper functions

def render_allocation_chart(df, label_col, value_col, title, chart_type, color_palette, export_dark=False):
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
        fig.update_layout(yaxis=dict(title="Allocation %", range=[0, y_max]), showlegend=False)

    # Apply dark mode template if exporting
    if export_dark:
        fig.update_layout(template="plotly_dark", paper_bgcolor="#1e1e1e", plot_bgcolor="#1e1e1e")

    # Display in Streamlit
    st.plotly_chart(fig, width="stretch")
    return fig

def render_rebalance(df, category_col, value_col, title, total_value_fx, 
                     primary_color="#4F8BF9", chart_type="Bar"):
    """
    df: DataFrame with columns [category_col, value_col]
    category_col: column to group by (e.g., "asset_type", "currency", "fund_type")
    value_col: column with FX-normalized total values
    title: chart/table title
    total_value_fx: total portfolio value (FX-normalized)
    primary_color: main chart color
    chart_type: "Bar" or "Pie"
    """

    categories = df[category_col].unique()
    current_alloc = df.groupby(category_col, as_index=False)[value_col].sum()
    current_alloc["allocation_pct"] = current_alloc[value_col] / total_value_fx * 100

    st.markdown(f"### 🎯 Set Target Allocation: {title}")
    target_alloc = {}
    for cat in categories:
        current_pct = current_alloc.loc[current_alloc[category_col]==cat, "allocation_pct"].values[0]
        target_alloc[cat] = st.number_input(
            f"{cat} target allocation (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(current_pct),
            step=1.0,
            format="%.1f",
            key=f"target_{title}_{cat}"
        )

    # Compute rebalancing
    current_alloc["target_pct"] = current_alloc[category_col].map(target_alloc)
    current_alloc["diff_pct"] = current_alloc["target_pct"] - current_alloc["allocation_pct"]
    current_alloc["diff_value"] = current_alloc["diff_pct"] / 100 * total_value_fx

    def action_label(val):
        if val > 0: return "🟢 Add"
        elif val < 0: return "🔴 Reduce"
        else: return "⚪ None"

    current_alloc["action"] = current_alloc["diff_value"].apply(action_label)
    current_alloc["diff_value"] = current_alloc["diff_value"].abs()

    # Display table
    st.dataframe(
        current_alloc[[category_col, "allocation_pct", "target_pct", "diff_pct", "diff_value", "action"]]
        .style.format({
            "allocation_pct": "{:.2f}%",
            "target_pct": "{:.2f}%",
            "diff_pct": "{:.2f}%",
            "diff_value": "{:,.2f}"
        }),
        width="stretch"
    )

    # Display chart
    if chart_type == "Pie":
        fig = go.Figure(go.Pie(
            labels=current_alloc[category_col],
            values=current_alloc["target_pct"],
            hole=0.4,
            marker_colors=[primary_color]*len(current_alloc)
        ))
        fig.update_layout(title=title, height=450, margin=dict(t=60, b=40, l=20, r=20))
    else:  # Bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=current_alloc[category_col],
            y=current_alloc["allocation_pct"],
            name="Current",
            marker_color=primary_color
        ))
        fig.add_trace(go.Bar(
            x=current_alloc[category_col],
            y=current_alloc["target_pct"],
            name="Target",
            marker_color="#f39c12"
        ))
        fig.update_layout(
            barmode="group",
            title=title,
            yaxis=dict(title="Allocation %", range=[0, max(current_alloc[["allocation_pct","target_pct"]].max())*1.2]),
            height=450,
            margin=dict(t=60, b=40, l=40, r=20)
        )

    st.plotly_chart(fig, width="stretch")


def render_fx_table(fx_dict, label):
    if fx_dict:
        fx_df = pd.DataFrame(list(fx_dict.items()), columns=["Currency", "Rate to Base"])
        html_buffer.write(fx_df.to_html(index=False, float_format="%.6f"))
    else:
        html_buffer.write(f"<p>No FX conversion applied for {label}.</p>")


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
    st.session_state.fx_display_df = fx_display_df
    st.session_state.fx_rates_performance = fx_rates

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
        st.session_state.income_display_df = income_display_df
        st.session_state.fx_rates_income = fx_rates 

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
    st.session_state.alloc_df = alloc_df
    st.session_state.fx_rates_allocation = fx_rates

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

    asset_fig = render_allocation_chart(
        asset_alloc,
        label_col="label",
        value_col="allocation_pct",
        title="Asset Allocation",
        chart_type=asset_chart_type,
        color_palette=color_palette,
        export_dark=True
    )
    st.session_state.asset_chart = asset_fig

    # Rebalancing
    with st.expander("🎯 Target Allocation by Asset Type"):
        asset_chart_type = st.radio(
            "Asset Allocation Chart Type",
            options=["Bar", "Pie"],
            horizontal=True,
            key="chart_type_asset"
        )
        render_rebalance(
            alloc_df, 
            category_col="asset_type", 
            value_col="total_value_fx", 
            title="Asset Type Allocation", 
            total_value_fx=total_value_fx,
            primary_color="#4F8BF9",
            chart_type=asset_chart_type
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

    currency_fig =render_allocation_chart(
        currency_alloc,
        label_col="label",
        value_col="allocation_pct",
        title="Currency Allocation",
        chart_type=currency_chart_type,
        color_palette=color_palette,
        export_dark=True
    )
    st.session_state.currency_chart = currency_fig

    # Rebalancing
    with st.expander("🎯 Target Allocation by Currency"):
        currency_chart_type = st.radio(
            "Currency Allocation Chart Type",
            options=["Bar", "Pie"],
            horizontal=True,
            key="chart_type_currency"
        )
        render_rebalance(
            alloc_df, 
            category_col="currency", 
            value_col="total_value_fx", 
            title="Currency Allocation", 
            total_value_fx=total_value_fx,
            primary_color="#27ae60",
            chart_type=currency_chart_type
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

        fund_fig = render_allocation_chart(
            fund_alloc,
            label_col="label",
            value_col="allocation_pct",
            title="Fund Allocation",
            chart_type=fund_chart_type,
            color_palette=color_palette,
            export_dark=True
        )
        st.session_state.fund_chart = fund_fig

        # Rebalancing
        with st.expander("🎯 Target Allocation by Index funds"):
            fund_chart_type = st.radio(
                "Fund Allocation Chart Type",
                options=["Bar", "Pie"],
                horizontal=True,
                key="chart_type_fund"
            )
            render_rebalance(
                fund_df, 
                category_col="fund_type", 
                value_col="total_value_fx", 
                title="Fund Type Allocation", 
                total_value_fx=total_value_fx,
                primary_color="#e74c3c",
                chart_type=fund_chart_type
            )
    else:
        st.info("No index funds in portfolio.")


# -----------------------------
# Transaction Report (placeholder)
# -----------------------------
with tabs[3]:
    st.subheader("🧾 Transaction Report")

    # --- Load transactions ---
    all_txs = []
    for h in df_holdings.itertuples():
        txs = get_transactions(h.symbol)
        if txs:
            df_tx = pd.DataFrame(txs)
            df_tx["currency"] = h.currency
            df_tx["asset_type"] = h.asset_type
            df_tx["fund_type"] = h.fund_type
            all_txs.append(df_tx)

    if not all_txs:
        st.info("No transactions recorded yet.")
        st.stop()

    tx_df = pd.concat(all_txs, ignore_index=True)
    tx_df["date"] = pd.to_datetime(tx_df["date"])
    tx_df.sort_values("date", inplace=True)

    # --- Filters ---
    symbols = sorted(tx_df["symbol"].unique())
    selected_symbols = st.multiselect("Filter by symbol", options=symbols, default=symbols)

    # --- Date Range ---
    min_date = tx_df["date"].min()
    max_date = pd.Timestamp.today()

    date_options = ["All Dates", "Custom Range"]
    selected_date_option = st.selectbox("Choose a date range", options=date_options, index=0)

    if selected_date_option == "All Dates":
        start_date, end_date = min_date, max_date
    else:
        date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date  # fallback

    # --- FX inputs outside button ---
    st.subheader("🌍 FX Normalization (Optional)")
    base_currency = st.selectbox(
        "Select base currency",
        options=sorted(tx_df["currency"].unique()),
        index=0,
        key="tx_fx_base_currency"
    )

    st.markdown("#### Enter FX rates to convert to base currency")
    fx_rates = {}
    for cur in sorted(tx_df["currency"].unique()):
        fx_rates[cur] = 1.0 if cur == base_currency else st.number_input(
            f"{cur} → {base_currency}",
            min_value=0.000001,
            value=1.0,
            step=0.01,
            format="%.6f",
            key=f"tx_fx_{cur}_to_{base_currency}"
        )

    # --- Apply Filters Button ---
    if st.button("Apply Filters"):
        # Ensure valid date range
        if start_date > end_date:
            st.warning("⚠️ Start date cannot be after end date.")
            st.stop()

        # Filter transactions
        filtered_tx = tx_df[
            (tx_df["symbol"].isin(selected_symbols)) &
            (tx_df["date"] >= pd.to_datetime(start_date)) &
            (tx_df["date"] <= pd.to_datetime(end_date))
        ].copy()

        if filtered_tx.empty:
            st.info("No transactions found for the selected filters.")
            st.stop()

        # --- Apply FX ---
        filtered_tx["fx_rate"] = filtered_tx["currency"].map(fx_rates)
        filtered_tx["price_fx"] = filtered_tx["price"] * filtered_tx["fx_rate"]
        filtered_tx["total_value_fx"] = filtered_tx["shares"] * filtered_tx["price_fx"]

        # --- Display table ---
        display_cols = ["date", "symbol", "asset_type", "fund_type", "shares", "price", "currency", "price_fx", "total_value_fx", "type"]
        filtered_tx_display = filtered_tx[display_cols].copy()
        filtered_tx_display.rename(columns={
            "price": "Price (Original Currency)",
            "price_fx": f"Price ({base_currency})",
            "total_value_fx": f"Total Value ({base_currency})"
        }, inplace=True)
        st.session_state.filtered_tx_display = filtered_tx_display
        st.session_state.fx_rates_transactions = fx_rates

        st.dataframe(
            filtered_tx_display.style.format({
                "Price (Original Currency)": "{:,.2f}",
                f"Price ({base_currency})": "{:,.2f}",
                f"Total Value ({base_currency})": "{:,.2f}"
            }),
            width="stretch"
        )

        # --- Download option ---
        csv = filtered_tx_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered transactions as CSV",
            data=csv,
            file_name=f"transactions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Consolidate report
st.markdown("---")
st.subheader("📥 Download Full Portfolio Report (HTML)")

# --- User chooses HTML theme ---
html_theme = st.radio("Select HTML Report Theme", options=["Dark", "Light"], horizontal=True)

# CSS styles for tables
css_light = """
<style>
body { font-family: Arial, sans-serif; background-color: #fff; color: #000; }
table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
</style>
"""

css_dark = """
<style>
body { font-family: Arial, sans-serif; background-color: #121212; color: #eee; }
table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
th, td { border: 1px solid #444; padding: 8px; text-align: left; }
th { background-color: #1f1f1f; }
tr:nth-child(even) { background-color: #1a1a1a; }
</style>
"""


if st.button("Generate & Download HTML Report"):

    html_buffer = io.StringIO()
    html_buffer.write("<html><head><title>Portfolio Report</title>")

    # Apply chosen theme
    html_buffer.write(css_light if html_theme=="Light" else css_dark)
    html_buffer.write("</head><body>")
    html_buffer.write(f"<h1>Portfolio Report - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>")

    # --- Performance ---
    if 'fx_display_df' in st.session_state and not st.session_state.fx_display_df.empty:
        html_buffer.write("<h2>📈 Performance</h2>")
        html_buffer.write("<h3>FX Conversion Rates Used</h3>")
        render_fx_table(st.session_state.get('fx_rates_performance'), "Performance")
        html_buffer.write(st.session_state.fx_display_df.to_html(index=False, float_format="%.2f"))
    else:
        html_buffer.write("<h2>📈 Performance</h2><p>No performance data available.</p>")

    # --- Income ---
    if 'income_display_df' in st.session_state and not st.session_state.income_display_df.empty:
        html_buffer.write("<h2>💸 Income / Dividends</h2>")
        html_buffer.write("<h3>FX Conversion Rates Used</h3>")
        render_fx_table(st.session_state.get('fx_rates_income'), "Income / Dividends")
        html_buffer.write(st.session_state.income_display_df.to_html(index=False, float_format="%.2f"))
    else:
        html_buffer.write("<h2>💸 Income / Dividends</h2><p>No income data available.</p>")

    # --- Allocation ---
    if 'alloc_df' in st.session_state and not st.session_state.alloc_df.empty:
        html_buffer.write("<h2>📊 Allocation</h2>")
        html_buffer.write("<h3>FX Conversion Rates Used</h3>")
        render_fx_table(st.session_state.get('fx_rates_allocation'), "Allocation")
        html_buffer.write(st.session_state.alloc_df.to_html(index=False, float_format="%.2f"))

        # Plot figures
        for chart_name, chart_fig in [
            ("Asset Allocation", st.session_state.get("asset_chart")),
            ("Currency Allocation", st.session_state.get("currency_chart")),
            ("Fund Allocation", st.session_state.get("fund_chart"))
        ]:
            if chart_fig is not None:
                # Convert to PNG and encode as base64
                img_bytes = pio.to_image(chart_fig, format="png", width=800, height=400)
                import base64
                img_base64 = base64.b64encode(img_bytes).decode()
                html_buffer.write(f"<h3>{chart_name}</h3>")
                html_buffer.write(f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%; height:auto;">')

    else:
        html_buffer.write("<h2>📊 Allocation</h2><p>No allocation data available.</p>")

    # --- Transactions ---
    if 'filtered_tx_display' in st.session_state and not st.session_state.filtered_tx_display.empty:
        html_buffer.write("<h2>🧾 Transactions</h2>")
        html_buffer.write("<h3>FX Conversion Rates Used</h3>")
        render_fx_table(st.session_state.get('fx_rates_transactions'), "Transactions")
        html_buffer.write(st.session_state.filtered_tx_display.to_html(index=False, float_format="%.2f"))
    else:
        html_buffer.write("<h2>🧾 Transactions</h2><p>No transaction data available or filters not applied.</p>")

    html_buffer.write("</body></html>")

    html_data = html_buffer.getvalue().encode("utf-8")

    st.download_button(
        label="Download Full Report (HTML)",
        data=html_data,
        file_name=f"portfolio_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html"
    )
