import streamlit as st
from components.quit_botton import quit_button
from core.db import (
    ensure_db_exists,
    seed_sample_data,
    fetch_entries,
)

# -------------------------------
# Initialize database
# -------------------------------
# 1️⃣ Ensure folder and table exist
ensure_db_exists()

# 2️⃣ Only seed if empty
try:
    if fetch_entries().empty:
        seed_sample_data()
except Exception as e:
    # Likely database file missing; create & seed
    seed_sample_data()

# -------------------------------
# Streamlit page setup
# -------------------------------
st.set_page_config(page_title="Budget Manager", layout="wide")
st.title("💰 Budget Manager")

st.write("""
Use the sidebar or top navigation to access:
- **Add Entry**
- **View/Edit Entries**
- **Summary**
""")

# -------------------------------
# Admin controls
# -------------------------------
quit_button()
