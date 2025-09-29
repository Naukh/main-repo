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
matplotlib.use("Agg")  # avoid GUI/Tk issues
import matplotlib.pyplot as plt
import logging
import chardet

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
        month = os.path.splitext(os.path.basename(f))[0]  # e.g. "2025-08"
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
    # ensure numeric
    df['Budgeted'] = pd.to_numeric(df.get('Budgeted', 0), errors='coerce').fillna(0.0)
    df['Actual']   = pd.to_numeric(df.get('Actual', 0), errors='coerce').fillna(0.0)

    # ensure month is datetime
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')

    # Split by type
    df_budget = df[df['EntryType'] == 'budget']
    df_income = df[df['EntryType'] == 'income']

    # Budget/actual by category
    grouped = df_budget.groupby(['month','Category']).agg(
        Budgeted_total=('Budgeted','sum'),
        Actual_total=('Actual','sum'),
        Count_entries=('Description','count')
    ).reset_index()

    # Income by month (total only, no category breakdown)
    income = df_income.groupby('month').agg(
        Income_total=('Actual','sum')  # use Actual to reflect reality
    ).reset_index()

    # Clean up
    grouped = grouped.sort_values('month')
    grouped['month'] = grouped['month'].dt.strftime('%Y-%m')
    income['month']  = income['month'].dt.strftime('%Y-%m')

    return grouped, income


def safe_save(func, path, retries=3, delay=2):
    """Try saving a file safely, retrying if PermissionError occurs."""
    import time
    for i in range(retries):
        try:
            func()
            logging.info("Saved %s", path)
            return
        except PermissionError:
            logging.warning("File %s is open (attempt %d/%d). Retrying in %ds...",
                            path, i + 1, retries, delay)
            time.sleep(delay)
    logging.error("Failed to save %s after %d attempts. Please close the file.", path)


import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import logging
import os

def safe_save(save_func, path, *args, **kwargs):
    """Attempt to save file, retry after asking user to close it if permission denied."""
    try:
        save_func(path, *args, **kwargs)
        logging.info("Saved file to %s", path)
    except PermissionError:
        logging.error("Permission denied when saving %s. Is the file open?", path)
        input("Close the file and press Enter to retry...")
        save_func(path, *args, **kwargs)
        logging.info("Saved file to %s", path)

def write_outputs(grouped, income, output_dir):
    """Save CSV, HTML, and multiple plot variants (line, bar, area, waterfall)."""
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.ticker import FuncFormatter

    os.makedirs(output_dir, exist_ok=True)

    # Save CSV & HTML
    csv_path = os.path.join(output_dir, "summary_by_category.csv")
    html_path = os.path.join(output_dir, "summary_by_category.html")
    safe_save(grouped.to_csv, csv_path, index=False)
    safe_save(grouped.to_html, html_path, index=False)

    # Combine totals
    month_totals = grouped.groupby('month').sum()[['Budgeted_total','Actual_total']].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals['Balance'] = month_totals['Income_total'] - month_totals['Actual_total']

    months = month_totals['month']
    budgeted = month_totals['Budgeted_total']
    actual = month_totals['Actual_total']
    income_total = month_totals['Income_total']
    balance = month_totals['Balance']

    # ---- 1. Line Graph ----
    fig_width = max(8, len(months) * 0.8)
    max_val = max(budgeted.max(), actual.max(), income_total.max(), balance.abs().max())
    scale_factor = 5 / 150000
    fig_height = max(4, max_val * scale_factor)

    plt.figure(figsize=(fig_width, fig_height))
    plt.plot(months, budgeted, marker='o', label="Expenses (Budgeted)")
    plt.plot(months, actual, marker='o', label="Expenses (Actual)")
    plt.plot(months, income_total, marker='o', label="Income")
    plt.plot(months, balance, marker='o', linestyle="--", label="Balance")
    plt.xlabel("Month")
    plt.ylabel("Amount [SEK]")
    plt.title("Line Graph: Monthly Summary")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(bottom=0.25)
    ax = plt.gca()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10000))
    safe_save(plt.savefig, os.path.join(output_dir, "line_graph.png"), dpi=300)
    safe_save(plt.savefig, os.path.join(output_dir, "line_graph.pdf"))
    plt.close()

    # ---- 2. Stacked Bar Chart ----
    plt.figure(figsize=(fig_width, fig_height))
    plt.bar(months, actual, label='Actual Expenses', color='salmon')
    plt.bar(months, income_total - actual, bottom=actual, label='Remaining Income', color='lightgreen')
    plt.plot(months, budgeted, marker='o', color='blue', label='Budgeted Expenses')
    plt.xlabel("Month")
    plt.ylabel("Amount [SEK]")
    plt.title("Stacked Bar Chart: Income vs Expenses")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    safe_save(plt.savefig, os.path.join(output_dir, "stacked_bar.png"), dpi=300)
    safe_save(plt.savefig, os.path.join(output_dir, "stacked_bar.pdf"))
    plt.close()

    # ---- 3. Waterfall Chart ----
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    bar_colors = ['green' if x >=0 else 'red' for x in balance]
    ax.bar(months, balance, color=bar_colors)
    ax.set_xlabel("Month")
    ax.set_ylabel("Balance [SEK]")
    ax.set_title("Waterfall: Monthly Surplus/Deficit")
    plt.grid(True, linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x/1000)}k'))
    plt.xticks(rotation=90)
    plt.tight_layout()
    safe_save(plt.savefig, os.path.join(output_dir, "waterfall.png"), dpi=300)
    safe_save(plt.savefig, os.path.join(output_dir, "waterfall.pdf"))
    plt.close()


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

    # NOTE: clean_and_aggregate returns (grouped, income) — unpack both
    grouped, income = clean_and_aggregate(df)
    write_outputs(grouped, income, args.output_dir)


if __name__ == "__main__":
    main()
