import streamlit as st
from utils.bedrock_client import invoke_model
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Chain-of-Thought & Reasoning", page_icon="🔗", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🔗 Chain-of-Thought & Reasoning")
    st.markdown("Encourage the model to break down problems into intermediate reasoning steps.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Standard vs CoT", "🆓 Zero-Shot CoT", "📚 Few-Shot CoT", "🗳️ Self-Consistency"
    ])

    # --- Tab 1: Standard vs CoT ---
    with tab1:
        st.markdown("Compare a direct prompt with one that asks the model to reason step by step.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**❌ Standard (Direct)**")
            standard_prompt = st.text_area(
                "Standard",
                value="A store sells apples for $2 each. If you buy 5 or more, you get a 20% discount.\nYou also have a $3 coupon. How much do you pay for 7 apples?\n\nAnswer:",
                height=140, key="standard", label_visibility="collapsed",
            )
        with col2:
            st.markdown("**✅ Chain-of-Thought**")
            cot_prompt = st.text_area(
                "CoT",
                value="A store sells apples for $2 each. If you buy 5 or more, you get a 20% discount.\nYou also have a $3 coupon. How much do you pay for 7 apples?\n\nLet's solve this step by step:",
                height=140, key="cot", label_visibility="collapsed",
            )
        if st.button("Compare Approaches", key="compare_cot"):
            col1, col2 = st.columns(2)
            with col1:
                with st.spinner("Standard..."):
                    st.write(invoke_model(standard_prompt, temperature=0.1))
            with col2:
                with st.spinner("CoT..."):
                    st.write(invoke_model(cot_prompt, temperature=0.1))

    # --- Tab 2: Zero-Shot CoT ---
    with tab2:
        st.markdown('Simply adding **"Let\'s think step by step"** triggers reasoning without examples.')
        zero_cot_base = st.text_area(
            "Base prompt:",
            value="If John has 3 sisters and each sister has 2 brothers, how many brothers does John have?",
            height=80, key="zero_cot_base",
        )
        if st.button("Without vs. With CoT Trigger", key="run_zero_cot"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Without:**")
                with st.spinner("..."):
                    st.write(invoke_model(zero_cot_base + "\n\nAnswer:", temperature=0.1))
            with col2:
                st.markdown("**With 'Think step by step':**")
                with st.spinner("..."):
                    st.write(invoke_model(zero_cot_base + "\n\nLet's think step by step:", temperature=0.1))

    # --- Tab 3: Few-Shot CoT ---
    with tab3:
        st.markdown("Providing examples **with reasoning steps** teaches the model the expected thought process.")
        few_shot_cot_prompt = st.text_area(
            "Few-shot CoT prompt:",
            value="""Solve each problem by showing your reasoning.

Q: A farmer has 15 sheep. All but 8 die. How many sheep are left?
A: Let's think step by step.
- The farmer starts with 15 sheep.
- "All but 8 die" means 8 survive.
Answer: 8

Q: If a train travels at 60 mph for 2.5 hours, how far does it go?
A: Let's think step by step.
- Distance = Speed x Time
- Distance = 60 x 2.5 = 150 miles
Answer: 150 miles

Q: A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?
A: Let's think step by step.""",
            height=280, key="few_shot_cot",
        )
        if st.button("Run Few-Shot CoT", key="run_few_cot"):
            with st.spinner("Reasoning..."):
                st.success(invoke_model(few_shot_cot_prompt, temperature=0.1))

    # --- Tab 4: Self-Consistency ---
    with tab4:
        st.markdown("""
**Self-Consistency** generates multiple reasoning paths and selects the most common answer.
This reduces errors from a single reasoning chain going astray.
""")
        sc_prompt = st.text_area(
            "Problem:",
            value="When I was 6 years old, my sister was half my age. Now I'm 70. How old is my sister?\n\nLet's think step by step:",
            height=100, key="self_consistency",
        )
        num_samples = st.slider("Number of samples:", 3, 7, 5, key="num_samples")
        if st.button("Run Self-Consistency", key="run_sc"):
            cols = st.columns(num_samples)
            for i in range(num_samples):
                with cols[i]:
                    st.markdown(f"**#{i+1}**")
                    with st.spinner("..."):
                        st.write(invoke_model(sc_prompt, temperature=0.7))
            st.info("🗳️ The most frequent final answer is likely correct.")
