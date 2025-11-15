import streamlit as st
import pandas as pd
import plotly.express as px
import os
from core.db import fetch_entries
from datetime import datetime

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
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

# ----------------------------
# Section 2 — Income vs Expenses vs Balance
# ----------------------------
st.header("2️⃣ Income vs Expenses vs Balance")
income = df[df["entry_type"] == "income"].groupby("month")["actual"].sum().reset_index()
expense = df[df["entry_type"] == "budget"].groupby("month")["actual"].sum().reset_index()
merged = income.merge(expense, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
merged["balance"] = merged["actual_income"] - merged["actual_expense"]

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

# ----------------------------
# Section 3 — Category Trends (Multiple)
# ----------------------------
st.header("3️⃣ Category Trends Across All Months")
all_categories = sorted(df["category"].dropna().unique())
selected_categories = st.multiselect("Select categories to plot", all_categories, default=all_categories[:3])

category_colors = {}
for cat in selected_categories:
    category_colors[cat] = st.color_picker(f"Color for '{cat}'", px.colors.qualitative.Plotly[all_categories.index(cat) % 10])

category_fig = px.line(template="plotly_dark")
category_fig.update_layout(title="Category Trends Across Months", xaxis_title="Month", yaxis_title="Amount")

# Prepare data for HTML export
category_tables = []
for cat in selected_categories:
    df_cat = df[df["category"] == cat]
    df_cat_group = df_cat.groupby("month")["actual"].sum().reset_index()
    category_fig.add_scatter(x=df_cat_group["month"], y=df_cat_group["actual"], mode="lines+markers", name=cat, line=dict(color=category_colors[cat]))
    category_tables.append((cat, df_cat_group))

st.plotly_chart(category_fig, use_container_width=True)

# ----------------------------
# Table page length selection
# ----------------------------
st.header("Table Display Options")
table_page_length = st.selectbox("Number of rows to show per table", ["10", "25", "50", "All"], index=0)
page_length_js = "0" if table_page_length=="All" else table_page_length

# ----------------------------
# Export HTML Report
# ----------------------------
st.header("📄 Export HTML Report")
if st.button("Generate HTML Report"):

    # Export interactive Plotly figures as HTML
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False)
    category_fig_html = category_fig.to_html(full_html=False, include_plotlyjs=False)

    # Build HTML tables
    table_html = ""
    # Expenses table
    table_html += f"""
    <div class='section'>
        <h2>Expenses per Month</h2>
        {expenses_per_month.to_html(index=False, classes='display')}
    </div>
    """
    # Income vs Expense table
    table_html += f"""
    <div class='section'>
        <h2>Income vs Expense vs Balance</h2>
        {merged.to_html(index=False, classes='display')}
    </div>
    """
    # Category tables
    for cat, df_cat_group in category_tables:
        table_html += f"""
        <div class='section'>
            <h2>Category Trend — {cat}</h2>
            {df_cat_group.to_html(index=False, classes='display')}
        </div>
        """

    html_content = f"""
    <html>
    <head>
        <title>Budget Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.css">
        <script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.js"></script>
        <style>
            body {{
                background-color: #121212;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
                margin: 30px;
            }}
            h1, h2 {{ color: #ffffff; margin-bottom: 10px; }}
            .section {{
                margin-bottom: 40px;
                padding: 20px;
                background: #1e1e1e;
                border-radius: 10px;
                box-shadow: 0 0 10px #00000055;
            }}
            table.dataframe {{
                width: 100%;
                border-collapse: collapse;
            }}
            table.dataframe th {{ background-color: #333; color: #fff; padding: 8px; }}
            table.dataframe td {{ background-color: #222; padding: 8px; color: #ddd; }}
            table.dataframe tr:nth-child(even) td {{ background-color: #2a2a2a; }}
            table.dataframe tr:hover td {{ background-color: #444; }}
            a {{ color: #4da3ff; }}
        </style>
    </head>
    <body>
        <h1>Budget Report</h1>
        <p>Generated on: {datetime.now()}</p>

        <div class="section">
            <h2>Expenses per Month Chart</h2>
            {fig1_html}
        </div>
        <div class="section">
            <h2>Expenses per Month Table</h2>
            {expenses_per_month.to_html(index=False, classes='display')}
        </div>

        <div class="section">
            <h2>Income vs Expense vs Balance Chart</h2>
            {fig2_html}
        </div>
        <div class="section">
            <h2>Income vs Expense vs Balance Table</h2>
            {merged.to_html(index=False, classes='display')}
        </div>

        <div class="section">
            <h2>Category Trends Chart</h2>
            {category_fig_html}
        </div>

        <!-- Category tables -->
        {table_html}

        <script>
            $(document).ready(function() {{
                $('table.display').DataTable({{ paging: true, searching: true, info: false, pageLength: {page_length_js} }});
            }});
        </script>
    </body>
    </html>
    """

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    st.success(f"Report generated → {HTML_PATH}")
    st.download_button("Download Report", data=html_content, file_name="budget_report.html")
