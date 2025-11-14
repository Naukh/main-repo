import streamlit as st
from core.db import fetch_entries
from components.quit_botton import quit_button
import pandas as pd

st.set_page_config(page_title="Summary", layout="wide")

def run():
    st.title("📈 Summary")

    # -------------------------------
    # Fetch all entries
    # -------------------------------
    df = fetch_entries()
    if df.empty:
        st.info("No data to summarize.")
        return

    # -------------------------------
    # Month selection
    # -------------------------------
    months = sorted(df["month"].dropna().unique(), reverse=True)
    selected_month = st.selectbox("Select month (or all months):", ["-- all --"] + months)

    # Filter by selected month
    df_filtered = df if selected_month == "-- all --" else df[df["month"] == selected_month]

    if df_filtered.empty:
        st.info("No entries for the selected month.")
        return

    # -------------------------------
    # Convert numeric columns
    # -------------------------------
    df_filtered["budgeted"] = pd.to_numeric(df_filtered["budgeted"], errors="coerce").fillna(0)
    df_filtered["actual"] = pd.to_numeric(df_filtered["actual"], errors="coerce").fillna(0)

    df_budget = df_filtered[df_filtered["entry_type"] == "budget"]
    df_income = df_filtered[df_filtered["entry_type"] == "income"]

    # -------------------------------
    # Compute Monthly Totals
    # -------------------------------
    month_totals = df_budget.groupby("month").agg(
        Actual_total=("actual", "sum")
    ).reset_index()

    income_totals = df_income.groupby("month").agg(
        Income_total=("actual", "sum")
    ).reset_index()

    total_summary = month_totals.merge(income_totals, on="month", how="left").fillna(0)
    total_summary["Balance"] = total_summary["Income_total"] - total_summary["Actual_total"]

    # -------------------------------
    # Display Monthly Totals
    # -------------------------------
    st.subheader("Monthly Totals")
    st.dataframe(
        total_summary.sort_values("month", ascending=False).reset_index(drop=True),
        width="stretch"
    )

    # -------------------------------
    # Display Category Totals
    # -------------------------------
    st.subheader(f"Category Totals ({'selected month' if selected_month != '-- all --' else 'all months'})")
    cat_totals = df_budget.groupby("category")["actual"].sum().sort_values(ascending=False)
    st.table(cat_totals.reset_index().rename(columns={"actual": "Total Spent"}))


run()
quit_button()
