"""Common utilities for the Prompt Engineering Workshop."""

import streamlit as st

GENERATOR_MODELS = {
    "Amazon Nova Micro": "us.amazon.nova-micro-v1:0",
    "Amazon Nova 2 Lite": "us.amazon.nova-2-lite-v1:0",
    "Amazon Nova Pro": "us.amazon.nova-pro-v1:0",
    "Claude Sonnet 4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Claude Sonnet 4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "Llama 4 Scout 17B": "us.meta.llama4-scout-17b-instruct-v1:0",
    "Mistral Ministral 3B": "mistral.ministral-3-3b-instruct",
    "Google Gemma 3 4B": "google.gemma-3-4b-it",
    "OpenAI GPT OSS 20B": "openai.gpt-oss-20b-1:0",
    "NVIDIA Nemotron Nano 9B": "nvidia.nemotron-nano-9b-v2",
}

JUDGE_MODELS = {
    "Claude Sonnet 4.6": "us.anthropic.claude-sonnet-4-6",
    "Claude Sonnet 4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "Claude Sonnet 4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Claude Opus 4.8": "us.anthropic.claude-opus-4-8",
    "Claude Opus 4.7": "us.anthropic.claude-opus-4-7",
    "Amazon Nova Pro": "us.amazon.nova-pro-v1:0",
    "Amazon Nova Lite": "us.amazon.nova-lite-v1:0",
}

_DEFAULT_GENERATOR = "Amazon Nova Micro"
_DEFAULT_JUDGE = "Claude Sonnet 4.6"


def render_sidebar():
    """Render shared sidebar navigation elements."""
    pass


def render_generator_model_selector() -> str:
    """Render a model selector in the sidebar for the generator and return the model ID."""
    st.markdown("#### 🤖 Generator Model")
    selection = st.selectbox(
        "Select generator model:",
        list(GENERATOR_MODELS.keys()),
        index=list(GENERATOR_MODELS.keys()).index(_DEFAULT_GENERATOR),
        key="generator_model_selection",
    )
    return GENERATOR_MODELS[selection]


def get_generator_model_id() -> str:
    """Return the currently selected generator model ID from session state."""
    selection = st.session_state.get("generator_model_selection", _DEFAULT_GENERATOR)
    return GENERATOR_MODELS.get(selection, GENERATOR_MODELS[_DEFAULT_GENERATOR])


def render_judge_model_selector() -> str:
    """Render a model selector in the sidebar for the AI judge and return the model ID."""
    st.markdown("#### 🧑‍⚖️ Judge Model")
    selection = st.selectbox(
        "Select judge model:",
        list(JUDGE_MODELS.keys()),
        index=list(JUDGE_MODELS.keys()).index(_DEFAULT_JUDGE),
        key="judge_model_selection",
    )
    return JUDGE_MODELS[selection]


def get_judge_model_id() -> str:
    """Return the currently selected judge model ID from session state."""
    selection = st.session_state.get("judge_model_selection", _DEFAULT_JUDGE)
    return JUDGE_MODELS.get(selection, JUDGE_MODELS[_DEFAULT_JUDGE])
