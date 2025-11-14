import streamlit as st
from components.quit_botton import quit_button
from core.db import ensure_db_exists

# -------------------------------
# Initialize database
# -------------------------------
# Just ensure the folder & table exist
ensure_db_exists()

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
