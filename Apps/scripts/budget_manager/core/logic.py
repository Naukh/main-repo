import pandas as pd
from .db import fetch_entries

def compute_summary(month=None):
    """
    Compute summary totals.

    Parameters:
        month (str): Optional, filter data by "YYYY-MM". If None, include all months.

    Returns:
        month_totals (DataFrame): Monthly totals including Income, Actual, and Balance.
        category_totals (DataFrame): Totals per category.
    """
    df = fetch_entries(month=month)
    if df.empty:
        return None, None

    # Ensure numeric
    df["budgeted"] = pd.to_numeric(df["budgeted"], errors="coerce").fillna(0)
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0)

    # Separate budgets and incomes
    df_budget = df[df["entry_type"] == "budget"]
    df_income = df[df["entry_type"] == "income"]

    # Monthly totals
    grouped_budget = df_budget.groupby(["month", "category"]).agg(
        Actual_total=("actual", "sum")
    ).reset_index()

    grouped_income = df_income.groupby("month").agg(
        Income_total=("actual", "sum")
    ).reset_index()

    month_totals = grouped_budget.groupby("month").sum()[["Actual_total"]].reset_index()
    month_totals = month_totals.merge(grouped_income, on="month", how="left").fillna(0)
    month_totals["Balance"] = month_totals["Income_total"] - month_totals["Actual_total"]

    return month_totals, grouped_budget
