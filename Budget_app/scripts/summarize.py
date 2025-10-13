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

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


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
        return pd.DataFrame(
            columns=[
                "EntryType",
                "Date",
                "Category",
                "Subcategory",
                "Description",
                "Budgeted",
                "Actual",
                "Income",
                "Account",
                "Notes",
                "month",
            ]
        )
    dfs = []
    for f in files:
        month = os.path.splitext(os.path.basename(f))[0]
        try:
            encoding = detect_encoding(f)
            df = pd.read_csv(f, encoding=encoding)
        except Exception as e:
            logging.error("Failed to read %s: %s", f, e)
            continue
        df["month"] = month
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def clean_and_aggregate(df):
    df["Budgeted"] = pd.to_numeric(df.get("Budgeted", 0), errors="coerce").fillna(0.0)
    df["Actual"] = pd.to_numeric(df.get("Actual", 0), errors="coerce").fillna(0.0)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")

    df_budget = df[df["EntryType"] == "budget"]
    df_income = df[df["EntryType"] == "income"]

    grouped = (
        df_budget.groupby(["month", "Category"])
        .agg(Actual_total=("Actual", "sum"))
        .reset_index()
    )

    income = (
        df_income.groupby("month").agg(Income_total=("Actual", "sum")).reset_index()
    )

    grouped["month"] = grouped["month"].dt.strftime("%Y-%m")
    income["month"] = income["month"].dt.strftime("%Y-%m")

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


# ---------- Utility: Save figure to Base64 ----------
def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ---------- Data preparation ----------
def prepare_month_totals(grouped, income):
    """Prepare monthly totals and balance DataFrame."""
    month_totals = grouped.groupby("month").sum()[["Actual_total"]].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals["Balance"] = (
        month_totals["Income_total"] - month_totals["Actual_total"]
    )
    return month_totals


