import streamlit as st
from utils.bedrock_client import get_models_by_provider


def render_config_panel(container):
    """Render model selection and inference configuration in the given container."""
    with container:
        # --- Model Selection Container ---
        with st.container(border=True):
            st.markdown("##### 🤖 Model")
            models_by_provider = get_models_by_provider()
            providers = list(models_by_provider.keys())

            selected_provider = st.selectbox(
                "Provider",
                providers,
                index=0,
                key="config_provider",
            )

            provider_models = models_by_provider[selected_provider]
            selected_model_name = st.selectbox(
                "Model",
                list(provider_models.keys()),
                index=0,
                key=f"config_model_{selected_provider}",
            )
            st.session_state["selected_model_id"] = provider_models[selected_model_name]
            st.session_state["selected_model_name"] = selected_model_name

            # Default region (us-east-1) — no UI selector
            st.session_state["aws_region"] = "us-east-1"

            st.caption(f"`{provider_models[selected_model_name]}`")

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
