import streamlit as st
import pandas as pd
import plotly.express as px
import os
from core.db import fetch_entries
from datetime import datetime

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go from /pages to project root
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HTML_FILENAME = "budget_report.html"
os.makedirs(REPORTS_DIR, exist_ok=True)
HTML_PATH = os.path.join(REPORTS_DIR, HTML_FILENAME)

st.set_page_config(page_title="Reports", layout="wide")
st.title("📊 Financial Reports & Analytics")

# ----------------------------
# Load Data
# ----------------------------
df = fetch_entries()
if df.empty:
    st.warning("No entries in database to visualize.")
    st.stop()

df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0)
df["budgeted"] = pd.to_numeric(df["budgeted"], errors="coerce").fillna(0)
df["month"] = df["month"].astype(str)

# ----------------------------
# Section 1 — Expenses Per Month
# ----------------------------
st.header("1️⃣ Expenses Across All Months")

expenses = df[df["entry_type"] == "budget"]
expenses_per_month = expenses.groupby("month")["actual"].sum().reset_index()

st.subheader("Pick color for expenses line")
expenses_color = st.color_picker("Expenses line color", "#FF6B6B")

fig1 = px.line(
    expenses_per_month,
    x="month",
    y="actual",
    markers=True,
    title="Total Expenses by Month",
    color_discrete_sequence=[expenses_color]
)
fig1.update_layout(template="plotly_dark")
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ----------------------------
# Section 2 — Income vs Expenses vs Balance
# ----------------------------
st.header("2️⃣ Income vs Expenses vs Balance")

income = df[df["entry_type"] == "income"].groupby("month")["actual"].sum().reset_index()
expense = df[df["entry_type"] == "budget"].groupby("month")["actual"].sum().reset_index()

merged = income.merge(expense, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
merged["balance"] = merged["actual_income"] - merged["actual_expense"]

st.subheader("Pick colors for Income, Expense, Balance lines")
income_color = st.color_picker("Income line color", "#4DA3FF")
expense_color = st.color_picker("Expense line color", "#FF6B6B")
balance_color = st.color_picker("Balance line color", "#FFD93D")

fig2 = px.line(
    merged,
    x="month",
    y=["actual_income", "actual_expense", "balance"],
    markers=True,
    title="Income vs Expense vs Balance",
    color_discrete_sequence=[income_color, expense_color, balance_color]
)
fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ----------------------------
# Section 3 — Per Category Trends
# ----------------------------
st.header("3️⃣ Category Trends Across All Months")

categories = sorted(df["category"].dropna().unique())
category_choice = st.selectbox("Choose a category:", categories)

df_cat = df[df["category"] == category_choice]
df_cat_group = df_cat.groupby("month")["actual"].sum().reset_index()

st.subheader(f"Pick color for {category_choice} category")
cat_color = st.color_picker("Category bar color", "#2018F4")

fig3 = px.bar(
    df_cat_group,
    x="month",
    y="actual",
    title=f"Spending Trend: {category_choice}",
    color_discrete_sequence=[cat_color]
)
fig3.update_layout(template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ----------------------------
# Export HTML Report
# ----------------------------
st.header("📄 Export HTML Report")

if st.button("Generate HTML Report"):

    # ----------------------------
    # Export interactive Plotly figures to HTML snippets
    # ----------------------------
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn')
    fig3_html = fig3.to_html(full_html=False, include_plotlyjs='cdn')

    # Make tables interactive with simple HTML style
    tables = {
        "Expenses per Month": expenses_per_month,
        "Income vs Expense vs Balance": merged,
        f"Category Trend — {category_choice}": df_cat_group
    }

    table_html = ""
    for title, table_df in tables.items():
        table_html += f"<div class='section'><h2>{title}</h2>{table_df.to_html(index=False)}</div>"

    # ----------------------------
    # Build full HTML
    # ----------------------------
    html_content = f"""
    <html>
    <head>
        <title>Budget Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                background-color: #121212;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
                margin: 30px;
            }}
            h1, h2 {{ color: #ffffff; margin-bottom: 10px; }}
            .section {{ margin-bottom: 40px; padding: 20px; background: #1e1e1e; border-radius: 10px; box-shadow: 0 0 10px #00000055; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background-color: #333; color: #fff; padding: 8px; }}
            td {{ background-color: #222; padding: 8px; color: #ddd; }}
            tr:nth-child(even) td {{ background-color: #2a2a2a; }}
            tr:hover td {{ background-color: #444; }}
            a {{ color: #4da3ff; }}
        </style>
    </head>
    <body>
        <h1>Budget Report</h1>
        <p>Generated on: {datetime.now()}</p>

        <div class="section">
            <h2>Interactive Charts</h2>
            {fig1_html}
            {fig2_html}
            {fig3_html}
        </div>

        <h2>Tables</h2>
        {table_html}

    </body>
    </html>
    """

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    st.success(f"Report generated → {HTML_PATH}")
    st.download_button("Download Report", data=html_content, file_name="budget_report.html")
