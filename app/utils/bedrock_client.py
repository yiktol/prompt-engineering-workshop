import boto3
import json
import streamlit as st


def get_bedrock_client():
    """Get or create a Bedrock Runtime client."""
    if "bedrock_client" not in st.session_state:
        region = st.session_state.get("aws_region", "us-east-1")
        st.session_state.bedrock_client = boto3.client(
            "bedrock-runtime", region_name=region
        )
    return st.session_state.bedrock_client


def get_available_models():
    """Return a dict of model display names to model IDs.

    All models listed here support the Amazon Bedrock Converse API.
    Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html
    """
    return {
        # Anthropic — use inference profile IDs (us. prefix)
        "Claude Sonnet 4.6": "us.anthropic.claude-sonnet-4-6",
        "Claude Sonnet 4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        # Amazon — on-demand supported directly
        "Amazon Nova Pro": "amazon.nova-pro-v1:0",
        "Amazon Nova Lite": "amazon.nova-lite-v1:0",
        "Amazon Nova Micro": "amazon.nova-micro-v1:0",
        # Meta — use inference profile IDs (us. prefix)
        "Llama 4 Scout 17B": "us.meta.llama4-scout-17b-instruct-v1:0",
        "Llama 4 Maverick 17B": "us.meta.llama4-maverick-17b-instruct-v1:0",
        # Mistral — on-demand supported directly
        "Mistral Large 3": "mistral.mistral-large-3-675b-instruct",
        # DeepSeek — use inference profile ID
        "DeepSeek-R1": "us.deepseek.r1-v1:0",
    }


def invoke_model(
    prompt: str,
    system_prompt: str = "",
    model_id: str = None,
    temperature: float = None,
    top_p: float = None,
    max_tokens: int = None,
) -> str:
    """Invoke a Bedrock model using the Converse API."""
    client = get_bedrock_client()

    if model_id is None:
        model_id = st.session_state.get(
            "selected_model_id", "amazon.nova-lite-v1:0"
        )

    # Use session state defaults from config panel if not explicitly provided
    if temperature is None:
        temperature = st.session_state.get("inference_temperature", 0.7)
    if max_tokens is None:
        max_tokens = st.session_state.get("inference_max_tokens", 1024)
    if top_p is None and st.session_state.get("inference_use_top_p", False):
        top_p = st.session_state.get("inference_top_p", 0.9)

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    inference_config = {
        "temperature": temperature,
        "maxTokens": max_tokens,
    }

    # Some models (e.g. DeepSeek-R1) don't allow both temperature and topP.
    # Only include topP when explicitly provided.
    if top_p is not None:
        inference_config["topP"] = top_p

    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": inference_config,
    }

    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    try:
        response = client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]
    except Exception as e:
        return f"❌ Error: {str(e)}"


def invoke_model_with_tools(
    prompt: str,
    system_prompt: str = "",
    tools: list = None,
    model_id: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict:
    """Invoke a Bedrock model with tool definitions (function calling)."""
    client = get_bedrock_client()

    if model_id is None:
        model_id = st.session_state.get(
            "selected_model_id", "amazon.nova-lite-v1:0"
        )

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"temperature": temperature, "maxTokens": max_tokens},
    }

    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    if tools:
        kwargs["toolConfig"] = {"tools": tools}

    try:
        response = client.converse(**kwargs)
        return response
    except Exception as e:
        return {"error": str(e)}
