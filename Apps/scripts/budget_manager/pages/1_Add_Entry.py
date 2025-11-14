import streamlit as st
from core.db import fetch_distinct_categories_subcategories, insert_entry
from datetime import date
from components.quit_botton import quit_button

st.set_page_config(page_title="Add Entry", layout="wide")

def run():
    st.title("➕ Add Entry")
    today = date.today()

    # -------------------------------
    # Form to add entry
    # -------------------------------
    with st.form("add_entry", clear_on_submit=True):
        # Entry type
        entry_type = st.selectbox("Entry Type", ["budget", "income"])

        # Date input
        date_input = st.date_input("Date", value=today)
        month = date_input.strftime("%Y-%m")  # automatically derive month

        # Fetch categories and subcategories dynamically from DB
        categories, cat_sub_pairs = fetch_distinct_categories_subcategories()
        categories = sorted(categories)

        # Category selection
        category = st.selectbox("Category", categories)
        subcategories = sorted([sc for c, sc in cat_sub_pairs if c == category])
        if not subcategories:
            subcategories = [""]  # fallback if no subcategories exist
        subcategory = st.selectbox("Subcategory", subcategories)

        # Other fields
        description = st.text_input("Description")
        budgeted = st.number_input("Budgeted", value=0.0, step=1.0)
        actual = st.number_input("Actual", value=0.0, step=1.0)
        account = st.text_input("Account")
        notes = st.text_area("Notes")

        # Submit
        if st.form_submit_button("Save"):
            entry = {
                "entry_type": entry_type,
                "date": str(date_input),
                "month": month,
                "category": category,
                "subcategory": subcategory,
                "description": description,
                "budgeted": budgeted,
                "actual": actual,
                "account": account,
                "notes": notes,
            }
            insert_entry(entry)
            st.success(f"Entry for {month} saved successfully!")

run()
quit_button()
