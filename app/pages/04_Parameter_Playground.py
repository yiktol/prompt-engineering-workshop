import streamlit as st
import boto3
import time
import json
import plotly.graph_objects as go
from utils.styles import load_css, sub_header, create_footer, AWS_COLORS
from utils.common import render_sidebar, render_generator_model_selector, get_generator_model_id


st.set_page_config(page_title="Parameter Playground", page_icon="🎛️", layout="wide")

@st.cache_resource
def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Preset prompts designed to highlight parameter effects
# ---------------------------------------------------------------------------
PRESET_PROMPTS = {
    "Creative tagline": {
        "prompt": "Write a creative one-sentence tagline for a coffee shop that also sells books.",
        "tip": "Try varying temperature to see how creativity changes. Low = safe and generic, High = unexpected and novel.",
    },
    "Factual definition": {
        "prompt": "Define photosynthesis in exactly one sentence.",
        "tip": "Factual tasks benefit from low temperature (0.0-0.2). Higher values may introduce inaccuracies.",
    },
    "Code generation": {
        "prompt": "Write a Python function that checks if a string is a palindrome.",
        "tip": "Code needs precision. Temperature > 0.5 may produce creative but buggy variations.",
    },
    "Long-form explanation": {
        "prompt": "Explain how a neural network learns, step by step, in detail.",
        "tip": "Use this to see max_tokens truncation. Try 100 vs 500 to see how it cuts off mid-thought.",
    },
    "Story opening": {
        "prompt": "Write the opening paragraph of a mystery novel set in a lighthouse.",
        "tip": "Creative writing shows the most dramatic difference between temperature 0.0 and 1.0.",
    },
    "List generation": {
        "prompt": "List 5 unusual uses for a paperclip.",
        "tip": "Top_p has a strong effect here. Low top_p = predictable ideas, High top_p = surprising ones.",
    },
}

# ---------------------------------------------------------------------------
# Parameter tips
# ---------------------------------------------------------------------------
PARAMETER_TIPS = {
    "Temperature": {
        "what": "Controls randomness by flattening the token probability distribution",
        "how": "At 0.0, always picks the most likely token. At 1.0, all tokens have more equal probability.",
        "range": "0.0 (deterministic) → 1.0 (maximum randomness)",
        "use_low": "Factual Q&A, code, data extraction, classification",
        "use_high": "Creative writing, brainstorming, diverse outputs",
    },
    "Top P (Nucleus Sampling)": {
        "what": "Limits token selection to the smallest set whose cumulative probability exceeds P",
        "how": "At 0.1, only considers the top 10% probability mass. At 1.0, considers all tokens.",
        "range": "0.0 (only top token) → 1.0 (all tokens eligible)",
        "use_low": "Focused, predictable outputs",
        "use_high": "Diverse vocabulary, creative phrasing",
    },
    "Max Tokens": {
        "what": "Hard cap on the number of output tokens generated",
        "how": "Generation stops immediately when this limit is reached, even mid-sentence.",
        "range": "1 → model maximum (varies by model)",
        "use_low": "Short answers, one-liners, cost control",
        "use_high": "Long explanations, detailed code, essays",
    },
}

