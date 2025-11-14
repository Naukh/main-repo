import os
import signal
import streamlit as st

ADMIN_PASSWORD = "584483" 

def quit_button():
    st.markdown("---")
    st.subheader("🔥 Danger Zone (Admin Only)")

    # ------------------------------------
    # SAFE user-agent detection
    # ------------------------------------
    try:
        user_agent = st.context.headers.get("User-Agent", "")
    except Exception:
        user_agent = ""  # fallback for older Streamlit

    def is_mobile(ua: str) -> bool:
        mobile_terms = ["iPhone", "Android", "Mobile"]
        return any(term in ua for term in mobile_terms)

    if is_mobile(user_agent):
        st.info("Admin controls hidden on mobile to prevent accidental taps.")
        return

    # ------------------------------------
    # Password check
    # ------------------------------------
    pw = st.text_input("Enter admin password:", type="password")
    if pw != ADMIN_PASSWORD:
        st.info("Enter password to unlock admin controls.")
        return

    st.success("Admin mode unlocked.")

    if "confirm_quit" not in st.session_state:
        st.session_state.confirm_quit = False

    # ------------------------------------
    # Quit button
    # ------------------------------------
    if st.button("Quit App"):
        st.session_state.confirm_quit = True

    # Quit confirmation
    if st.session_state.confirm_quit:
        st.error("⚠️ Are you sure you want to **QUIT** the app?")
        q1, q2 = st.columns(2)

        with q1:
            if st.button("Yes, Quit Now"):
                st.warning("Stopping Streamlit server...")
                os.kill(os.getpid(), signal.SIGINT)

        with q2:
            if st.button("Cancel Quit"):
                st.session_state.confirm_quit = False
