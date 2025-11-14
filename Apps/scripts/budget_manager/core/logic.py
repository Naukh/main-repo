import pandas as pd
from .db import fetch_entries

def compute_summary():
    df = fetch_entries()

    if df.empty:
        return None, None

    df["budgeted"] = pd.to_numeric(df["budgeted"], errors="coerce").fillna(0)
    df["actual"]  = pd.to_numeric(df["actual"], errors="coerce").fillna(0)

    df_budget = df[df["entry_type"] == "budget"]
    df_income = df[df["entry_type"] == "income"]

    # Monthly totals
    grouped = df_budget.groupby(["month", "category"]).agg(
        Actual_total=("actual", "sum")
    ).reset_index()

    income = df_income.groupby("month").agg(
        Income_total=("actual", "sum")
    ).reset_index()

    month_totals = grouped.groupby("month").sum()[["Actual_total"]].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals["Balance"] = month_totals["Income_total"] - month_totals["Actual_total"]

    return month_totals, grouped
