import streamlit as st
from utils.bedrock_client import get_available_models
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(
    page_title="Prompt Engineering Workshop",
    page_icon="🧠",
    layout="wide",
)
apply_custom_styles()

# 70/30 layout
main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🧠 Prompt Engineering Workshop")
    st.markdown("**Live Demo — Best Practices for Generative & Agentic AI**")
    st.caption("Reference: [promptingguide.ai](https://www.promptingguide.ai/)")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("**📋 Duration**")
            st.markdown("90 minutes")
    with col2:
        with st.container(border=True):
            st.markdown("**🧩 Sections**")
            st.markdown("7 topics")
    with col3:
        with st.container(border=True):
            st.markdown("**🤖 Platform**")
            st.markdown("Amazon Bedrock")

    st.markdown("")

    with st.container(border=True):
        st.markdown("#### 📋 Agenda")
        st.markdown("""
| # | Topic | Time |
|---|-------|------|
| 1 | Foundations & LLM Settings | 15 min |
| 2 | Zero-Shot & Few-Shot Prompting | 15 min |
| 3 | Chain-of-Thought & Reasoning | 15 min |
| 4 | Advanced Techniques | 15 min |
| 5 | Agentic Prompting & Tool Use | 15 min |
| 6 | Safety & Adversarial Prompting | 10 min |
| 7 | Multimodal & RAG Prompting | 10 min |
""")

    st.markdown("")

    with st.container(border=True):
        st.markdown("#### 🔑 Key Takeaways")
        st.markdown("""
1. **Prompt structure matters more than length**
2. **Techniques build on each other** — zero-shot → few-shot → CoT → agents
3. **Agentic AI = prompting + tool use + planning loops**
4. **Always consider safety** — adversarial robustness is not optional
""")

    st.markdown("")

    with st.container(border=True):
        st.markdown("#### 🚀 Getting Started")
        st.markdown("""
1. Select your **Model** and adjust **Inference Config** on the right panel
2. Navigate through the **pages** in the sidebar
3. Each page uses **tabs** to separate sub-topics
4. All examples are editable — try your own prompts
""")
        st.info("Make sure your AWS credentials are configured with access to Amazon Bedrock.")
