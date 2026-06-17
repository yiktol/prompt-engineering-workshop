import streamlit as st
import uuid
from utils.styles import load_css, custom_header, create_footer, AWS_COLORS
from utils.common import render_sidebar
import utils.authenticate as authenticate

st.set_page_config(
    page_title="AWS AI Practitioner - Essentials of Prompt Engineering",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def main():
    load_css()

    with st.sidebar:
        render_sidebar()
        if st.button("🗑️ Reset All Labs", key="home_clear_all"):
            # Clear all session state except session_id and auth
            keys_to_keep = {"session_id", "authenticated", "auth_token", "username"}
            keys_to_clear = [k for k in list(st.session_state.keys()) if k not in keys_to_keep]
            for key in keys_to_clear:
                del st.session_state[key]
            st.rerun()

    st.markdown("""
        <div style='background: linear-gradient(135deg, #232F3E 0%, #0073BB 50%, #FF9900 100%);
                    padding: 2.5rem; border-radius: 1rem; margin-bottom: 2rem;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.15);'>
            <h1 style='color: #FF9900; margin: 0; font-size: 2rem;'>
                ✍️ Essentials of Prompt Engineering
            </h1>
            <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;'>
                Master prompt construction, strategies, inference parameters, and prompt security.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📚 Interactive Labs")

    pages = [
        "🧱 Prompt Anatomy Builder",
        "🛡️ System Prompt Workshop",
        "⚖️ Strategy Comparison Lab",
        "🎛️ Parameter Playground",
        "🔴 Prompt Injection Red Team",
        "🔄 Iterative Refinement Lab",
    ]

    col1, col2 = st.columns(2)
    mid = (len(pages) + 1) // 2
    with col1:
        for i, page in enumerate(pages[:mid], 1):
            st.markdown(f"**{i}.** {page}")
    with col2:
        for i, page in enumerate(pages[mid:], mid + 1):
            st.markdown(f"**{i}.** {page}")

    create_footer()


if __name__ == "__main__":
    try:
        if "localhost" in st.context.headers.get("host", "localhost"):
            main()
        else:
            is_authenticated = authenticate.login()
            if is_authenticated:
                main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
