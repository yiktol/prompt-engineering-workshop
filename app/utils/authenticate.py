"""Authentication utilities for the Prompt Engineering Workshop."""

import streamlit as st
import os

_MODULE_NUMBER = 4
os.environ.setdefault("MODULE_NUMBER", str(_MODULE_NUMBER))


def login() -> bool:
    """Handle user authentication.

    Returns True if the user is authenticated, False otherwise.
    When running locally (localhost), authentication is bypassed.
    """
    if st.session_state.get("authenticated"):
        return True

    st.sidebar.markdown("### 🔐 Authentication")

    if "auth_token" not in st.session_state:
        with st.sidebar.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if username and password:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_token"] = "authenticated"
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Please enter both username and password.")
        return False

    return st.session_state.get("authenticated", False)
