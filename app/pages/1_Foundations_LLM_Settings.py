import streamlit as st
from utils.bedrock_client import invoke_model
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Foundations & LLM Settings", page_icon="🎛️", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🎛️ Foundations & LLM Settings")
    st.markdown("Understanding prompt structure and how LLM parameters affect output.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📝 Prompt Elements", "🌡️ Temperature Effect", "💡 General Tips"])

    # --- Tab 1: Prompt Elements ---
    with tab1:
        st.markdown("""
A prompt is composed of **four elements**:
- **Instruction** — The task you want the model to perform
- **Context** — Background information to guide the response
- **Input Data** — The specific question or data to process
- **Output Indicator** — The desired format or type of response
""")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**❌ Vague Prompt**")
            vague_prompt = st.text_area(
                "Vague", value="Tell me about AI.",
                height=80, key="vague", label_visibility="collapsed",
            )
        with col2:
            st.markdown("**✅ Structured Prompt**")
            structured_prompt = st.text_area(
                "Structured",
                value="Instruction: Explain the concept in simple terms for a non-technical audience.\nContext: You are a tech educator writing for a blog.\nInput: What is prompt engineering?\nOutput: A 3-sentence explanation.",
                height=120, key="structured", label_visibility="collapsed",
            )
        if st.button("Compare Both", key="compare_elements"):
            col1, col2 = st.columns(2)
            with col1:
                with st.spinner("Running vague prompt..."):
                    st.write(invoke_model(vague_prompt))
            with col2:
                with st.spinner("Running structured prompt..."):
                    st.write(invoke_model(structured_prompt))

    # --- Tab 2: Temperature Effect ---
    with tab2:
        st.markdown("""
| Parameter | Effect |
|-----------|--------|
| **Temperature** | Lower = deterministic, Higher = creative |
| **Top-P** | Nucleus sampling diversity (not all models support both) |
| **Max Tokens** | Maximum response length |
""")
        prompt_for_params = st.text_area(
            "Prompt to test with different temperatures:",
            value="Write a short poem about cloud computing.",
            height=80, key="param_prompt",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            temp_low = st.slider("Temp (Left)", 0.0, 1.0, 0.1, 0.1, key="temp_low")
        with col2:
            temp_mid = st.slider("Temp (Center)", 0.0, 1.0, 0.5, 0.1, key="temp_mid")
        with col3:
            temp_high = st.slider("Temp (Right)", 0.0, 1.0, 1.0, 0.1, key="temp_high")

        if st.button("Run with All Three", key="run_params"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Temp={temp_low}**")
                with st.spinner("..."):
                    st.write(invoke_model(prompt_for_params, temperature=temp_low))
            with col2:
                st.markdown(f"**Temp={temp_mid}**")
                with st.spinner("..."):
                    st.write(invoke_model(prompt_for_params, temperature=temp_mid))
            with col3:
                st.markdown(f"**Temp={temp_high}**")
                with st.spinner("..."):
                    st.write(invoke_model(prompt_for_params, temperature=temp_high))

    # --- Tab 3: General Tips ---
    with tab3:
        st.markdown("""
1. **Be specific and clear** — Avoid ambiguity in your instructions
2. **Use delimiters** — Separate sections with `###`, `---`, or XML tags
3. **Specify the output format** — JSON, bullet points, table, etc.
4. **Provide an "out"** — Tell the model to say "I don't know" if unsure
5. **Start with the instruction** — Put the task first, context second
""")
        tip_example = st.selectbox(
            "Try a tip:", ["Be specific", "Use delimiters", "Specify output format"], key="tip_sel"
        )
        tip_prompts = {
            "Be specific": (
                "Summarize the text.",
                "Summarize the following text in exactly 2 bullet points, focusing on the main argument:\n\n###\nArtificial intelligence is transforming healthcare by enabling faster diagnosis, personalized treatment plans, and drug discovery. However, challenges remain around data privacy, algorithmic bias, and the need for human oversight in clinical decisions.\n###",
            ),
            "Use delimiters": (
                "Translate this: Hello how are you I want to translate this to French",
                "Translate the text between the <text> tags to French.\n\n<text>\nHello, how are you? I hope you are having a great day.\n</text>\n\nOutput only the translation, nothing else.",
            ),
            "Specify output format": (
                "List some programming languages and what they're used for",
                'List 5 programming languages with their primary use case.\n\nRespond in JSON format:\n```json\n[\n  {"language": "...", "use_case": "..."}\n]\n```',
            ),
        }
        bad_prompt, good_prompt = tip_prompts[tip_example]
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("❌ Without tip", value=bad_prompt, height=120, key="bad_tip", disabled=True)
        with col2:
            st.text_area("✅ With tip", value=good_prompt, height=120, key="good_tip", disabled=True)
        if st.button("Compare", key="compare_tips"):
            col1, col2 = st.columns(2)
            with col1:
                with st.spinner("..."):
                    st.write(invoke_model(bad_prompt))
            with col2:
                with st.spinner("..."):
                    st.write(invoke_model(good_prompt))
