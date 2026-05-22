import streamlit as st
from utils.bedrock_client import invoke_model
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Zero-Shot & Few-Shot", page_icon="🎯", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🎯 Zero-Shot & Few-Shot Prompting")
    st.markdown("**Zero-shot** — no examples. **Few-shot** — examples demonstrate desired behavior.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["0️⃣ Zero-Shot", "🔢 Few-Shot", "⚖️ Comparison"])

    # --- Tab 1: Zero-Shot ---
    with tab1:
        st.markdown("""
The model performs a task with only an instruction — no examples provided.
Works well for simple, well-understood tasks.
""")
        zero_shot_prompt = st.text_area(
            "Zero-shot prompt:",
            value="Classify the following text as positive, negative, or neutral.\n\nText: The new restaurant downtown has amazing food but terrible service.\nSentiment:",
            height=120, key="zero_shot",
        )
        if st.button("Run Zero-Shot", key="run_zero"):
            with st.spinner("Generating..."):
                st.success(invoke_model(zero_shot_prompt))

    # --- Tab 2: Few-Shot ---
    with tab2:
        st.markdown("""
Providing examples helps the model understand:
- The **format** of the expected output
- The **style** or **tone** desired
- Edge cases and nuances
""")
        few_shot_prompt = st.text_area(
            "Few-shot prompt:",
            value='''Classify the sentiment of each review as positive, negative, or neutral.

Review: "The battery life is incredible, lasts all day!"
Sentiment: positive

Review: "It's okay, nothing special about it."
Sentiment: neutral

Review: "Worst purchase ever. Broke after two days."
Sentiment: negative

Review: "The camera quality is decent but the price is too high for what you get."
Sentiment:''',
            height=250, key="few_shot",
        )
        if st.button("Run Few-Shot", key="run_few"):
            with st.spinner("Generating..."):
                st.success(invoke_model(few_shot_prompt))

    # --- Tab 3: Comparison ---
    with tab3:
        st.markdown("See how the same task performs with zero-shot vs. few-shot approaches.")
        task = st.selectbox(
            "Choose a task:", ["Sentiment Analysis", "Text Classification", "Entity Extraction"], key="zf_task"
        )
        comparisons = {
            "Sentiment Analysis": {
                "zero": "Classify the sentiment as positive, negative, or neutral.\n\nText: I waited 45 minutes for my order and when it arrived it was cold, but the waiter was very apologetic and gave us a discount.\nSentiment:",
                "few": 'Classify the sentiment as positive, negative, or neutral.\n\nText: "Great product, fast shipping!"\nSentiment: positive\n\nText: "The item works but the packaging was damaged."\nSentiment: neutral\n\nText: "Complete waste of money, doesn\'t work at all."\nSentiment: negative\n\nText: "I waited 45 minutes for my order and when it arrived it was cold, but the waiter was very apologetic and gave us a discount."\nSentiment:',
            },
            "Text Classification": {
                "zero": "Classify the following news headline into one category: Sports, Technology, Politics, Entertainment, Science.\n\nHeadline: New CRISPR technique enables precise gene editing in living organisms\nCategory:",
                "few": 'Classify each headline into one category: Sports, Technology, Politics, Entertainment, Science.\n\nHeadline: "Lakers win championship in overtime thriller"\nCategory: Sports\n\nHeadline: "Senate passes new infrastructure bill"\nCategory: Politics\n\nHeadline: "Apple announces new M4 chip with 40% performance boost"\nCategory: Technology\n\nHeadline: "New CRISPR technique enables precise gene editing in living organisms"\nCategory:',
            },
            "Entity Extraction": {
                "zero": "Extract all person names, organizations, and locations from the following text.\n\nText: Sarah Johnson from Microsoft presented at the AI conference in Seattle last Tuesday, where she met with Dr. Chen from Stanford University.\n\nEntities:",
                "few": 'Extract entities (Person, Organization, Location) from the text.\n\nText: "Tim Cook announced Apple\'s new product at their Cupertino headquarters."\nEntities:\n- Person: Tim Cook\n- Organization: Apple\n- Location: Cupertino\n\nText: "Sarah Johnson from Microsoft presented at the AI conference in Seattle last Tuesday, where she met with Dr. Chen from Stanford University."\nEntities:',
            },
        }
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Zero-Shot**")
            zero_p = st.text_area("Zero", value=comparisons[task]["zero"], height=200, key="cmp_zero", label_visibility="collapsed")
        with col2:
            st.markdown("**Few-Shot**")
            few_p = st.text_area("Few", value=comparisons[task]["few"], height=200, key="cmp_few", label_visibility="collapsed")
        if st.button("Compare Both Approaches", key="compare_both"):
            col1, col2 = st.columns(2)
            with col1:
                with st.spinner("Zero-shot..."):
                    st.write(invoke_model(zero_p))
            with col2:
                with st.spinner("Few-shot..."):
                    st.write(invoke_model(few_p))
