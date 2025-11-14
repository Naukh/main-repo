import streamlit as st
import pandas as pd

from core.db import (
    fetch_entries,
    fetch_distinct_categories_subcategories,
    bulk_update_rows,
    bulk_delete,
)
from components.quit_botton import quit_button


st.set_page_config(page_title="View/Edit", layout="wide")

def run():
    st.title("📋 View & Edit Entries")

    # -------------------------------------------
    # Fetch all entries
    # -------------------------------------------
    df_all = fetch_entries()

    if df_all.empty:
        st.info("No entries in database.")
        return

    # -------------------------------------------
    # Filter options
    # -------------------------------------------
    months = sorted(df_all["month"].dropna().unique(), reverse=True)
    categories, cat_subpairs = fetch_distinct_categories_subcategories()
    categories = sorted(categories)
    subcategories = sorted({sc for _, sc in cat_subpairs})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        month_filter = st.selectbox(
            "Filter by month (optional)",
            options=["-- all --"] + months,
            index=0  # default to "-- all --"
        )

    with col2:
        category_filter = st.selectbox(
            "Filter by category (optional)",
            options=["-- all --"] + categories
        )

    with col3:
        subcategory_filter = st.selectbox(
            "Filter by subcategory (optional)",
            options=["-- all --"] + subcategories
        )

    with col4:
        entry_type_filter = st.selectbox(
            "Entry type",
            options=["-- all --", "budget", "income"]
        )

    # -------------------------------------------
    # Apply filters
    # -------------------------------------------
    month_val = None if month_filter == "-- all --" else month_filter
    cat_val   = None if category_filter == "-- all --" else category_filter
    sub_val   = None if subcategory_filter == "-- all --" else subcategory_filter
    et_val    = None if entry_type_filter == "-- all --" else entry_type_filter

    df = fetch_entries(
        month=month_val,
        category=cat_val,
        subcategory=sub_val,
        entry_type=et_val
    )

    if df.empty:
        st.info("No rows match your filters.")
        return

    st.write("Edit inline and click **Save changes**:")

    # -------------------------------------------
    # Editable table
    # -------------------------------------------
    editable_df = st.data_editor(
        df,
        width="stretch",
        num_rows="dynamic",
        disabled=["id"],
        column_config={
            "entry_type": st.column_config.SelectboxColumn(
                "Entry Type", options=["budget", "income"]
            ),
            "category": st.column_config.SelectboxColumn(
                "Category", options=categories
            ),
            "subcategory": st.column_config.SelectboxColumn(
                "Subcategory", options=subcategories
            ),
        },
    )

    # -------------------------------------------
    # Detect modified rows
    # -------------------------------------------
    merged = editable_df.merge(df, on="id", suffixes=("_new", "_orig"))

    changed_mask = (
        (merged["month_new"] != merged["month_orig"]) |
        (merged["entry_type_new"] != merged["entry_type_orig"]) |
        (merged["date_new"] != merged["date_orig"]) |
        (merged["category_new"] != merged["category_orig"]) |
        (merged["subcategory_new"] != merged["subcategory_orig"]) |
        (merged["description_new"] != merged["description_orig"]) |
        (merged["budgeted_new"] != merged["budgeted_orig"]) |
        (merged["actual_new"] != merged["actual_orig"]) |
        (merged["account_new"] != merged["account_orig"]) |
        (merged["notes_new"] != merged["notes_orig"])
    )

    changed_rows = merged[changed_mask]
    st.write(f"**{len(changed_rows)} row(s) changed.**")

    # -------------------------------------------
    # Save changes button
    # -------------------------------------------
    if not changed_rows.empty:
        if st.button("Save changes"):
            to_update = changed_rows[[
                "month_new","entry_type_new","date_new","category_new","subcategory_new",
                "description_new","budgeted_new","actual_new","account_new","notes_new","id"
            ]].copy()

            to_update.columns = [
                "month","entry_type","date","category","subcategory",
                "description","budgeted","actual","account","notes","id"
            ]

            updated = bulk_update_rows(to_update)
            st.success(f"Updated {updated} rows.")

    # -------------------------------------------
    # Delete rows
    # -------------------------------------------
    st.write("---")
    ids = st.multiselect("Select rows to delete (by ID)", df["id"].tolist())

    if ids:
        if st.button("Delete selected"):
            deleted = bulk_delete(ids)
            st.success(f"Deleted {deleted} row(s).")

run()

quit_button()