#!/usr/bin/env python3
"""
Streamlit Budget Manager
- Connects to SQLite DB (budget.db)
- Add / Edit / Delete entries directly in DB
"""

import sqlite3
import pandas as pd
import streamlit as st
from datetime import date
import os
from typing import List, Tuple
import signal

# CONFIG: adjust if needed
DB_PATH = os.path.join("..", "data", "budget.db")  # relative to where you run the app
TABLE_NAME = "entries"

st.set_page_config(page_title="Budget Manager", layout="wide")


# ----------------- DB helpers -----------------

def get_conn():
    return sqlite3.connect(DB_PATH)


def ensure_db_available():
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at: {DB_PATH}")
        st.stop()


def fetch_entries(month=None, category=None, subcategory=None, entry_type=None):
    conn = get_conn()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []

    if month:
        query += " AND month=?"
        params.append(month)
    if category:
        query += " AND category=?"
        params.append(category)
    if subcategory:
        query += " AND subcategory=?"
        params.append(subcategory)
    if entry_type:
        query += " AND entry_type=?"
        params.append(entry_type)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df



def fetch_distinct_categories_subcategories() -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Return:
      - list of distinct categories
      - list of (category, subcategory) tuples
    """
    ensure_db_available()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT category FROM {TABLE_NAME} WHERE category IS NOT NULL")
    categories = [r[0] for r in cur.fetchall() if r[0]]
    cur.execute(f"SELECT DISTINCT category, subcategory FROM {TABLE_NAME} WHERE category IS NOT NULL AND subcategory IS NOT NULL")
    cat_sub = [(r[0], r[1]) for r in cur.fetchall()]
    conn.close()
    return categories, cat_sub


def insert_entry(entry: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TABLE_NAME} (entry_type, date, month, category, subcategory, description, budgeted, actual, account, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry.get("entry_type"),
        entry.get("date"),
        entry.get("month"),
        entry.get("category"),
        entry.get("subcategory"),
        entry.get("description"),
        entry.get("budgeted"),
        entry.get("actual"),
        entry.get("account"),
        entry.get("notes"),
    ))
    conn.commit()
    conn.close()


def bulk_update_rows(changed_df: pd.DataFrame):
    """
    changed_df must contain at least the id column and other fields to update.
    We'll update row-by-row.
    """
    if changed_df.empty:
        return 0
    conn = get_conn()
    cur = conn.cursor()
    updated = 0
    for _, row in changed_df.iterrows():
        # Prepare update values (ensure column types)
        cur.execute(f"""
            UPDATE {TABLE_NAME}
            SET month = ?, entry_type = ?, date = ?, category = ?, subcategory = ?, description = ?,
                budgeted = ?, actual = ?, account = ?, notes = ?
            WHERE id = ?
        """, (
            row.get("month"),
            row.get("entry_type"),
            row.get("date"),
            row.get("category"),
            row.get("subcategory"),
            row.get("description"),
            row.get("budgeted"),
            row.get("actual"),
            row.get("account"),
            row.get("notes"),
            row.get("id"),
        ))
        updated += cur.rowcount
    conn.commit()
    conn.close()
    return updated


def bulk_delete_by_id(ids: List[int]):
    if not ids:
        return 0
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id IN ({','.join(['?']*len(ids))})", ids)
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


# ----------------- UI building blocks -----------------

def add_entry_form():
    with st.form("add_entry", clear_on_submit=True):
        # Get existing categories/subcategories
        categories, cat_sub = fetch_distinct_categories_subcategories()
        categories = sorted(set(categories)) if categories else []
        cat_options = ["-- choose or add new --"] + categories + ["<Add new category>"]

        entry_type = st.selectbox("Entry type", ["budget", "income"])
        today = date.today()
        month_default = f"{today.year}-{today.month:02d}"
        month = st.text_input("Month (YYYY-MM)", value=month_default)
        date_input = st.date_input("Date (optional)", value=today)

        # Category selection with option to add new
        chosen_cat = st.selectbox("Category", options=cat_options, index=0)
        new_category = None
        if chosen_cat == "<Add new category>":
            new_category = st.text_input("New category name")
            category_value = new_category.strip() if new_category else ""
        elif chosen_cat == "-- choose or add new --":
            category_value = ""
        else:
            category_value = chosen_cat

        # Subcategory: fetch subcategories for chosen category if available
        # Build list of subcategories for the chosen category
        subcats = sorted({sc for c, sc in cat_sub if c == category_value}) if category_value else []
        sub_options = ["-- choose or add new --"] + subcats + ["<Add new subcategory>"]
        chosen_sub = st.selectbox("Subcategory", options=sub_options, index=0)
        new_sub = None
        if chosen_sub == "<Add new subcategory>":
            new_sub = st.text_input("New subcategory name")
            sub_value = new_sub.strip() if new_sub else ""
        elif chosen_sub == "-- choose or add new --":
            sub_value = ""
        else:
            sub_value = chosen_sub

        description = st.text_input("Description", value="")
        budgeted = st.number_input("Budgeted", value=0.0, step=1.0, format="%.2f")
        actual = st.number_input("Actual", value=0.0, step=1.0, format="%.2f")
        account = st.text_input("Account", value="")
        notes = st.text_area("Notes", value="")

        submitted = st.form_submit_button("Save entry")
        if submitted:
            # Validate month format (simple)
            if len(month) != 7 or month[4] != "-" or not (month[:4].isdigit() and month[5:].isdigit()):
                st.error("Month must be in YYYY-MM format.")
            else:
                entry = {
                    "entry_type": entry_type,
                    "date": str(date_input) if date_input else None,
                    "month": month,
                    "category": category_value,
                    "subcategory": sub_value,
                    "description": description,
                    "budgeted": float(budgeted) if budgeted is not None else 0.0,
                    "actual": float(actual) if actual is not None else 0.0,
                    "account": account,
                    "notes": notes,
                }
                insert_entry(entry)
                st.success("Entry added to the database.")


def view_edit_tab():
    st.header("View and Edit Entries")

    # --- Filters ---
    conn = get_conn()
    all_months = pd.read_sql_query(f"SELECT DISTINCT month FROM {TABLE_NAME} ORDER BY month DESC", conn)["month"].tolist()
    conn.close()

    month_filter = st.selectbox("Filter by month (optional)", options=["-- all --"] + (all_months or []))
    categories, subcategories = fetch_distinct_categories_subcategories()
    category_filter = st.selectbox("Filter by category (optional)", options=["-- all --"] + (categories or []))
    subcategory_filter = st.selectbox("Filter by subcategory (optional)", options=["-- all --"] + (sorted({sc for _, sc in subcategories}) or []))
    entry_type_filter = st.selectbox("Filter by entry type", options=["-- all --", "budget", "income"])

    month_val = None if month_filter == "-- all --" else month_filter
    cat_val = None if category_filter == "-- all --" else category_filter
    subcat_val = None if subcategory_filter == "-- all --" else subcategory_filter
    et_val = None if entry_type_filter == "-- all --" else entry_type_filter

    df = fetch_entries(month=month_val, category=cat_val, subcategory=subcat_val, entry_type=et_val)

    if df.empty:
        st.info("No entries found for the selected filters.")
        return

    st.write("Edit values inline and click 'Save changes' to commit.")

    # --- Editable Table with dropdowns for category/subcategory ---
    editable_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=sorted(set(categories)),
                help="Select an existing category or edit manually",
            ),
            "subcategory": st.column_config.SelectboxColumn(
                "Subcategory",
                options=sorted({sc for _, sc in subcategories}),
                help="Select an existing subcategory or edit manually",
            ),
            "entry_type": st.column_config.SelectboxColumn(
                "Entry Type",
                options=["budget", "income"],
            ),
        },
        disabled=["id"],  # prevent editing the primary key
    )

    # --- Detect Changes ---
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
    st.write(f"{len(changed_rows)} edited row(s).")

    if not changed_rows.empty:
        if st.button("Save changes"):
            to_update = changed_rows[[
                "month_new","entry_type_new","date_new","category_new","subcategory_new",
                "description_new","budgeted_new","actual_new","account_new","notes_new","id"
            ]].copy()
            to_update.columns = ["month","entry_type","date","category","subcategory",
                                 "description","budgeted","actual","account","notes","id"]
            updated = bulk_update_rows(to_update)
            st.success(f"Updated {updated} rows.")
            st.experimental_rerun()

    # --- Delete Rows ---
    st.write("---")
    st.write("Delete rows (select IDs to delete):")
    ids = st.multiselect("Select IDs to delete", options=df["id"].tolist())
    if ids and st.button("Delete selected"):
        deleted = bulk_delete_by_id(ids)
        st.success(f"Deleted {deleted} rows.")
        st.experimental_rerun()


def summary_tab():

    # Reuse your summarize_db pipeline but simplified inline for quick preview
    df = fetch_entries()
    if df.empty:
        st.info("No data for summary.")
        return

    # Transform to grouped format similar to summarize_db.py
    df["budgeted"] = pd.to_numeric(df["budgeted"], errors="coerce").fillna(0.0)
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0.0)
    df_budget = df[df["entry_type"] == "budget"]
    df_income = df[df["entry_type"] == "income"]

    grouped = df_budget.groupby(["month", "category"]).agg(Actual_total=("actual", "sum")).reset_index()
    income = df_income.groupby("month").agg(Income_total=("actual", "sum")).reset_index()

    month_totals = grouped.groupby("month").sum()[["Actual_total"]].reset_index()
    month_totals = month_totals.merge(income, on="month", how="left").fillna(0)
    month_totals["Balance"] = month_totals["Income_total"] - month_totals["Actual_total"]

    st.subheader("Monthly totals")
    st.dataframe(month_totals.sort_values("month", ascending=False).reset_index(drop=True), use_container_width=True)

    st.subheader("Category totals (latest months)")
    cat_totals = grouped.groupby("category")["Actual_total"].sum().sort_values(ascending=False)
    st.table(cat_totals.reset_index().rename(columns={0:"Actual_total"}))


# ----------------- App -----------------

def main():
    st.set_page_config(page_title="Budget Manager", layout="wide")
    st.title("💰 Budget Manager")

    # --- Tabs ---
    tabs = st.tabs(["➕ Add Entry", "📋 View/Edit Entries", "📈 Summary"])

    with tabs[0]:
        st.header("Add a new budget/expense entry")
        add_entry_form()  # your existing form function

    with tabs[1]:
        st.header("View and Edit Entries")
        view_edit_tab()   # your existing view/edit function

    with tabs[2]:
        st.header("Summary")
        summary_tab()     # your existing summary function

    # --- Sidebar: Quit Button ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Danger Zone ⚠️")
    st.sidebar.markdown("Stops the Streamlit server safely")
    st.sidebar.info("Use this button to safely stop the app. Make sure to save changes before quitting.")

    if st.sidebar.button("Quit App"):
        st.sidebar.warning("Stopping Streamlit server...")
        os.kill(os.getpid(), signal.SIGINT)

if __name__ == "__main__":
    main()
