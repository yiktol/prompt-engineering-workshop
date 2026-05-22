import streamlit as st
from utils.bedrock_client import invoke_model
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Advanced Techniques", page_icon="🚀", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🚀 Advanced Techniques")
    st.markdown("Techniques for complex, multi-step tasks: decomposition and context enrichment.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 Prompt Chaining", "🧠 Generate Knowledge", "🌳 Tree of Thoughts", "🪄 Meta Prompting"
    ])

    # --- Tab 1: Prompt Chaining ---
    with tab1:
        st.markdown("""
**Prompt Chaining** breaks a complex task into sequential subtasks.
The output of one step becomes the input for the next.
This improves reliability by keeping each step focused and verifiable.
""")
        input_text = st.text_area(
            "Input document:",
            value="""Amazon Web Services (AWS) announced today that it has expanded its generative AI services with new features in Amazon Bedrock. The update includes support for additional foundation models from Anthropic, Meta, and Mistral AI. AWS CEO Matt Garman stated that enterprise adoption of generative AI has tripled in the past year, with healthcare and financial services leading the charge. The new features include guardrails for responsible AI, knowledge bases for RAG applications, and agents for multi-step task automation. Pricing starts at $0.001 per 1000 input tokens for the most affordable models.""",
            height=130, key="chain_input",
        )
        if st.button("Run 3-Step Chain", key="run_chain"):
            st.markdown("**Step 1: Summarize**")
            with st.spinner("Summarizing..."):
                summary = invoke_model(f"Summarize the following text in 2-3 sentences:\n\n{input_text}", temperature=0.3)
            st.info(summary)

            st.markdown("**Step 2: Extract Entities**")
            with st.spinner("Extracting..."):
                entities = invoke_model(f"From the following summary, extract all named entities (people, organizations, products, prices). Format as a bullet list.\n\nSummary: {summary}", temperature=0.1)
            st.info(entities)

            st.markdown("**Step 3: Business Insights**")
            with st.spinner("Generating insights..."):
                insights = invoke_model(f"Based on the following summary and entities, generate 3 actionable business insights.\n\nSummary: {summary}\n\nEntities: {entities}", temperature=0.5)
            st.success(insights)

    # --- Tab 2: Generate Knowledge ---
    with tab2:
        st.markdown("""
**Generate Knowledge** asks the model to produce relevant facts first,
then uses that knowledge to answer. This reduces hallucination by grounding
the response in self-generated context.
""")
        knowledge_q = st.text_area(
            "Question:", value="Is it safe to mix bleach and vinegar for cleaning?",
            height=60, key="knowledge_q",
        )
        if st.button("Direct vs. Knowledge-First", key="run_knowledge"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Direct Answer**")
                with st.spinner("..."):
                    st.write(invoke_model(knowledge_q, temperature=0.3))
            with col2:
                st.markdown("**Knowledge → Answer**")
                with st.spinner("Generating knowledge..."):
                    knowledge = invoke_model(
                        f"Generate 3-5 relevant scientific facts about the chemicals in this question:\n\nQuestion: {knowledge_q}\n\nFacts:",
                        temperature=0.3,
                    )
                st.info(knowledge)
                with st.spinner("Answering..."):
                    answer = invoke_model(
                        f"Using these facts, answer accurately.\n\nFacts:\n{knowledge}\n\nQuestion: {knowledge_q}\n\nAnswer:",
                        temperature=0.3,
                    )
                st.write(answer)

    # --- Tab 3: Tree of Thoughts ---
    with tab3:
        st.markdown("""
**Tree of Thoughts (ToT)** explores multiple reasoning paths in parallel,
evaluates each, and selects the most promising one.
""")
        tot_problem = st.text_area(
            "Problem:",
            value="A company needs to reduce cloud computing costs by 30% without affecting performance. They use on-demand instances for all workloads. What strategy should they adopt?",
            height=80, key="tot_problem",
        )
        if st.button("Run Tree of Thoughts", key="run_tot"):
            st.markdown("**Step 1: Generate Approaches**")
            with st.spinner("Generating..."):
                approaches = invoke_model(
                    f"Problem: {tot_problem}\n\nGenerate 3 different approaches. For each: name, core strategy, 2-3 key steps.",
                    temperature=0.7,
                )
            st.info(approaches)
            st.markdown("**Step 2: Evaluate & Recommend**")
            with st.spinner("Evaluating..."):
                evaluation = invoke_model(
                    f"Problem: {tot_problem}\n\nApproaches:\n{approaches}\n\nEvaluate each on Feasibility, Risk, Expected Impact (1-5). Recommend the best.",
                    temperature=0.3,
                )
            st.success(evaluation)

    # --- Tab 4: Meta Prompting ---
    with tab4:
        st.markdown("""
**Meta Prompting** asks the model to generate or improve a prompt for a given task.
The model becomes a prompt engineer itself.
""")
        meta_task = st.text_area(
            "Describe the task you need a prompt for:",
            value="I need to extract action items from meeting transcripts and format them with assignee, deadline, and priority.",
            height=80, key="meta_task",
        )
        if st.button("Generate Optimized Prompt", key="run_meta"):
            with st.spinner("Generating prompt..."):
                generated = invoke_model(
                    f"You are an expert prompt engineer. Generate an optimized prompt for this task:\n\nTask: {meta_task}\n\nRequirements: clear, specific, includes format instructions, handles edge cases.\n\nGenerated Prompt:",
                    temperature=0.5,
                )
            st.code(generated, language=None)

            st.markdown("**Testing with sample input:**")
            test_input = "Meeting notes: John will prepare the Q4 report by Friday. Sarah needs to review the budget proposal ASAP. The team agreed to postpone the launch to next month."
            with st.spinner("Testing..."):
                result = invoke_model(f"{generated}\n\nInput:\n{test_input}", temperature=0.3)
            st.success(result)
