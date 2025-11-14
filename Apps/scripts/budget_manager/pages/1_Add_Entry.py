import streamlit as st
from core.db import fetch_distinct_categories_subcategories, insert_entry
from datetime import date
from components.quit_botton import quit_button

st.set_page_config(page_title="Add Entry", layout="wide")

def run():
    st.title("➕ Add Entry")
    with st.form("add_entry", clear_on_submit=True):

        entry_type = st.selectbox("Entry Type", ["budget", "income"])
        today = date.today()
        month = st.text_input("Month (YYYY-MM)", value=f"{today.year}-{today.month:02d}")
        date_input = st.date_input("Date", value=today)

        categories, cat_sub = fetch_distinct_categories_subcategories()
        categories = sorted(categories)

        category = st.selectbox("Category", [""] + categories)
        subcats = sorted([sc for c, sc in cat_sub if c == category])
        subcategory = st.selectbox("Subcategory", [""] + subcats)

        description = st.text_input("Description")
        budgeted = st.number_input("Budgeted", value=0.0)
        actual = st.number_input("Actual", value=0.0)
        account = st.text_input("Account")
        notes = st.text_area("Notes")

        if st.form_submit_button("Save"):
            entry = dict(
                entry_type=entry_type,
                date=str(date_input),
                month=month,
                category=category,
                subcategory=subcategory,
                description=description,
                budgeted=budgeted,
                actual=actual,
                account=account,
                notes=notes,
            )
            insert_entry(entry)
            st.success("Entry saved.")

run()

quit_button()
