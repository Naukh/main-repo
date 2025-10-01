#!/usr/bin/env python3
"""
Summarize budgets and expenses across months.
Usage:
  python summarize.py -d ../data -o ../outputs
"""

import os
import glob
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import logging
import chardet
import base64
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def detect_encoding(file_path):
    """Detect file encoding using chardet."""
    with open(file_path, "rb") as f:
        raw = f.read()
    result = chardet.detect(raw)
    return result["encoding"]


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
            encoding = detect_encoding(f)
            df = pd.read_csv(f, encoding=encoding)
        except Exception as e:
            logging.error("Failed to read %s: %s", f, e)
            continue
        df['month'] = month
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def clean_and_aggregate(df):
    df['Budgeted'] = pd.to_numeric(df.get('Budgeted', 0), errors='coerce').fillna(0.0)
    df['Actual'] = pd.to_numeric(df.get('Actual', 0), errors='coerce').fillna(0.0)
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')

    df_budget = df[df['EntryType'] == 'budget']
    df_income = df[df['EntryType'] == 'income']

    grouped = df_budget.groupby(['month','Category']).agg(
        Actual_total=('Actual','sum')
    ).reset_index()

    income = df_income.groupby('month').agg(
        Income_total=('Actual','sum')
    ).reset_index()

    grouped['month'] = grouped['month'].dt.strftime('%Y-%m')
    income['month'] = income['month'].dt.strftime('%Y-%m')

    return grouped, income


def safe_save(save_func, path, *args, **kwargs):
    """Attempt to save a file, retry if PermissionError occurs."""
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
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def write_outputs(grouped, income, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Save CSV raw data
    csv_path = os.path.join(output_dir, "summary_by_category.csv")
    safe_save(grouped.to_csv, csv_path, index=False)

    # Month totals with balance
    month_totals = grouped.groupby('month').sum()[['Actual_total']].reset_index()
    month_totals = month_totals.merge(income, on='month', how='left').fillna(0)
    month_totals['Balance'] = month_totals['Income_total'] - month_totals['Actual_total']

    months = month_totals['month']
    actual = month_totals['Actual_total']
    income_total = month_totals['Income_total']
    balance = month_totals['Balance']

    # ---- Main Charts ----
    fig_width = max(8, len(months)*0.8)
    max_val = max(actual.max(), income_total.max(), balance.abs().max())
    scale_factor = 5 / 150000
    fig_height = max(4, max_val * scale_factor)

    # Line chart
    fig1 = plt.figure(figsize=(fig_width, fig_height))
    plt.plot(months, actual, marker='o', label="Expenses (Actual)")
    plt.plot(months, income_total, marker='o', label="Income")
    plt.plot(months, balance, marker='o', linestyle="--", label="Balance")
    plt.xlabel("Month"); plt.ylabel("Amount [SEK]")
    plt.title("Line Graph: Monthly Summary")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(); plt.xticks(rotation=90); plt.tight_layout()
    line_b64 = fig_to_base64(fig1); plt.close(fig1)

    # Stacked bar
    fig2 = plt.figure(figsize=(fig_width, fig_height))
    plt.bar(months, actual, label='Actual Expenses', color='salmon')
    plt.bar(months, income_total-actual, bottom=actual, label='Remaining Income', color='lightgreen')
    plt.xlabel("Month"); plt.ylabel("Amount [SEK]"); plt.title("Stacked Bar Chart: Income vs Expenses")
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend(); plt.xticks(rotation=90); plt.tight_layout()
    bar_b64 = fig_to_base64(fig2); plt.close(fig2)

    # Waterfall
    fig3, ax = plt.subplots(figsize=(fig_width, fig_height))
    colors = ['green' if x>=0 else 'red' for x in balance]
    ax.bar(months, balance, color=colors)
    ax.set_xlabel("Month"); ax.set_ylabel("Balance [SEK]"); ax.set_title("Waterfall: Monthly Surplus/Deficit")
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=90); plt.tight_layout()
    waterfall_b64 = fig_to_base64(fig3); plt.close(fig3)

    # ---- Category sections ----
    cat_totals = grouped.groupby("Category")["Actual_total"].sum().sort_values(ascending=False)
    sorted_categories = cat_totals.index.tolist()

    category_sections = []
    for cat in sorted_categories:
        cat_df = grouped[grouped["Category"] == cat][["month", "Actual_total"]].sort_values("month")
        cat_pivot = cat_df.pivot_table(index=None, columns="month", values="Actual_total", aggfunc="sum").fillna(0)
        cat_pivot.columns = [str(c) for c in cat_pivot.columns]

        # Line graph per category
        num_months = len(cat_df["month"].unique())
        max_val = cat_df["Actual_total"].max()
        fig_width = max(6, num_months*0.8)
        fig_height = max(3, max_val * scale_factor)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.plot(cat_df["month"], cat_df["Actual_total"], marker="o", linestyle='-')
        ax.set_title(f"{cat} - Actuals by Month")
        ax.set_xlabel("Month"); ax.set_ylabel("Amount [SEK]")
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=90); plt.tight_layout()
        cat_b64 = fig_to_base64(fig); plt.close(fig)

        section_html = f"""
        <h2>{cat}</h2>
        {cat_pivot.to_html(index=False)}
        <img src="data:image/png;base64,{cat_b64}" />
        """
        category_sections.append(section_html)

    category_summary_html = "\n".join(category_sections)

    # ---- Build HTML ----
    html_path = os.path.join(output_dir, "summary_report.html")
    html_content = f"""
    <html>
    <head>
        <title>Budget Summary Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1,h2 {{ color: #2C3E50; }}
            table {{ border-collapse: collapse; margin: 20px 0; }}
            table, th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            th {{ background-color: #f4f4f4; text-align: center; }}
            td:first-child {{ text-align: left; font-weight: bold; }}
            img {{ max-width: 100%; height: auto; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Budget Summary Report</h1>

        <h2>Income & Totals</h2>
        {month_totals.to_html(index=False)}

        <h2>Charts</h2>
        <h3>Line Graph</h3><img src="data:image/png;base64,{line_b64}" />
        <h3>Stacked Bar Chart</h3><img src="data:image/png;base64,{bar_b64}" />
        <h3>Waterfall Chart</h3><img src="data:image/png;base64,{waterfall_b64}" />

        <h1>Category Summary (Actuals by Month)</h1>
        {category_summary_html}
    </body>
    </html>
    """
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logging.info("Saved rich HTML report to %s", html_path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--data-dir", default="../data", help="Directory with input CSV files")
    parser.add_argument("-o","--output-dir", default="../outputs", help="Directory to save outputs")
    args = parser.parse_args()

    df = read_all_months(args.data_dir)
    if df.empty:
        logging.warning("Nothing to summarize.")
        return

    grouped, income = clean_and_aggregate(df)
    write_outputs(grouped, income, args.output_dir)


if __name__ == "__main__":
    main()