# ---------------------------------------------------------------------------
# Challenge mode
# ---------------------------------------------------------------------------
CHALLENGES = {
    "Deterministic Output": {
        "description": "Get the model to produce the EXACT same response on 3 consecutive runs.",
        "prompt": "What is the capital of France?",
        "check": "deterministic",
        "hint": "Which parameter makes outputs completely predictable?",
    },
    "Maximum Creativity": {
        "description": "Get 3 runs to produce highly varied responses (Jaccard distance > 0.6).",
        "prompt": "Invent a name for a new color that doesn't exist yet.",
        "check": "creative",
        "hint": "Which parameters maximize randomness in token selection?",
    },
    "Precise Length Control": {
        "description": "Get the model to produce a response of EXACTLY 20-30 words (no more, no less).",
        "prompt": "Describe the ocean in exactly 25 words.",
        "check": "length",
        "hint": "Max tokens can cap output, but the instruction itself matters too. What max_tokens ensures ~25 words?",
    },
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def call_bedrock(prompt, temperature=0.7, top_p=0.9, max_tokens=200):
    client = get_bedrock_client()
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    inference_config = {
        "temperature": temperature,
        "topP": top_p,
        "maxTokens": max_tokens,
    }
    try:
        start = time.time()
        response = client.converse(
            modelId=get_generator_model_id(),
            messages=messages,
            inferenceConfig=inference_config,
        )
        latency = time.time() - start
        output_text = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        return {
            "text": output_text,
            "input_tokens": usage.get("inputTokens", 0),
            "output_tokens": usage.get("outputTokens", 0),
            "latency": latency,
        }
    except Exception as e:
        return {"text": f"Error: {str(e)}", "input_tokens": 0, "output_tokens": 0, "latency": 0}


def jaccard_distance(text1, text2):
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 and not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    if not union:
        return 0.0
    return 1.0 - (len(intersection) / len(union))


def avg_jaccard(responses):
    if len(responses) < 2:
        return 0.0
    distances = []
    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            distances.append(jaccard_distance(responses[i], responses[j]))
    return sum(distances) / len(distances) if distances else 0.0


def render_probability_chart(temperature):
    """Render a conceptual token probability distribution chart."""
    import math
    # Simulate softmax with temperature on 5 hypothetical tokens
    raw_logits = [2.0, 1.5, 1.0, 0.5, 0.2]
    labels = ["Token A\n(most likely)", "Token B", "Token C", "Token D", "Token E\n(least likely)"]

    if temperature == 0:
        probs = [1.0, 0.0, 0.0, 0.0, 0.0]
    else:
        scaled = [l / max(temperature, 0.01) for l in raw_logits]
        exp_scaled = [math.exp(s) for s in scaled]
        total = sum(exp_scaled)
        probs = [e / total for e in exp_scaled]

    fig = go.Figure(data=[
        go.Bar(x=labels, y=probs, marker_color=["#FF9900" if p == max(probs) else "#0073BB" for p in probs])
    ])
    fig.update_layout(
        title=f"Token Selection Probability (temp={temperature:.1f})",
        yaxis_title="Probability",
        yaxis=dict(range=[0, 1.05]),
        height=250,
        margin=dict(t=40, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    load_css()

    with st.sidebar:
        render_sidebar()
        render_generator_model_selector()
        if st.button("🗑️ Clear All", key="pp_clear_all"):
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("pp_")]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown(sub_header("Parameter Playground", icon="🎛️"), unsafe_allow_html=True)
    st.markdown(
        "**Key Concept:** Inference parameters (temperature, top_p, max_tokens) control "
        "how tokens are selected during generation. They affect creativity and variability, "
        "not the model's underlying knowledge."
    )

    # --- Parameter tips ---
    with st.expander("💡 Parameter Reference Guide", expanded=False):
        tips_cols = st.columns(3)
        for i, (param, info) in enumerate(PARAMETER_TIPS.items()):
            with tips_cols[i]:
                st.markdown(f"**{param}**")
                st.markdown(f"*What:* {info['what']}")
                st.markdown(f"*How:* {info['how']}")
                st.markdown(f"*Range:* {info['range']}")
                st.markdown(f"✅ Use low: {info['use_low']}")
                st.markdown(f"🎨 Use high: {info['use_high']}")

    # --- Prompt selection ---
    def _on_preset_change():
        p = st.session_state.get("pp_preset", "Custom")
        if p != "Custom" and p in PRESET_PROMPTS:
            st.session_state["pp_prompt"] = PRESET_PROMPTS[p]["prompt"]

    preset = st.selectbox(
        "Load preset prompt:",
        ["Custom"] + list(PRESET_PROMPTS.keys()),
        key="pp_preset",
        on_change=_on_preset_change,
    )

    if preset != "Custom" and preset in PRESET_PROMPTS:
        st.caption(f"💡 {PRESET_PROMPTS[preset]['tip']}")

    if "pp_prompt" not in st.session_state:
        st.session_state["pp_prompt"] = PRESET_PROMPTS[list(PRESET_PROMPTS.keys())[0]]["prompt"]

    prompt = st.text_area("Enter your prompt:", height=80, key="pp_prompt")

    # --- Parameters ---
    st.markdown("### ⚙️ Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="pp_temp")
    with col2:
        top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.05, key="pp_top_p")
    with col3:
        max_tokens = st.slider("Max Tokens", 50, 1000, 200, 50, key="pp_max_tokens")

    # Contextual hints
    if temperature < 0.3:
        st.info("🎯 **Low temperature (< 0.3):** Focused and deterministic. Good for factual/precise tasks.")
    elif temperature < 0.7:
        st.info("⚖️ **Medium temperature (0.3-0.7):** Balanced creativity and consistency.")
    else:
        st.info("🎨 **High temperature (> 0.7):** Creative and varied. Good for brainstorming.")

    if temperature > 0.5 and top_p < 0.5:
        st.warning(
            "⚠️ **Parameter conflict:** High temperature broadens the distribution, but low top_p cuts it back. "
            "These work against each other. Adjust one at a time for predictable control."
        )

    # --- Probability visualization ---
    st.plotly_chart(render_probability_chart(temperature), use_container_width=True)

    # --- Tabs ---
    tab_experiment, tab_temp_compare, tab_topp_compare, tab_history, tab_challenge = st.tabs(
        ["🔬 Experiment", "🌡️ Temperature Compare", "🎯 Top-P Compare", "📈 History", "🎯 Challenge"]
    )

    with tab_experiment:
        num_runs = st.slider("Number of runs:", 1, 5, 3, key="pp_num_runs")
        if st.button("🚀 Run Experiment", type="primary", key="pp_run_exp"):
            if not prompt.strip():
                st.warning("Please enter a prompt.")
            else:
                results = []
                progress = st.progress(0)
                for i in range(num_runs):
                    with st.spinner(f"Run {i + 1}/{num_runs}..."):
                        r = call_bedrock(prompt, temperature, top_p, max_tokens)
                        results.append(r)
                    progress.progress((i + 1) / num_runs)
                st.session_state["pp_exp_results"] = results
                st.session_state["pp_exp_params"] = {
                    "temperature": temperature, "top_p": top_p, "max_tokens": max_tokens
                }

                # Save to history
                if "pp_history" not in st.session_state:
                    st.session_state["pp_history"] = []
                response_texts = [r["text"] for r in results if not r["text"].startswith("Error")]
                variability = avg_jaccard(response_texts) if len(response_texts) >= 2 else 0
                avg_tokens = sum(r["output_tokens"] for r in results) / len(results) if results else 0
                st.session_state["pp_history"].append({
                    "prompt": prompt[:50],
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                    "variability": variability,
                    "avg_output_tokens": avg_tokens,
                    "num_runs": num_runs,
                })

        if "pp_exp_results" in st.session_state:
            results = st.session_state["pp_exp_results"]
            for i, r in enumerate(results):
                with st.expander(f"Run {i + 1}", expanded=(i == 0)):
                    st.markdown(r["text"])
                    st.caption(f"Tokens: {r['input_tokens']} in / {r['output_tokens']} out | Latency: {r['latency']:.2f}s")

            response_texts = [r["text"] for r in results if not r["text"].startswith("Error")]
            if len(response_texts) >= 2:
                variability = avg_jaccard(response_texts)
                st.markdown("---")
                st.markdown("### 📊 Variability Analysis")

                var_cols = st.columns(3)
                var_cols[0].metric("Jaccard Distance", f"{variability:.3f}", help="0 = identical, 1 = completely different")
                avg_len = sum(len(t) for t in response_texts) / len(response_texts)
                var_cols[1].metric("Avg Response Length", f"{avg_len:.0f} chars")
                avg_out = sum(r["output_tokens"] for r in results) / len(results)
                var_cols[2].metric("Avg Output Tokens", f"{avg_out:.0f}")

                if variability < 0.2:
                    st.success("Low variability — responses are very consistent.")
                elif variability < 0.5:
                    st.info("Moderate variability — some creative differences.")
                else:
                    st.warning("High variability — responses differ significantly.")

                # Length chart
                lengths = [len(r["text"]) for r in results]
                fig = go.Figure(data=[
                    go.Bar(x=[f"Run {i+1}" for i in range(len(lengths))], y=lengths, marker_color="#0073BB")
                ])
                fig.update_layout(title="Response Lengths (characters)", height=250, margin=dict(t=40, b=40))
                st.plotly_chart(fig, use_container_width=True)

    with tab_temp_compare:
        st.markdown("Runs the same prompt at 3 temperature settings to show the effect.")
        if st.button("🌡️ Run Temperature Compare", type="primary", key="pp_temp_compare"):
            if not prompt.strip():
                st.warning("Please enter a prompt.")
            else:
                temps = [0.0, 0.5, 1.0]
                compare_results = []
                with st.spinner("Running 3 calls at different temperatures..."):
                    for t in temps:
                        r = call_bedrock(prompt, temperature=t, top_p=top_p, max_tokens=max_tokens)
                        compare_results.append(r)
                st.session_state["pp_temp_results"] = compare_results

        if "pp_temp_results" in st.session_state:
            results = st.session_state["pp_temp_results"]
            temps = [0.0, 0.5, 1.0]
            labels = ["🧊 Temp=0.0", "⚖️ Temp=0.5", "🔥 Temp=1.0"]

            cols = st.columns(3)
            for i, (col, label) in enumerate(zip(cols, labels)):
                with col:
                    st.markdown(f"**{label}**")
                    st.markdown(results[i]["text"])
                    st.caption(f"{results[i]['output_tokens']} tokens | {results[i]['latency']:.2f}s")

            response_texts = [r["text"] for r in results if not r["text"].startswith("Error")]
            if len(response_texts) >= 2:
                st.markdown("---")
                variability = avg_jaccard(response_texts)
                st.metric("Cross-temperature Variability", f"{variability:.3f}")
                st.info("💡 Higher temperature typically produces more varied vocabulary and creative phrasing.")

    with tab_topp_compare:
        st.markdown("Runs the same prompt at 3 top_p settings (with temperature fixed) to show nucleus sampling effect.")
        if st.button("🎯 Run Top-P Compare", type="primary", key="pp_topp_compare"):
            if not prompt.strip():
                st.warning("Please enter a prompt.")
            else:
                top_ps = [0.1, 0.5, 1.0]
                compare_results = []
                with st.spinner("Running 3 calls at different top_p values..."):
                    for tp in top_ps:
                        r = call_bedrock(prompt, temperature=temperature, top_p=tp, max_tokens=max_tokens)
                        compare_results.append(r)
                st.session_state["pp_topp_results"] = compare_results

        if "pp_topp_results" in st.session_state:
            results = st.session_state["pp_topp_results"]
            top_ps = [0.1, 0.5, 1.0]
            labels = ["🎯 P=0.1 (narrow)", "⚖️ P=0.5 (moderate)", "🌐 P=1.0 (full)"]

            cols = st.columns(3)
            for i, (col, label) in enumerate(zip(cols, labels)):
                with col:
                    st.markdown(f"**{label}**")
                    st.markdown(results[i]["text"])
                    st.caption(f"{results[i]['output_tokens']} tokens | {results[i]['latency']:.2f}s")

            response_texts = [r["text"] for r in results if not r["text"].startswith("Error")]
            if len(response_texts) >= 2:
                st.markdown("---")
                variability = avg_jaccard(response_texts)
                st.metric("Cross-top_p Variability", f"{variability:.3f}")
                st.info(
                    "💡 Top_p controls how many tokens are 'eligible' for selection. "
                    "Low top_p = only the most probable tokens. High top_p = rare tokens can also be chosen."
                )

    with tab_history:
        history = st.session_state.get("pp_history", [])
        if history:
            st.markdown("#### Experiment Log")
            st.markdown("Track how different parameter settings affect output across experiments.")

            # Summary table
            table_data = []
            for i, h in enumerate(history, 1):
                table_data.append({
                    "#": i,
                    "Prompt": h["prompt"] + "...",
                    "Temp": h["temperature"],
                    "Top P": h["top_p"],
                    "Max Tokens": h["max_tokens"],
                    "Variability": f"{h['variability']:.3f}",
                    "Avg Output": f"{h['avg_output_tokens']:.0f}",
                })
            st.table(table_data)

            # Variability vs temperature scatter
            if len(history) >= 2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[h["temperature"] for h in history],
                    y=[h["variability"] for h in history],
                    mode="markers",
                    marker=dict(size=12, color="#FF9900"),
                    text=[h["prompt"] for h in history],
                    hovertemplate="Temp: %{x}<br>Variability: %{y:.3f}<br>%{text}",
                ))
                fig.update_layout(
                    title="Temperature vs Variability",
                    xaxis_title="Temperature",
                    yaxis_title="Jaccard Distance",
                    height=300,
                    margin=dict(t=40, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

            if st.button("🗑️ Clear History", key="pp_clear_history"):
                st.session_state["pp_history"] = []
                st.rerun()
        else:
            st.info("Run experiments to build your parameter history log.")

    with tab_challenge:
        st.markdown("#### 🎯 Parameter Challenge Mode")
        st.markdown("Achieve specific output behaviors using ONLY parameter adjustments.")

        challenge_name = st.selectbox(
            "Select a challenge:",
            list(CHALLENGES.keys()),
            key="pp_challenge_select",
        )
        challenge = CHALLENGES[challenge_name]

        st.markdown(f"**Goal:** {challenge['description']}")
        st.markdown(f"**Fixed prompt:** `{challenge['prompt']}`")
        with st.expander("💡 Hint"):
            st.markdown(challenge["hint"])

        st.markdown("---")
        st.markdown("#### Set your parameters:")
        ch_cols = st.columns(3)
        with ch_cols[0]:
            ch_temp = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="pp_ch_temp")
        with ch_cols[1]:
            ch_top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.05, key="pp_ch_top_p")
        with ch_cols[2]:
            ch_max_tokens = st.slider("Max Tokens", 20, 500, 200, 10, key="pp_ch_max_tokens")

        if st.button("🚀 Run Challenge (3 runs)", key="pp_run_challenge"):
            results = []
            with st.spinner("Running 3 times..."):
                for _ in range(3):
                    r = call_bedrock(challenge["prompt"], ch_temp, ch_top_p, ch_max_tokens)
                    results.append(r)
            st.session_state["pp_challenge_results"] = results

        if "pp_challenge_results" in st.session_state:
            results = st.session_state["pp_challenge_results"]
            response_texts = [r["text"] for r in results if not r["text"].startswith("Error")]

            # Show responses
            for i, r in enumerate(results):
                with st.expander(f"Run {i+1}", expanded=True):
                    st.markdown(r["text"])
                    word_count = len(r["text"].split())
                    st.caption(f"{r['output_tokens']} tokens | {word_count} words | {r['latency']:.2f}s")

            # Evaluate challenge
            st.markdown("---")
            passed = False
            if challenge["check"] == "deterministic":
                if len(response_texts) >= 3 and response_texts[0] == response_texts[1] == response_texts[2]:
                    passed = True
                    st.success("🎉 All 3 responses are identical! Challenge passed.")
                else:
                    variability = avg_jaccard(response_texts) if len(response_texts) >= 2 else 1
                    st.warning(f"Responses are not identical (variability: {variability:.3f}). Try lower temperature.")

            elif challenge["check"] == "creative":
                variability = avg_jaccard(response_texts) if len(response_texts) >= 2 else 0
                st.metric("Variability (Jaccard)", f"{variability:.3f}")
                if variability > 0.6:
                    passed = True
                    st.success(f"🎉 High variability ({variability:.3f} > 0.6)! Challenge passed.")
                else:
                    st.warning(f"Variability {variability:.3f} is below 0.6. Try higher temperature and top_p.")

            elif challenge["check"] == "length":
                word_counts = [len(t.split()) for t in response_texts]
                avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
                st.metric("Average Word Count", f"{avg_words:.0f}")
                if all(20 <= wc <= 30 for wc in word_counts):
                    passed = True
                    st.success(f"🎉 All responses are 20-30 words! Challenge passed.")
                else:
                    st.warning(f"Word counts: {word_counts}. Need all between 20-30. Adjust max_tokens and prompt framing.")

            if passed:
                st.markdown(f"✅ Parameters used: temp={ch_temp}, top_p={ch_top_p}, max_tokens={ch_max_tokens}")

    create_footer()



main()
