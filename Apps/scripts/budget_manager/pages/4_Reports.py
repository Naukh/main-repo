import streamlit as st
import pandas as pd
import plotly.express as px
import os
from core.db import fetch_entries
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HTML_FILENAME = "budget_report.html"
os.makedirs(REPORTS_DIR, exist_ok=True)
HTML_PATH = os.path.join(REPORTS_DIR, HTML_FILENAME)

st.set_page_config(page_title="Reports", layout="wide")
st.title("📊 Financial Reports & Analytics")

# Load Data
df = fetch_entries()
if df.empty:
    st.warning("No entries in database to visualize.")
    st.stop()

df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0)
df["budgeted"] = pd.to_numeric(df["budgeted"], errors="coerce").fillna(0)
df["month"] = df["month"].astype(str)

# ----------------------------
# Charts
# ----------------------------
# Expenses per month
expenses = df[df["entry_type"] == "budget"]
expenses_per_month = expenses.groupby("month")["actual"].sum().reset_index()
fig1 = px.line(expenses_per_month, x="month", y="actual", markers=True, title="Total Expenses by Month")
fig1.update_layout(template="plotly_dark")
st.plotly_chart(fig1, use_container_width=True)

# Income vs expense vs balance
income = df[df["entry_type"] == "income"].groupby("month")["actual"].sum().reset_index()
expense = df[df["entry_type"] == "budget"].groupby("month")["actual"].sum().reset_index()
merged = income.merge(expense, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
merged["balance"] = merged["actual_income"] - merged["actual_expense"]
fig2 = px.line(merged, x="month", y=["actual_income", "actual_expense", "balance"], markers=True, title="Income vs Expense vs Balance")
fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)

# Category trend
categories = sorted(df["category"].dropna().unique())
category_choice = st.selectbox("Choose a category:", categories)
df_cat_group = df[df["category"] == category_choice].groupby("month")["actual"].sum().reset_index()
fig3 = px.bar(df_cat_group, x="month", y="actual", title=f"Spending Trend: {category_choice}")
fig3.update_layout(template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)

# ----------------------------
# Export HTML Report
# ----------------------------
st.header("📄 Export HTML Report")
if st.button("Generate HTML Report"):
    # Embed interactive tables using DataTables JS
    table_js_header = """
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.css">
    <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        $(document).ready(function() {
            $('table').DataTable();
        });
    </script>
    """

    html_content = f"""
    <html>
    <head>
        <title>Budget Report</title>
        {table_js_header}
        <style>
            body {{ background-color: #121212; color: #e0e0e0; font-family: Arial, sans-serif; margin: 30px; }}
            h1, h2 {{ color: #ffffff; }}
            .section {{ margin-bottom: 40px; padding: 20px; background: #1e1e1e; border-radius: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background-color: #333; color: #fff; padding: 8px; }}
            td {{ background-color: #222; padding: 8px; color: #ddd; }}
            tr:nth-child(even) td {{ background-color: #2a2a2a; }}
            tr:hover td {{ background-color: #444; }}
        </style>
    </head>
    <body>
        <h1>Budget Report</h1>
        <p>Generated on: {datetime.now()}</p>

        <div class="section">
            <h2>1️⃣ Expenses per Month</h2>
            {expenses_per_month.to_html(index=False)}
            {fig1.to_html(include_plotlyjs='cdn', full_html=False)}
        </div>

        <div class="section">
            <h2>2️⃣ Income vs Expense vs Balance</h2>
            {merged.to_html(index=False)}
            {fig2.to_html(include_plotlyjs='cdn', full_html=False)}
        </div>

        <div class="section">
            <h2>3️⃣ Category Trend — {category_choice}</h2>
            {df_cat_group.to_html(index=False)}
            {fig3.to_html(include_plotlyjs='cdn', full_html=False)}
        </div>
    </body>
    </html>
    """

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    st.success(f"Report generated → {HTML_PATH}")
    st.download_button("Download Report", data=html_content, file_name="budget_report.html")
