import streamlit as st
from data import db_utils

# Initialize DB on first run
db_utils.init_db()

st.set_page_config(page_title="Investment Manager", layout="wide")
st.title("Investment Manager 💹")

st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between pages.")
