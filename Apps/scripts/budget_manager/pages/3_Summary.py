import streamlit as st
from core.logic import compute_summary
from components.quit_botton import quit_button

st.set_page_config(page_title="Summary", layout="wide")

def run():
    st.title("📈 Summary")

    month_totals, grouped = compute_summary()

    if month_totals is None:
        st.info("No data to summarize.")
        return

    # -------------------------------------------
    # Monthly Totals
    # -------------------------------------------
    st.subheader("Monthly Totals")
    st.dataframe(
        month_totals.sort_values("month", ascending=False).reset_index(drop=True),
        width="stretch"
    )

    # -------------------------------------------
    # Category Totals
    # -------------------------------------------
    st.subheader("Category Totals (all months combined)")

    cat_totals = grouped.groupby("category")["Actual_total"].sum().sort_values(ascending=False)
    st.table(cat_totals.reset_index().rename(columns={"Actual_total": "Total Spent"}))


run()

quit_button()