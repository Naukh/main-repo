import streamlit as st
import pandas as pd
import plotly.express as px
import os
from core.db import fetch_entries
from datetime import datetime

# ----------------------------
# Setup paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # from /pages to root
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
# User options
# ----------------------------

table_entries_options = ["10", "25", "50", "All"]
default_entries = "10"
selected_entries = st.selectbox("Number of table rows in HTML report:", table_entries_options, index=table_entries_options.index(default_entries))
table_rows = None if selected_entries == "All" else int(selected_entries)

# ----------------------------
# Section 1 — Expenses Across All Months
# ----------------------------
st.header("1️⃣ Expenses Across All Months")
expenses = df[df["entry_type"] == "budget"]
expenses_per_month = expenses.groupby("month")["actual"].sum().reset_index()
expense_color = st.color_picker("Select line color for Expenses", "#FF5733")

fig1 = px.line(
    expenses_per_month,
    x="month",
    y="actual",
    markers=True,
    title="Total Expenses by Month",
    line_shape="linear"
)
fig1.update_traces(line=dict(color=expense_color))
fig1.update_layout(template="plotly_dark")
st.plotly_chart(fig1, use_container_width=True)
st.subheader("Expenses Table")
st.dataframe(expenses_per_month.head(table_rows))
st.markdown("---")

# ----------------------------
# Section 2 — Income vs Expenses vs Balance
# ----------------------------
st.header("2️⃣ Income vs Expenses vs Balance")
income = df[df["entry_type"] == "income"].groupby("month")["actual"].sum().reset_index()
expense = expenses_per_month.copy()
merged = income.merge(expense, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
merged["balance"] = merged["actual_income"] - merged["actual_expense"]
line_color_expense = st.color_picker("Select line color for Expenses per Month", "#FF5733")
line_color_income = st.color_picker("Select line color for Income", "#33FF57")
line_color_balance = st.color_picker("Select line color for Balance", "#3380FF")

fig2 = px.line(
    merged,
    x="month",
    y=["actual_income", "actual_expense", "balance"],
    markers=True,
    title="Income vs Expense vs Balance"
)
fig2.update_traces(selector=dict(name="actual_income"), line=dict(color=line_color_income))
fig2.update_traces(selector=dict(name="actual_expense"), line=dict(color=line_color_expense))
fig2.update_traces(selector=dict(name="balance"), line=dict(color=line_color_balance))
fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)
st.subheader("Income / Expenses / Balance Table")
st.dataframe(merged.head(table_rows))
st.markdown("---")

# ----------------------------
# Section 3 — Category Trends
# ----------------------------
st.header("3️⃣ Category Trends Across All Months")
categories = sorted(df["category"].dropna().unique())
category_choice = st.selectbox("Choose a category:", categories)

df_cat = df[df["category"] == category_choice]
df_cat_group = df_cat.groupby("month")["actual"].sum().reset_index()
category_color = st.color_picker("Select line color for Category", "#3380FF")

fig3 = px.bar(
    df_cat_group,
    x="month",
    y="actual",
    title=f"Spending Trend: {category_choice}"
)
fig3.update_traces(marker_color=category_color)
fig3.update_layout(template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)
st.subheader(f"Table for {category_choice}")
st.dataframe(df_cat_group.head(table_rows))
st.markdown("---")

# ----------------------------
# Export HTML Report (interactive)
# ----------------------------
st.header("📄 Export Interactive HTML Report")

if st.button("Generate HTML Report"):
    # Convert Plotly figures to HTML snippets
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False)
    fig3_html = fig3.to_html(full_html=False, include_plotlyjs=False)

    # Build HTML with DataTables for interactive tables
    html_content = f"""
    <html>
    <head>
        <title>Budget Report</title>

        <!-- ---- Dark theme CSS ---- -->
        <style>
            body {{ background-color:#121212; color:#e0e0e0; font-family:Arial, sans-serif; margin:30px; }}
            h1, h2 {{ color:#ffffff; }}
            .section {{ margin-bottom:40px; padding:20px; background:#1e1e1e; border-radius:10px; box-shadow:0 0 10px #00000055; }}
            table {{ width:100%; border-collapse: collapse; }}
            th {{ background-color:#333; color:#fff; padding:8px; }}
            td {{ background-color:#222; padding:8px; color:#ddd; }}
            tr:nth-child(even) td {{ background-color:#2a2a2a; }}
            tr:hover td {{ background-color:#444; }}
            a {{ color:#4da3ff; }}
        </style>

        <!-- ---- Include Plotly JS ---- -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

        <!-- ---- Include DataTables JS & CSS ---- -->
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css"/>
        <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

        <script>
            $(document).ready(function() {{
                $('.datatable').DataTable({{
                    "pageLength": {table_rows if table_rows else '10'},
                    "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
                    "order": []
                }});
            }});
        </script>
    </head>

    <body>
        <h1>Budget Report</h1>
        <p>Generated on: {datetime.now()}</p>

        <div class="section">
            <h2>1️⃣ Expenses per Month</h2>
            {expenses_per_month.head(table_rows).to_html(index=False, classes="datatable")}
            {fig1_html}
        </div>

        <div class="section">
            <h2>2️⃣ Income vs Expenses vs Balance</h2>
            {merged.head(table_rows).to_html(index=False, classes="datatable")}
            {fig2_html}
        </div>

        <div class="section">
            <h2>3️⃣ Category Trend — {category_choice}</h2>
            {df_cat_group.head(table_rows).to_html(index=False, classes="datatable")}
            {fig3_html}
        </div>
    </body>
    </html>
    """


    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    st.success(f"Interactive report generated → {HTML_PATH}")
    st.download_button("Download Interactive Report", data=html_content, file_name="budget_report.html")
