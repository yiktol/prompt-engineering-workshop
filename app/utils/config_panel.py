import streamlit as st
from utils.bedrock_client import get_available_models


def render_config_panel(container):
    """Render model selection and inference configuration in the given container."""
    with container:
        # --- Model Selection Container ---
        with st.container(border=True):
            st.markdown("##### 🤖 Model")
            models = get_available_models()
            selected_model_name = st.selectbox(
                "Model",
                list(models.keys()),
                index=0,
                key="config_model",
                label_visibility="collapsed",
            )
            st.session_state["selected_model_id"] = models[selected_model_name]
            st.session_state["selected_model_name"] = selected_model_name

            region = st.selectbox(
                "Region",
                ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
                index=0,
                key="config_region",
                label_visibility="collapsed",
            )
            st.session_state["aws_region"] = region

            # Clear cached client if region changes
            if "bedrock_client" in st.session_state:
                prev_region = st.session_state.get("_prev_region")
                if prev_region and prev_region != region:
                    del st.session_state["bedrock_client"]
            st.session_state["_prev_region"] = region

            st.caption(f"`{models[selected_model_name]}`")

        # --- Inference Config Container ---
        with st.container(border=True):
            st.markdown("##### 🎛️ Inference Config")

            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                key="config_temperature",
                help="Controls randomness. Lower = deterministic, Higher = creative.",
            )
            st.session_state["inference_temperature"] = temperature

            max_tokens = st.slider(
                "Max Tokens",
                min_value=64,
                max_value=4096,
                value=1024,
                step=64,
                key="config_max_tokens",
                help="Maximum length of the generated response.",
            )
            st.session_state["inference_max_tokens"] = max_tokens

            top_p = st.slider(
                "Top-P",
                min_value=0.0,
                max_value=1.0,
                value=0.9,
                step=0.05,
                key="config_top_p",
                help="Nucleus sampling. Not all models support both Temperature and Top-P.",
            )
            st.session_state["inference_top_p"] = top_p

            use_top_p = st.checkbox(
                "Include Top-P in request",
                value=False,
                key="config_use_top_p",
                help="Some models (e.g. DeepSeek-R1) reject both temperature and top_p.",
            )
            st.session_state["inference_use_top_p"] = use_top_p
