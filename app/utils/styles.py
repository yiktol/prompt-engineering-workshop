"""Styles and UI components for the Prompt Engineering Workshop."""

import streamlit as st

AWS_COLORS = {
    "orange": "#FF9900",
    "dark_blue": "#232F3E",
    "light_blue": "#0073BB",
    "white": "#FFFFFF",
    "gray": "#687078",
    "light_gray": "#F2F3F3",
}


def load_css():
    """Inject custom CSS for the workshop app."""
    st.markdown(
        """
        <style>
        .stApp {
            font-family: 'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        h1, h2, h3 {
            color: #232F3E;
        }
        .stButton>button {
            background-color: #FF9900;
            color: #232F3E;
            border: none;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #EC7211;
            color: white;
        }
        [data-testid="stMetric"] {
            border: 1px solid #e0e0e0;
            border-radius: 0;
            padding: 1rem;
            background-color: #fafafa;
        }
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def custom_header(title: str, subtitle: str = "", icon: str = "✍️") -> str:
    """Return HTML for a styled page header."""
    subtitle_html = (
        f"<p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;'>{subtitle}</p>"
        if subtitle
        else ""
    )
    return (
        f"<div style='background: linear-gradient(135deg, #232F3E 0%, #0073BB 50%, #FF9900 100%); "
        f"padding: 2.5rem; border-radius: 1rem; margin-bottom: 2rem; "
        f"box-shadow: 0 10px 30px rgba(0,0,0,0.15);'>"
        f"<h1 style='color: #FF9900; margin: 0; font-size: 2rem;'>{icon} {title}</h1>"
        f"{subtitle_html}"
        f"</div>"
    )


def sub_header(title: str, icon: str = "📌") -> str:
    """Return HTML for a styled sub-page header."""
    return (
        f"<div style='background: linear-gradient(135deg, #232F3E 0%, #0073BB 100%); "
        f"padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 1.5rem;'>"
        f"<h2 style='color: #FF9900; margin: 0;'>{icon} {title}</h2>"
        f"</div>"
    )


def create_footer():
    """Render a styled footer."""
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem 0; color: #687078; font-size: 0.85rem;'>
            <hr style='border: none; border-top: 1px solid #eee; margin-bottom: 1rem;'/>
            © 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )
