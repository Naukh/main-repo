#!/usr/bin/env python3
"""
Loan payoff simulator (CSV + forecast)

- Reads cumulative principal, interest, and balance from CSV.
- Continues simulation from last point using original loan amount.
- Generates amortization table (HTML) and two-panel plot (PNG).
- Includes loan summary section in HTML.

Author: ChatGPT
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# =============================
# CONFIG
# =============================
CSV_FILE = Path("../data/Mortgage_data_file/Mortgage_payments.csv")
OUTPUT_DIR = Path("../outputs")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

HTML_FILE = OUTPUT_DIR / "Mortgage_payment_summary.html"
PNG_FILE = OUTPUT_DIR / "Mortgage_payment_graph.png"

# Loan simulation parameters
ANNUAL_INTEREST_RATE = 2.45  # annual rate in %
MIN_PRINCIPAL_ANNUAL_PCT = 2.0  # min principal % of total loan
FIXED_MONTHLY_PAYMENT = 12_000.0  # use None if no fixed payment value is to be used
MAX_MONTHS = 2000
START_MONTH = datetime(2025, 10, 1)  # next period start

# =============================
# FUNCTIONS
# =============================


def load_csv_data(csv_path):
    """Load the CSV and extract cumulative values and original principal."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Remove quotes and split
    lines_clean = [line.strip('"') for line in lines]
    header = [h.strip() for h in lines_clean[0].split(",")]
    data = [[x.strip() for x in row.split(",")] for row in lines_clean[1:]]

    df = pd.DataFrame(data, columns=header)

    # Clean numeric columns
    numeric_cols = ["Interest", "Principal", "Total", "Balance", "Interest_Rate"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            # Column missing, fill with zeros
            df[col] = 0.0

    cumulative_interest = df["Interest"].sum()
    cumulative_principal = df["Principal"].sum()
    current_balance = df.iloc[-1]["Balance"]

    # The *original* loan is the first nonzero Balance in the CSV
    original_loan = df.loc[df["Balance"] > 0, "Balance"].iloc[0]

    return original_loan, current_balance, cumulative_principal, cumulative_interest


def simulate_loan(
    principal_remaining,
    annual_rate,
    min_principal_annual_pct,
    fixed_monthly_payment,
    cumulative_principal,
    cumulative_interest,
    original_loan,
    max_months=2000,
):
    """Simulate loan amortization from current balance."""
    monthly_rate = annual_rate / 12.0 / 100.0
    min_monthly_principal = original_loan * (min_principal_annual_pct / 100.0) / 12.0

    rows = []
    balance = principal_remaining
    month = 0

    while balance > 1e-8 and month < max_months:
        month += 1
        interest = balance * monthly_rate
        required_min_payment = interest + min_monthly_principal

        payment = (
            fixed_monthly_payment
            if fixed_monthly_payment is not None
            else required_min_payment
        )
        payment = max(payment, required_min_payment)

        principal_payment = payment - interest
        if principal_payment > balance:
            principal_payment = balance
            payment = interest + principal_payment

        balance -= principal_payment
        cumulative_interest += interest
        cumulative_principal += principal_payment

        rows.append(
            {
                "Month": month,
                "Payment": round(payment, 2),
                "Interest": round(interest, 2),
                "Principal Paid": round(principal_payment, 2),
                "Remaining Balance": round(balance, 2),
                "Cumulative Interest": round(cumulative_interest, 2),
                "Cumulative Principal": round(cumulative_principal, 2),
                "Required Min Payment": round(required_min_payment, 2),
            }
        )

        if payment <= interest + 1e-12:
            print("Payment only covers interest — loan will not amortize.")
            break

    return pd.DataFrame(rows)


def plot_results(df, output_path):
    """Generate dark-themed two-panel plot with independent axes and clear formatting."""
    df["Date"] = pd.date_range(start=START_MONTH, periods=len(df), freq="MS")

    # --- Dark theme settings ---
    plt.style.use("dark_background")  # built-in dark style
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), facecolor="#121212")
    ax1.set_facecolor("#1a1a1a")
    ax2.set_facecolor("#1a1a1a")

    # --- Top: Remaining balance ---
    ax1.plot(df["Date"], df["Remaining Balance"] / 1000, color="#64b5f6", linewidth=2)
    ax1.set_title("Loan Remaining Balance Over Time (in thousands SEK)", color="white", pad=10)
    ax1.set_ylabel("Balance (thousands SEK)", color="white")
    ax1.set_xlabel("Date", labelpad=10, color="white")
    ax1.grid(True, linestyle="--", alpha=0.3, color="white")

    # --- Bottom: Monthly payments ---
    ax2.plot(df["Date"], df["Payment"] / 1000, color="#81c784", linewidth=2)
    ax2.set_title("Monthly Payment Over Time (in thousands SEK)", color="white", pad=10)
    ax2.set_ylabel("Payment (thousands SEK)", color="white")
    ax2.set_xlabel("Date", labelpad=10, color="white")
    ax2.grid(True, linestyle="--", alpha=0.3, color="white")

    # --- X-axis formatting ---
    locator = mdates.MonthLocator(interval=6)
    formatter = mdates.DateFormatter("%b-%Y")
    for ax in (ax1, ax2):
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params(axis="x", colors="white", rotation=90)
        ax.tick_params(axis="y", colors="white")
        for spine in ax.spines.values():
            spine.set_color("#555")

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5)

    # --- Save dark-themed figure ---
    plt.savefig(output_path, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved plot: {output_path.resolve()}")


def write_html(
    sim_df,
    original_loan,
    current_balance,
    cumulative_principal,
    total_months,
    cumulative_interest,
    total_interest,
    html_file,
    plot_file,
):
    """Generate dark-themed HTML report with summary and payment plan table."""

    end_date = START_MONTH + relativedelta(months=total_months - 1)

    # --- CSS for dark theme ---
    dark_style = """
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h2 {
            color: #80cbc4;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            border: 1px solid #444;
            padding: 8px;
            text-align: center;
        }
        th {
            background-color: #1f1f1f;
        }
        tr:nth-child(even) {
            background-color: #1a1a1a;
        }
        tr:nth-child(odd) {
            background-color: #222;
        }
        img {
            display: block;
            margin: 20px auto;
            border: 1px solid #444;
            border-radius: 8px;
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
        }
    </style>
    """

    # --- Summary section ---
    summary_html = f"""
    <h2>Loan Summary</h2>
    <p>The summary of total prognosed loan repayment plan:</p>
    <table>
        <tr>
            <th>Total Loan (SEK)</th>
            <th>Remaining Loan (SEK)</th>
            <th>Total Principal Paid (SEK)</th>
            <th>Total Payments Left</th>
            <th>Expected End Date</th>
            <th>Total Interest Paid (SEK)</th>
            <th>Total Interest Payment Prediction (SEK)</th>
        </tr>
        <tr>
            <td>{original_loan:,.2f}</td>
            <td>{current_balance:,.2f}</td>
            <td>{cumulative_principal:,.2f}</td>
            <td>{total_months}</td>
            <td>{end_date.strftime("%b-%Y")}</td>
            <td>{cumulative_interest:,.2f}</td>
            <td>{total_interest:,.2f}</td>
        </tr>
    </table>
    """

    # --- Format numeric columns ---
    cols_to_format = [
        "Payment",
        "Interest",
        "Principal Paid",
        "Remaining Balance",
        "Cumulative Interest",
        "Cumulative Principal",
        "Required Min Payment",
    ]
    format_dict = {col: lambda x: f"{x:,.2f}" for col in cols_to_format}

    payment_plan_table_html = sim_df.to_html(
        index=False,
        formatters=format_dict,
        border=0,
        justify="center",
        classes="payment-table",
    )

    # --- Payment plan section ---
    payment_plan_html = f"""
    <h2>Payment Plan</h2>
    <p>The complete loan repayment plan is shown in figure and table below:</p>
    <img src="{plot_file.name}" alt="Loan Plot">
    {payment_plan_table_html}
    """

    # --- Full HTML document ---
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Loan Report</title>
        {dark_style}
    </head>
    <body>
        {summary_html}
        {payment_plan_html}
    </body>
    </html>
    """

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Saved HTML report: {html_file.resolve()}")


# =============================
# MAIN
# =============================
def main():
    original_loan, current_balance, cumulative_principal, cumulative_interest = (
        load_csv_data(CSV_FILE)
    )

    sim_df = simulate_loan(
        current_balance,
        ANNUAL_INTEREST_RATE,
        MIN_PRINCIPAL_ANNUAL_PCT,
        FIXED_MONTHLY_PAYMENT,
        cumulative_principal,
        cumulative_interest,
        original_loan,
        MAX_MONTHS,
    )

    # Add calendar month column
    sim_df["Calendar Month"] = [
        (START_MONTH + relativedelta(months=i - 1)).strftime("%b-%Y")
        for i in sim_df["Month"]
    ]
    cols = ["Month", "Calendar Month"] + [
        c for c in sim_df.columns if c not in ("Month", "Calendar Month")
    ]
    sim_df = sim_df[cols]

    # Plot results
    plot_results(sim_df, PNG_FILE)

    # Write HTML report
    total_months = sim_df["Month"].iloc[-1]
    total_interest = sim_df["Interest"].sum()
    write_html(
        sim_df,
        original_loan,
        current_balance,
        cumulative_principal,
        total_months,
        cumulative_interest,
        total_interest,
        HTML_FILE,
        PNG_FILE,
    )


if __name__ == "__main__":
    main()
