import streamlit as st
from components.quit_botton import quit_button
from core.db import ensure_db_exists

ensure_db_exists()

st.set_page_config(page_title="Budget Manager", layout="wide")
st.title("💰 Budget Manager")

st.write("""
Use the sidebar or top navigation to access:
- **Add Entry**
- **View/Edit Entries**
- **Summary**
- **Reports**
""")

quit_button()
