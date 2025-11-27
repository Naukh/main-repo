# pages/1_Add_Entry.py
import streamlit as st
from core.db import fetch_distinct_categories_subcategories, insert_entry, initialize_new_month
from datetime import date
from components.quit_botton import quit_button

st.set_page_config(page_title="Add Entry", layout="wide")

def run():
    st.title("➕ Add Entry")
    today = date.today()

    # -------------------------------
    # Fetch categories OUTSIDE form (so they rerun live)
    # -------------------------------
    categories, cat_sub_pairs = fetch_distinct_categories_subcategories()
    categories = sorted([c for c in categories if c])

    category_options = [""] + categories
    category = st.selectbox("Category", category_options, index=0, key="add_category")

    # ✅ This now updates LIVE when category changes
    if category:
        subcats = sorted([
            sc for c, sc in cat_sub_pairs
            if c and sc and c.strip() == category.strip()
        ])
    else:
        subcats = []

    subcategory = st.selectbox(
        "Subcategory",
        [""] + subcats if subcats else [""],
        index=0,
        key="add_subcategory"
    )

    # -------------------------------
    # Form to add entry
    # -------------------------------
    with st.form("add_entry", clear_on_submit=True):

        entry_type = st.selectbox("Entry Type", ["budget", "income"], key="add_entry_type")

        date_input = st.date_input("Date", value=today, key="add_date")
        month = date_input.strftime("%Y-%m")

        description = st.text_input("Description", key="add_description")
        budgeted = st.number_input("Budgeted", value=0.0, key="add_budgeted")
        actual = st.number_input("Actual", value=0.0, key="add_actual")
        account = st.text_input("Account", key="add_account")
        notes = st.text_area("Notes", key="add_notes")

        if st.form_submit_button("Save", use_container_width=True):
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
            st.success(f"Entry for {month} saved successfully!")
            st.rerun()
# -------------------------------

run()

# Option to initialize new month
st.subheader("📅 Initialize New Month")

new_month = st.text_input("Enter new month (YYYY-MM)")
carry_budget = st.checkbox("Carry over last month's budgets")

if st.button("Initialize New Month"):
    if len(new_month) != 7 or new_month[4] != "-":
        st.error("Invalid format. Use YYYY-MM.")
    else:
        success, msg = initialize_new_month(new_month, carry_budget)
        if success:
            st.success(msg)
        else:
            st.error(msg)


quit_button()
