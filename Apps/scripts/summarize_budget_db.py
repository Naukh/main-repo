#!/usr/bin/env python3
"""
Summarize budgets and expenses across months from SQLite DB.
Usage:
  python summarize_db.py -db ../data/budget.db -o ../outputs
"""

import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.express as px
import logging
import base64
from io import BytesIO

from util.util import (
    dark_style,
    get_datatables_dependencies,
    get_datatables_init_script,
    add_tfoot_to_html_table
)

OUTPUT_FILENAME = "summary_monthly_budget_db"
MOVING_AVERAGE_MONTHS = 12
LINE_COLOR = "#64b5f6"

# ----------------- Utility -----------------

def safe_save(save_func, path, *args, **kwargs):
    try:
        save_func(path, *args, **kwargs)
        logging.info("Saved file to %s", path)
    except PermissionError:
        logging.error("Permission denied when saving %s. Is the file open?", path)
        input("Close the file and press Enter to retry...")
        save_func(path, *args, **kwargs)
        logging.info("Saved file to %s", path)

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ----------------- DB Read & Aggregation -----------------

def read_db(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM entries", conn)
    conn.close()
    return df

def clean_and_aggregate(df):
    df["budgeted"] = pd.to_numeric(df.get("budgeted", 0), errors="coerce").fillna(0.0)
    df["actual"] = pd.to_numeric(df.get("actual", 0), errors="coerce").fillna(0.0)

    df["month_dt"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df_budget = df[df["entry_type"] == "budget"]
    df_income = df[df["entry_type"] == "income"]

    grouped = df_budget.groupby(["month", "category"]).agg(Actual_total=("actual", "sum")).reset_index()
    income = df_income.groupby("month").agg(Income_total=("actual", "sum")).reset_index()

    grouped["month"] = pd.to_datetime(grouped["month"])
    income["month"] = pd.to_datetime(income["month"])
    grouped["month"] = grouped["month"].dt.strftime("%Y-%m")
    income["month"] = income["month"].dt.strftime("%Y-%m")

    return grouped, income

def prepare_month_totals(grouped, income):
    month_totals = grouped.groupby("month").sum()[["Actual_total"]].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals["Balance"] = month_totals["Income_total"] - month_totals["Actual_total"]
    return month_totals

# ----------------- Plotting -----------------

def generate_summary_charts(month_totals):
    months = month_totals["month"]
    actual = month_totals["Actual_total"]
    income_total = month_totals["Income_total"]
    balance = month_totals["Balance"]

    plt.style.use("dark_background")
    fig_face, ax_face, grid_color = "#121212", "#1a1a1a", "#555"

    fig_width = max(8, len(months) * 0.8)
    max_val = max(actual.max(), income_total.max(), balance.abs().max())
    scale_factor = 5 / 150000
    fig_height = max(4, max_val * scale_factor)

    charts = {}

    # Line Chart
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    ax.plot(months, actual, marker="o", label="Expenses (Actual)", color="#e57373")
    ax.plot(months, income_total, marker="o", label="Income", color="#81c784")
    ax.plot(months, balance, marker="o", linestyle="--", label="Balance", color=LINE_COLOR)
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Amount [SEK]", color="white")
    ax.set_title("Line Graph: Monthly Summary", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    ax.legend()
    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["line"] = fig_to_base64(fig)
    plt.close(fig)

    # Stacked Bar Chart
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    ax.bar(months, actual, label="Actual Expenses", color="#ef5350")
    ax.bar(months, income_total - actual, bottom=actual, label="Remaining Income", color="#66bb6a")
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Amount [SEK]", color="white")
    ax.set_title("Stacked Bar Chart: Income vs Expenses", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    ax.legend()
    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["bar"] = fig_to_base64(fig)
    plt.close(fig)

    # Waterfall Chart
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    colors = ["#66bb6a" if x >= 0 else "#ef5350" for x in balance]
    ax.bar(months, balance, color=colors)
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Balance [SEK]", color="white")
    ax.set_title("Waterfall: Monthly Surplus/Deficit", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["waterfall"] = fig_to_base64(fig)
    plt.close(fig)

    return charts

# ----------------- Category Sections -----------------

def generate_category_sections(grouped):
    cat_totals = grouped.groupby("category")["Actual_total"].sum().sort_values(ascending=False)
    sorted_categories = cat_totals.index.tolist()
    sections = []

    for cat in sorted_categories:
        cat_df = grouped[grouped["category"] == cat].copy()
        cat_df = cat_df.sort_values("month")
        cat_df["month_dt"] = pd.to_datetime(cat_df["month"])
        cat_df["MA"] = cat_df["Actual_total"].rolling(MOVING_AVERAGE_MONTHS, min_periods=1).mean()

        total = cat_df["Actual_total"].sum()
        latest_val = cat_df["Actual_total"].iloc[-1]
        latest_ma = cat_df["MA"].iloc[-1]

        if latest_val > latest_ma:
            trend = "▲"
            trend_color = "green"
        elif latest_val < latest_ma:
            trend = "▼"
            trend_color = "red"
        else:
            trend = "→"
            trend_color = "gray"

        pct_diff = (latest_val - latest_ma) / latest_ma * 100 if latest_ma != 0 else 0
        trend_text = f"<span style='color:{trend_color}'>{trend}</span> ({pct_diff:+.1f}%)"

        cat_pivot = cat_df.pivot_table(index=None, columns="month", values="Actual_total", aggfunc="sum").fillna(0)
        cat_pivot.columns = [str(c) for c in cat_pivot.columns]
        cat_table = cat_pivot.to_html(index=False, border=0, justify='center')

        fig = px.line(
            cat_df,
            x="month_dt",
            y="Actual_total",
            title=f"{cat} - Actuals by Month",
            markers=True,
            labels={"month_dt": "Month", "Actual_total": "Amount (SEK)"}
        )
        fig.update_traces(line=dict(color=LINE_COLOR))
        fig.update_layout(
            paper_bgcolor="#121212",
            plot_bgcolor="#121212",
            font_color="white",
            margin=dict(l=20, r=20, t=40, b=20),
            height=350,
            yaxis=dict(range=[0, cat_df["Actual_total"].max() * 1.05])
        )
        fig_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

        sections.append(f"""
        <details style='margin:15px 0;'>
            <summary style='cursor:pointer; font-size:1.1em; font-weight:bold;'>
                {cat} — TOTAL {total:,.0f} SEK — {MOVING_AVERAGE_MONTHS} Months Avg: {latest_ma:,.0f} SEK {trend_text}
            </summary>
            <div style='margin-top:10px; padding-left:10px;'>
                {cat_table}
                {fig_html}
            </div>
        </details>
        """)

    return "\n".join(sections)

# ----------------- HTML Report -----------------

def write_html_report(output_dir, month_totals, charts, category_summary_html):
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, f"{OUTPUT_FILENAME}.html")
    month_table = add_tfoot_to_html_table(month_totals.to_html(index=False, border=0, justify='center', classes="dt-summary-table"))

    html = f"""
    <html>
    <head>
        <title>Budget Summary Report</title>
        {get_datatables_dependencies()}
        <style>
            body {{ background-color:#121212;color:#fff;font-family:Arial;margin:40px; }}
            table {{ border-collapse:collapse; width:100%; margin:20px 0; }}
            table,th,td {{ border:1px solid #444; padding:8px; text-align:right; }}
            th {{ background:#1f1f1f; text-align:center; }}
            tr:nth-child(even){{background:#1a1a1a;}}
            tr:nth-child(odd){{background:#222;}}
            td:first-child {{ text-align:left; font-weight:bold; }}
            summary {{ cursor: pointer; padding: 6px; background-color:#1f1f1f; border-radius: 4px; }}
            details {{ margin-bottom: 14px; padding: 4px; }}
        </style>
    </head>
    <body>
        <h1>Budget Summary Report</h1>
        <h2>Income & Totals</h2>
        {month_table}
        <h2>Static Summary Charts</h2>
        <h3>Line Graph</h3><img src="data:image/png;base64,{charts['line']}">
        <h3>Stacked Bar Chart</h3><img src="data:image/png;base64,{charts['bar']}">
        <h3>Waterfall Chart</h3><img src="data:image/png;base64,{charts['waterfall']}">
        <h1>Category Summary (Actuals by Month)</h1>
        {category_summary_html}
        {get_datatables_init_script('.dt-summary-table')}
    </body>
    </html>
    """
    safe_save(lambda p: open(p, "w", encoding="utf-8").write(html), html_path)
    print(f"Saved HTML report: {html_path}")

# ----------------- Orchestrator -----------------

def write_outputs(grouped, income, output_dir):
    csv_path = os.path.join(output_dir, f"{OUTPUT_FILENAME}.csv")
    safe_save(grouped.to_csv, csv_path, index=False)
    month_totals = prepare_month_totals(grouped, income)
    charts = generate_summary_charts(month_totals)
    category_html = generate_category_sections(grouped)
    write_html_report(output_dir, month_totals, charts, category_html)

# ----------------- Main -----------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-db", "--db-path", default="../data/budget.db", help="SQLite DB path")
    parser.add_argument("-o", "--output-dir", default="../outputs", help="Directory to save outputs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    else:
        logging.disable(logging.CRITICAL)

    df = read_db(args.db_path)
    if df.empty:
        print("No data found in DB. Exiting.")
        return

    grouped, income = clean_and_aggregate(df)
    write_outputs(grouped, income, args.output_dir)

if __name__ == "__main__":
    main()
