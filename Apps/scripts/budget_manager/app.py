import streamlit as st
from components.quit_botton import quit_button
from core.db import (
    ensure_db_exists,
    seed_sample_data,
    fetch_entries,
)


# Ensure DB & table exist first
ensure_db_exists()

# Optionally seed sample data only if database is empty
if fetch_entries().empty:
    seed_sample_data()

st.set_page_config(page_title="Budget Manager", layout="wide")
st.title("💰 Budget Manager")

st.write("""
Use the sidebar or top navigation to access:
- **Add Entry**
- **View/Edit Entries**
- **Summary**
""")

quit_button()