# ---------- Plotting ----------
def generate_summary_charts(month_totals):
    """Generate Base64-encoded plots for line, stacked bar, and waterfall charts with rotated y-axis labels."""
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

    # ---- Line Chart ----
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    ax.plot(months, actual, marker="o", label="Expenses (Actual)", color="#e57373")
    ax.plot(months, income_total, marker="o", label="Income", color="#81c784")
    ax.plot(
        months, balance, marker="o", linestyle="--", label="Balance", color="#64b5f6"
    )
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Amount [SEK]", color="white")
    ax.set_title("Line Graph: Monthly Summary", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    ax.legend()
    # Rotate y-axis labels
    for label in ax.get_yticklabels():
        label.set_rotation(0)

    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["line"] = fig_to_base64(fig)
    plt.close(fig)

    # ---- Stacked Bar Chart ----
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    ax.bar(months, actual, label="Actual Expenses", color="#ef5350")
    ax.bar(
        months,
        income_total - actual,
        bottom=actual,
        label="Remaining Income",
        color="#66bb6a",
    )
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Amount [SEK]", color="white")
    ax.set_title("Stacked Bar Chart: Income vs Expenses", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    ax.legend()
    for label in ax.get_yticklabels():
        label.set_rotation(0)

    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["bar"] = fig_to_base64(fig)
    plt.close(fig)

    # ---- Waterfall Chart ----
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
    ax.set_facecolor(ax_face)
    colors = ["#66bb6a" if x >= 0 else "#ef5350" for x in balance]
    ax.bar(months, balance, color=colors)
    ax.set_xlabel("Month", color="white")
    ax.set_ylabel("Balance [SEK]", color="white")
    ax.set_title("Waterfall: Monthly Surplus/Deficit", color="white")
    ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
    for label in ax.get_yticklabels():
        label.set_rotation(0)

    for spine in ax.spines.values():
        spine.set_color(grid_color)
    plt.tight_layout()
    charts["waterfall"] = fig_to_base64(fig)
    plt.close(fig)

    return charts


# ---------- Category section generation ----------
def generate_category_sections(grouped, scale_factor=5 / 150000):
    """Generate HTML sections per category with charts."""
    cat_totals = (
        grouped.groupby("Category")["Actual_total"].sum().sort_values(ascending=False)
    )
    sorted_categories = cat_totals.index.tolist()
    sections = []

    plt.style.use("dark_background")
    fig_face, ax_face, grid_color = "#121212", "#1a1a1a", "#555"

    for cat in sorted_categories:
        cat_df = grouped[grouped["Category"] == cat][
            ["month", "Actual_total"]
        ].sort_values("month")
        cat_pivot = cat_df.pivot_table(
            index=None, columns="month", values="Actual_total", aggfunc="sum"
        ).fillna(0)
        cat_pivot.columns = [str(c) for c in cat_pivot.columns]

        num_months = len(cat_df["month"].unique())
        max_val = cat_df["Actual_total"].max()
        fig_width = max(6, num_months * 0.8)
        fig_height = max(3, max_val * scale_factor)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_face)
        ax.set_facecolor(ax_face)
        ax.plot(cat_df["month"], cat_df["Actual_total"], marker="o", color="#64b5f6")
        ax.set_title(f"{cat} - Actuals by Month", color="white")
        ax.set_xlabel("Month", color="white")
        ax.set_ylabel("Amount [SEK]", color="white")
        ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
        ax.tick_params(colors="white", axis="y", rotation=0)
        for spine in ax.spines.values():
            spine.set_color(grid_color)
        plt.tight_layout()
        cat_b64 = fig_to_base64(fig)
        plt.close(fig)

        sections.append(
            f"""
            <h2>{cat}</h2>
            {cat_pivot.to_html(index=False, border=0, justify='center')}
            <img src="data:image/png;base64,{cat_b64}" />
        """
        )

    return "\n".join(sections)


# ---------- HTML writer ----------
def write_html_report(output_dir, month_totals, charts, category_summary_html):
    """Render and write dark-themed HTML report."""
    html_path = os.path.join(output_dir, "summary_report.html")
    html_content = f"""
    <html>
    <head>
        <title>Budget Summary Report</title>
        <style>
            body {{
                background-color: #121212;
                color: #ffffff;
                font-family: Arial, sans-serif;
                margin: 40px;
            }}
            h1, h2, h3 {{
                color: #80cbc4;
            }}
            table {{
                border-collapse: collapse;
                margin: 20px 0;
                width: 100%;
            }}
            table, th, td {{
                border: 1px solid #444;
                padding: 8px;
                text-align: right;
            }}
            th {{
                background-color: #1f1f1f;
                color: #ffffff;
                text-align: center;
            }}
            tr:nth-child(even) {{ background-color: #1a1a1a; }}
            tr:nth-child(odd) {{ background-color: #222; }}
            td:first-child {{ text-align: left; font-weight: bold; }}
            img {{
                max-width: 100%;
                height: auto;
                margin: 20px 0;
                border: 1px solid #444;
                border-radius: 8px;
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
            }}
        </style>
    </head>
    <body>
        <h1>Budget Summary Report</h1>

        <h2>Income & Totals</h2>
        {month_totals.to_html(index=False, border=0, justify='center')}

        <h2>Charts</h2>
        <h3>Line Graph</h3><img src="data:image/png;base64,{charts['line']}" />
        <h3>Stacked Bar Chart</h3><img src="data:image/png;base64,{charts['bar']}" />
        <h3>Waterfall Chart</h3><img src="data:image/png;base64,{charts['waterfall']}" />

        <h1>Category Summary (Actuals by Month)</h1>
        {category_summary_html}
    </body>
    </html>
    """

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logging.info("Saved dark-themed HTML report to %s", html_path)


# ---------- Main wrapper ----------
def write_outputs(grouped, income, output_dir):
    """Main entry: orchestrates CSV, plots, and HTML report generation."""
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "summary_by_category.csv")
    safe_save(grouped.to_csv, csv_path, index=False)

    month_totals = prepare_month_totals(grouped, income)
    charts = generate_summary_charts(month_totals)
    category_html = generate_category_sections(grouped)
    write_html_report(output_dir, month_totals, charts, category_html)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--data-dir", default="../data", help="Directory with input CSV files"
    )
    parser.add_argument(
        "-o", "--output-dir", default="../outputs", help="Directory to save outputs"
    )
    args = parser.parse_args()

    df = read_all_months(args.data_dir)
    if df.empty:
        logging.warning("Nothing to summarize.")
        return

    grouped, income = clean_and_aggregate(df)
    write_outputs(grouped, income, args.output_dir)


if __name__ == "__main__":
    main()
