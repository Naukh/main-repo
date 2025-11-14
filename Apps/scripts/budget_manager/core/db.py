import streamlit as st
from core.db import fetch_entries, ensure_db_exists, seed_sample_data
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Summary", layout="wide")

def compute_summary():
    """Compute totals per month and category."""
    ensure_db_exists()

    # Seed sample data if empty
    if fetch_entries().empty:
        seed_sample_data()

    df = fetch_entries()
    if df.empty:
        return {}, {}

    # Group by month and entry_type
    month_totals = df.groupby(["month", "entry_type"])[["budgeted", "actual"]].sum().reset_index()

    # Group by category
    category_totals = df.groupby(["category", "entry_type"])[["budgeted", "actual"]].sum().reset_index()

    return month_totals, category_totals

def run():
    st.title("📊 Summary")

    month_totals, category_totals = compute_summary()

    if month_totals.empty:
        st.info("No data to summarize.")
        return

    st.subheader("Monthly Totals")
    st.dataframe(month_totals)

    st.subheader("Category Totals")
    st.dataframe(category_totals)

run()
