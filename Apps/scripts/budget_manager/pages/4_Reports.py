import streamlit as st
import pandas as pd
import plotly.express as px
import os
from core.db import fetch_entries   # use your DB file
from datetime import datetime

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

fig1 = px.line(
    expenses_per_month,
    x="month",
    y="actual",
    markers=True,
    title="Total Expenses by Month",
)
st.plotly_chart(fig1, width="stretch")

st.markdown("---")

# ----------------------------
# Section 2 — Income vs Expenses vs Balance
# ----------------------------
st.header("2️⃣ Income vs Expenses vs Balance")

income = df[df["entry_type"] == "income"].groupby("month")["actual"].sum().reset_index()
expense = df[df["entry_type"] == "budget"].groupby("month")["actual"].sum().reset_index()

merged = income.merge(expense, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
merged["balance"] = merged["actual_income"] - merged["actual_expense"]

fig2 = px.line(
    merged,
    x="month",
    y=["actual_income", "actual_expense", "balance"],
    markers=True,
    title="Income vs Expense vs Balance",
)
st.plotly_chart(fig2, width="stretch")

st.markdown("---")

# ----------------------------
# Section 3 — Per Category Trends
# ----------------------------
st.header("3️⃣ Category Trends Across All Months")

categories = sorted(df["category"].dropna().unique())
category_choice = st.selectbox("Choose a category:", categories)

df_cat = df[df["category"] == category_choice]
df_cat_group = df_cat.groupby("month")["actual"].sum().reset_index()

fig3 = px.bar(
    df_cat_group,
    x="month",
    y="actual",
    title=f"Spending Trend: {category_choice}",
)
st.plotly_chart(fig3, width="stretch")

st.markdown("---")

# ----------------------------
# Export HTML Report
# ----------------------------
st.header("📄 Export HTML Report")

if st.button("Generate HTML Report"):

    # Build HTML
    html_content = f"""
    <html>
    <head>
        <title>Budget Report</title>
        <style>
            /* ---- DARK THEME ---- */
            body {{
                background-color: #121212;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
                margin: 30px;
            }}

            h1, h2 {{
                color: #ffffff;
                margin-bottom: 10px;
            }}

            .section {{
                margin-bottom: 40px;
                padding: 20px;
                background: #1e1e1e;
                border-radius: 10px;
                box-shadow: 0 0 10px #00000055;
            }}

            /* ---- TABLE DARK MODE ---- */
            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background-color: #333;
                color: #fff;
                padding: 8px;
            }}

            td {{
                background-color: #222;
                padding: 8px;
                color: #ddd;
            }}

            tr:nth-child(even) td {{
                background-color: #2a2a2a;
            }}

            tr:hover td {{
                background-color: #444;
            }}

            /* ---- LINKS ---- */
            a {{
                color: #4da3ff;
            }}
        </style>
    </head>

    <body>
        <h1>Budget Report</h1>
        <p>Generated on: {datetime.now()}</p>

        <div class="section">
            <h2>Expenses per Month</h2>
            {expenses_per_month.to_html(index=False)}
        </div>

        <div class="section">
            <h2>Income vs Expense vs Balance</h2>
            {merged.to_html(index=False)}
        </div>

        <div class="section">
            <h2>Category Trend — {category_choice}</h2>
            {df_cat_group.to_html(index=False)}
        </div>

    </body>
    </html>
    """

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    st.success(f"Report generated → {HTML_PATH}")
    st.download_button("Download Report", data=html_content, file_name="budget_report.html")
