#!/usr/bin/env python3
"""
Summarize budgets and expenses across months.
Usage:
  python summarize.py -d ../data -o ../outputs
"""

import os
import glob
import logging
import base64
from io import BytesIO
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import chardet

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


# ------------------------- Utility Functions -------------------------
def detect_encoding(file_path):
    """Detect file encoding using chardet."""
    with open(file_path, "rb") as f:
        raw = f.read()
    return chardet.detect(raw)["encoding"]


def safe_save(save_func, path, *args, retries=3, delay=2, **kwargs):
    """Attempt to save file, retry if PermissionError occurs."""
    import time
    for attempt in range(retries):
        try:
            save_func(path, *args, **kwargs)
            logging.info("Saved %s", path)
            return
        except PermissionError:
            logging.warning("File %s open? Attempt %d/%d. Retrying in %ds...", path, attempt+1, retries, delay)
            time.sleep(delay)
    logging.error("Failed to save %s after %d attempts", path, retries)


def fig_to_base64(fig):
    """Convert Matplotlib figure to base64-encoded PNG string."""
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def create_line_chart(x, y, title, xlabel="Month", ylabel="Amount [SEK]"):
    """Reusable function to create dynamic line chart and return base64 string."""
    num_points = len(x)
    width = max(6, num_points * 0.8)
    height = max(3, max(y) * 5 / 150000 if len(y) else 3)
    fig, ax = plt.subplots(figsize=(width, height))
    ax.plot(x, y, marker='o', linestyle='-')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=90)
    plt.tight_layout()
    b64 = fig_to_base64(fig)
    plt.close(fig)
    return b64


# ------------------------- Data Handling -------------------------
def read_all_months(data_dir):
    """Read all CSVs from data_dir into a single DataFrame."""
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not files:
        logging.warning("No month CSV files found in %s", data_dir)
        return pd.DataFrame(columns=[
            "EntryType","Date","Category","Subcategory","Description",
            "Budgeted","Actual","Income","Account","Notes","month"
        ])

    dfs = []
    for f in files:
        month = os.path.splitext(os.path.basename(f))[0]
        try:
            df = pd.read_csv(f, encoding=detect_encoding(f))
        except Exception as e:
            logging.error("Failed to read %s: %s", f, e)
            continue
        df['month'] = month
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def clean_and_aggregate(df):
    """Clean and aggregate budget and income data."""
    df['Budgeted'] = pd.to_numeric(df.get('Budgeted', 0), errors='coerce').fillna(0.0)
    df['Actual'] = pd.to_numeric(df.get('Actual', 0), errors='coerce').fillna(0.0)
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')

    df_budget = df[df['EntryType'] == 'budget']
    df_income = df[df['EntryType'] == 'income']

    grouped = df_budget.groupby(['month','Category']).agg(
        Budgeted_total=('Budgeted','sum'),
        Actual_total=('Actual','sum'),
        Count_entries=('Description','count')
    ).reset_index()

    income = df_income.groupby('month').agg(
        Income_total=('Actual','sum')
    ).reset_index()

    grouped['month'] = grouped['month'].dt.strftime('%Y-%m')
    income['month'] = income['month'].dt.strftime('%Y-%m')

    return grouped, income


# ------------------------- Output Generation -------------------------
def write_outputs(grouped, income, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Save raw CSV
    safe_save(grouped.to_csv, os.path.join(output_dir, "summary_by_category.csv"), index=False)

    # Monthly totals & balance
    month_totals = grouped.groupby('month').sum()[['Budgeted_total','Actual_total']].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals['Balance'] = month_totals['Income_total'] - month_totals['Actual_total']

    months = month_totals['month']
    budgeted = month_totals['Budgeted_total']
    actual = month_totals['Actual_total']
    income_total = month_totals['Income_total']
    balance = month_totals['Balance']

    # Main charts
    line_b64 = create_line_chart(months, budgeted, "Expenses (Budgeted) vs Month")
    bar_b64 = create_line_chart(months, actual, "Expenses (Actual) vs Month")
    waterfall_b64 = create_line_chart(months, balance, "Balance by Month")

    # ---------------- Category sections ----------------
    cat_totals = grouped.groupby("Category")["Actual_total"].sum().sort_values(ascending=False)
    sorted_categories = cat_totals.index.tolist()
    category_sections = []

    for cat in sorted_categories:
        cat_df = grouped[grouped["Category"] == cat][["month", "Actual_total"]].sort_values("month")
        # Pivot into single row for table
        cat_pivot = cat_df.pivot_table(index=None, columns="month", values="Actual_total", aggfunc="sum").fillna(0)
        cat_pivot.columns.name = None
        cat_pivot.insert(0, "Measure", ["Actual cost"])
        # Chart
        cat_b64 = create_line_chart(cat_df["month"], cat_df["Actual_total"], f"{cat} - Actuals by Month")
        category_sections.append(f"<h2>{cat}</h2>\n{cat_pivot.to_html(index=False)}\n<img src='data:image/png;base64,{cat_b64}' />")

    category_summary_html = "\n".join(category_sections)

    # ---------------- Build HTML ----------------
    html_path = os.path.join(output_dir, "summary_report.html")
    html_blocks = [
        "<html><head><title>Budget Summary Report</title><style>",
        "body { font-family: Arial, sans-serif; margin: 40px; }",
        "h1,h2 { color: #2C3E50; }",
        "table { border-collapse: collapse; margin: 20px 0; }",
        "table, th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }",
        "th { background-color: #f4f4f4; text-align: center; }",
        "td:first-child { text-align: left; font-weight: bold; }",
        "img { max-width: 100%; height: auto; margin: 20px 0; }",
        "</style></head><body>",
        "<h1>Budget Summary Report</h1>",
        "<h2>Income & Totals</h2>",
        month_totals.to_html(index=False),
        "<h2>Charts</h2>",
        f"<h3>Budget</h3><img src='data:image/png;base64,{line_b64}' />",
        f"<h3>Expenses</h3><img src='data:image/png;base64,{bar_b64}' />",
        f"<h3>Balance</h3><img src='data:image/png;base64,{waterfall_b64}' />",
        "<h1>Category Summary (Actuals by Month)</h1>",
        category_summary_html,
        "</body></html>"
    ]
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_blocks))
    logging.info("Saved rich HTML report to %s", html_path)


# ------------------------- Main -------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data-dir", default="../data", help="Directory with input CSV files")
    parser.add_argument("-o", "--output-dir", default="../outputs", help="Directory to save outputs")
    args = parser.parse_args()

    df = read_all_months(args.data_dir)
    if df.empty:
        logging.warning("Nothing to summarize.")
        return

    grouped, income = clean_and_aggregate(df)
    write_outputs(grouped, income, args.output_dir)


if __name__ == "__main__":
    main()
