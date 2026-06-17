import streamlit as st
import boto3
import time
import json
import re
from utils.styles import load_css, sub_header, create_footer, AWS_COLORS
from utils.common import (
    render_sidebar,
    render_generator_model_selector,
    get_generator_model_id,
    render_judge_model_selector,
    get_judge_model_id,
)


@st.cache_resource
def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Practical scenario presets
# ---------------------------------------------------------------------------
PRESETS = {
    "Summarize article": {
        "instruction": "Summarize the following article in 3 bullet points.",
        "context": "You are a professional editor who specializes in concise summaries for busy executives.",
        "input_data": (
            "Artificial intelligence has transformed healthcare by enabling early disease "
            "detection through medical imaging analysis. Machine learning models can now "
            "identify patterns in X-rays, MRIs, and CT scans with accuracy comparable to "
            "experienced radiologists. These advances have reduced diagnostic wait times "
            "and improved patient outcomes in several clinical trials."
        ),
        "output_format": "Return exactly 3 bullet points, each starting with a dash. Keep each bullet under 20 words.",
    },
    "Classify sentiment": {
        "instruction": "Classify the sentiment of the following customer review.",
        "context": "You are a sentiment analysis system for an e-commerce platform. You must be precise and consistent.",
        "input_data": (
            "I ordered this laptop two weeks ago and it arrived with a cracked screen. "
            "Customer support took 5 days to respond and offered no refund. Absolutely terrible experience."
        ),
        "output_format": "Respond with exactly one word: POSITIVE, NEGATIVE, or NEUTRAL. Then provide a one-sentence justification.",
    },
    "Extract JSON": {
        "instruction": "Extract structured information from the following text and return it as JSON.",
        "context": "You are a data extraction system. Be precise and only extract information explicitly stated in the text.",
        "input_data": (
            "Dr. Sarah Chen, a cardiologist at Boston Medical Center, published a study on "
            "March 15, 2024 about the effects of sleep deprivation on heart rate variability "
            "in adults aged 30-50."
        ),
        "output_format": '{"name": "...", "specialty": "...", "institution": "...", "publication_date": "...", "topic": "...", "demographic": "..."}',
    },
    "Write email": {
        "instruction": "Write a professional email declining a meeting invitation.",
        "context": "You are an executive assistant. The tone should be polite but firm. The person invited is a VP-level executive.",
        "input_data": "Meeting: Quarterly Budget Review. Date: Friday 3pm. Reason for declining: conflict with board presentation prep.",
        "output_format": "Format as: Subject line, then email body. Keep under 100 words. Include a suggestion to reschedule.",
    },
    "Debug code": {
        "instruction": "Identify the bug in the following Python code and provide the corrected version.",
        "context": "You are a senior Python developer performing code review. The code is intended to calculate the average of a list of numbers.",
        "input_data": (
            "def calculate_average(numbers):\n"
            "    total = 0\n"
            "    for num in numbers:\n"
            "        total += num\n"
            "    return total / len(numbers)\n\n"
            "result = calculate_average([])"
        ),
        "output_format": "1. State the bug in one sentence. 2. Show the corrected code. 3. Explain why the fix works.",
    },
    "Generate SQL query": {
        "instruction": "Write a SQL query based on the following business requirement.",
        "context": "You are a database analyst. The database uses PostgreSQL. Tables: orders(id, customer_id, amount, status, created_at), customers(id, name, email, tier).",
        "input_data": "Find the top 5 premium-tier customers by total order amount in the last 30 days, only counting completed orders.",
        "output_format": "Return only the SQL query. Use clear formatting with each clause on its own line.",
    },
    "Create test cases": {
        "instruction": "Generate test cases for the following function specification.",
        "context": "You are a QA engineer writing test cases for a password validation function. The function should return True if the password is valid.",
        "input_data": "Rules: minimum 8 characters, at least one uppercase letter, at least one number, at least one special character (!@#$%^&*), no spaces allowed.",
        "output_format": "Return a table with columns: Test Case Name | Input | Expected Output | Reason. Include at least 6 test cases covering edge cases.",
    },
    "Incident response": {
        "instruction": "Draft an incident response communication for the following production issue.",
        "context": "You are a Site Reliability Engineer at a SaaS company. The communication is for internal engineering stakeholders via Slack.",
        "input_data": "Issue: Payment processing API returning 500 errors for 12% of requests since 14:30 UTC. Root cause: database connection pool exhausted due to a slow query introduced in today's deployment v2.4.1.",
        "output_format": "Format: Status (Investigating/Identified/Resolved) | Impact summary | Root cause | Current actions | ETA. Keep under=180 words.",
    },
}


# ---------------------------------------------------------------------------
# Challenge mode scenarios
# ---------------------------------------------------------------------------
CHALLENGES = {
    "JSON Extraction Challenge": {
        "scenario": (
            "A recruiter sends you this message: 'Hi, we have an opening for a Senior Backend "
            "Engineer at Netflix in Los Angeles, offering $180k-$220k. They need 5+ years of Go "
            "experience and Kubernetes expertise. The role is hybrid, 3 days in office. Apply by "
            "June 30, 2025.'"
        ),
        "goal": "Get the model to output valid JSON with ALL fields: title, company, location, salary_range, requirements, work_model, deadline.",
        "passing_score": 8,
    },
    "Concise Summary Challenge": {
        "scenario": (
            "Summarize this 3-paragraph technical article about quantum computing into exactly "
            "2 sentences that a non-technical CEO would understand. The article discusses qubit "
            "stability improvements, error correction breakthroughs, and commercial timeline projections."
        ),
        "goal": "Get exactly 2 sentences, no jargon, that capture the business impact. Judge score ≥ 8.",
        "passing_score": 8,
    },
    "Tone Control Challenge": {
        "scenario": (
            "Write a message informing a customer that their subscription will increase by 20% "
            "next month. The customer is a 3-year loyal user on the Enterprise plan."
        ),
        "goal": "The response must be empathetic, offer a retention incentive, and stay under 80 words. Judge score ≥ 8.",
        "passing_score": 8,
    },
}

# ---------------------------------------------------------------------------
# Prompt tips reference
# ---------------------------------------------------------------------------
PROMPT_TIPS = {
    "Instruction": [
        "Start with a clear action verb (Summarize, Classify, Extract, Write, Generate)",
        "Be specific about the task scope — what to include AND exclude",
        "Avoid ambiguous words like 'good', 'nice', 'appropriate'",
    ],
    "Context": [
        "Define the persona/role the model should assume",
        "Include domain-specific constraints (e.g., 'Use only information from the provided text')",
        "Mention the target audience if relevant",
    ],
    "Input Data": [
        "Clearly delimit input from instruction using tags or formatting",
        "Provide representative data — garbage in, garbage out",
        "For multi-part input, label each section",
    ],
    "Output Format": [
        "Specify exact structure (JSON, bullets, table, numbered list)",
        "Set length constraints (word count, sentence count, character limit)",
        "Include an example of the desired output when possible",
    ],
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def call_bedrock(prompt, system_prompt=None, model_id=None):
    client = get_bedrock_client()
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    kwargs = {"modelId": model_id or get_generator_model_id(), "messages": messages}
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]
    try:
        start = time.time()
        response = client.converse(**kwargs)
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


def assemble_prompt(components):
    parts = []
    if components.get("instruction_enabled") and components.get("instruction"):
        parts.append(f"<instruction>\n{components['instruction']}\n</instruction>")
    if components.get("context_enabled") and components.get("context"):
        parts.append(f"<context>\n{components['context']}\n</context>")
    if components.get("input_enabled") and components.get("input_data"):
        parts.append(f"<input>\n{components['input_data']}\n</input>")
    if components.get("output_format_enabled") and components.get("output_format"):
        parts.append(f"<output_format>\n{components['output_format']}\n</output_format>")
    return "\n\n".join(parts)


def count_tokens_approx(text):
    """Rough token estimate: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def _on_preset_change():
    """Callback: update text area session state when preset selection changes."""
    preset = st.session_state.get("pa_preset", "Custom")
    if preset != "Custom" and preset in PRESETS:
        vals = PRESETS[preset]
        st.session_state["pa_instruction"] = vals["instruction"]
        st.session_state["pa_context"] = vals["context"]
        st.session_state["pa_input_data"] = vals["input_data"]
        st.session_state["pa_output_format"] = vals["output_format"]
    else:
        st.session_state["pa_instruction"] = ""
        st.session_state["pa_context"] = ""
        st.session_state["pa_input_data"] = ""
        st.session_state["pa_output_format"] = ""


def run_judge(full_prompt, response_text):
    """Run the AI judge and return the result dict."""
    judge_prompt = (
        f"You are an expert AI judge evaluating prompt engineering quality.\n\n"
        f"## Prompt Sent\n```\n{full_prompt}\n```\n\n"
        f"## Model Response\n```\n{response_text}\n```\n\n"
        f"## Evaluation Criteria\n\n"
        f"### PROMPT Evaluation (score each 1-10):\n"
        f"1. **Clarity** — Is the instruction unambiguous? Could it be misinterpreted?\n"
        f"2. **Specificity** — Does it define scope, constraints, and boundaries precisely?\n"
        f"3. **Structure** — Does it use clear sections (instruction, context, input, output format) with proper delimiters?\n"
        f"4. **Context Sufficiency** — Does it provide enough background for the model to respond accurately?\n"
        f"5. **Output Guidance** — Does it specify the expected format, length, tone, or style?\n\n"
        f"### RESPONSE Evaluation (score each 1-10):\n"
        f"1. **Accuracy** — Is the information factually correct and free of hallucinations?\n"
        f"2. **Completeness** — Does it fully address what was asked without missing key points?\n"
        f"3. **Format Adherence** — Does it follow the requested output format exactly?\n"
        f"4. **Relevance** — Does it stay on-topic without unnecessary filler or tangents?\n"
        f"5. **Coherence** — Is it well-organized, logically structured, and easy to read?\n\n"
        f"## Required Output Format\n"
        f"You MUST respond in EXACTLY this format (no extra text):\n"
        f"Prompt Clarity: X/10\n"
        f"Prompt Specificity: X/10\n"
        f"Prompt Structure: X/10\n"
        f"Prompt Context: X/10\n"
        f"Prompt Output Guidance: X/10\n"
        f"Response Accuracy: X/10\n"
        f"Response Completeness: X/10\n"
        f"Response Format Adherence: X/10\n"
        f"Response Relevance: X/10\n"
        f"Response Coherence: X/10\n"
        f"Prompt Feedback: (one actionable sentence to improve the prompt)\n"
        f"Response Feedback: (one sentence on the response quality)"
    )
    return call_bedrock(judge_prompt, model_id=get_judge_model_id())


def parse_judge_scores(judge_text):
    """Parse judge output into a dict of scores and feedback."""
    def _score(label):
        match = re.search(rf"{label}:\s*(\d+)/10", judge_text)
        return int(match.group(1)) if match else None

    scores = {
        "p_clarity": _score("Prompt Clarity"),
        "p_specificity": _score("Prompt Specificity"),
        "p_structure": _score("Prompt Structure"),
        "p_context": _score("Prompt Context"),
        "p_output": _score("Prompt Output Guidance"),
        "r_accuracy": _score("Response Accuracy"),
        "r_completeness": _score("Response Completeness"),
        "r_format": _score("Response Format Adherence"),
        "r_relevance": _score("Response Relevance"),
        "r_coherence": _score("Response Coherence"),
    }
    p_scores = [v for k, v in scores.items() if k.startswith("p_") and v is not None]
    r_scores = [v for k, v in scores.items() if k.startswith("r_") and v is not None]
    scores["p_avg"] = sum(p_scores) / len(p_scores) if p_scores else None
    scores["r_avg"] = sum(r_scores) / len(r_scores) if r_scores else None

    pf = re.search(r"Prompt Feedback:\s*(.+)", judge_text)
    rf = re.search(r"Response Feedback:\s*(.+)", judge_text)
    scores["prompt_feedback"] = pf.group(1).strip() if pf else None
    scores["response_feedback"] = rf.group(1).strip() if rf else None
    return scores


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    load_css()

    with st.sidebar:
        render_sidebar()
        render_generator_model_selector()
        render_judge_model_selector()
        if st.button("🗑️ Clear All", key="pa_clear"):
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("pa_")]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            # Set components to empty so they don't get re-initialized with preset
            st.session_state["pa_instruction"] = ""
            st.session_state["pa_context"] = ""
            st.session_state["pa_input_data"] = ""
            st.session_state["pa_output_format"] = ""
            st.rerun()

    st.markdown(sub_header("Prompt Anatomy Builder", icon="🧱"), unsafe_allow_html=True)
    st.markdown(
        "**Key Concept:** Every effective prompt has up to 4 components — "
        "Instruction, Context, Input Data, and Output Format. "
        "Toggle them on/off to see how each affects the response."
    )

    # --- Prompt Tips panel ---
    with st.expander("💡 Prompt Writing Tips", expanded=False):
        tips_cols = st.columns(4)
        for i, (component, tips) in enumerate(PROMPT_TIPS.items()):
            with tips_cols[i]:
                st.markdown(f"**{component}**")
                for tip in tips:
                    st.markdown(f"- {tip}")

    # Initialize text areas with first preset if not yet set
    if "pa_instruction" not in st.session_state:
        first_preset = list(PRESETS.keys())[0]
        st.session_state["pa_instruction"] = PRESETS[first_preset]["instruction"]
        st.session_state["pa_context"] = PRESETS[first_preset]["context"]
        st.session_state["pa_input_data"] = PRESETS[first_preset]["input_data"]
        st.session_state["pa_output_format"] = PRESETS[first_preset]["output_format"]

    preset = st.selectbox(
        "Load a sample preset:",
        ["Custom"] + list(PRESETS.keys()),
        key="pa_preset",
        on_change=_on_preset_change,
    )

    st.markdown("---")
    st.markdown("### Prompt Components")

    col1, col2 = st.columns(2)
    with col1:
        inst_enabled = st.checkbox("✅ Instruction", value=True, key="pa_inst_en")
        instruction = st.text_area(
            "Instruction",
            key="pa_instruction",
            height=80,
            disabled=not inst_enabled,
        )
        ctx_enabled = st.checkbox("✅ Context", value=True, key="pa_ctx_en")
        context = st.text_area(
            "Context",
            key="pa_context",
            height=80,
            disabled=not ctx_enabled,
        )

    with col2:
        inp_enabled = st.checkbox("✅ Input Data", value=True, key="pa_inp_en")
        input_data = st.text_area(
            "Input Data",
            key="pa_input_data",
            height=180,
            disabled=not inp_enabled,
        )
        fmt_enabled = st.checkbox("✅ Output Format", value=True, key="pa_fmt_en")
        output_format = st.text_area(
            "Output Format",
            key="pa_output_format",
            height=80,
            disabled=not fmt_enabled,
        )

    components = {
        "instruction_enabled": inst_enabled,
        "instruction": instruction,
        "context_enabled": ctx_enabled,
        "context": context,
        "input_enabled": inp_enabled,
        "input_data": input_data,
        "output_format_enabled": fmt_enabled,
        "output_format": output_format,
    }

    full_prompt = assemble_prompt(components)

    # --- Token estimate ---
    if full_prompt.strip():
        est_tokens = count_tokens_approx(full_prompt)
        st.caption(f"📊 Estimated prompt size: ~{est_tokens} tokens | {len(full_prompt)} characters")

    # --- Run prompt ---
    if st.button("🚀 Run Prompt", type="primary"):
        if not full_prompt.strip():
            st.warning("Please enable at least one component and add content.")
        else:
            with st.spinner("Calling Amazon Bedrock..."):
                result = call_bedrock(full_prompt)
                st.session_state["pa_full_result"] = result
                st.session_state["pa_full_prompt"] = full_prompt

                # Comparison: instruction-only
                instruction_only_prompt = ""
                if instruction.strip():
                    instruction_only_prompt = f"<instruction>\n{instruction}\n</instruction>"
                    if input_data.strip() and inp_enabled:
                        instruction_only_prompt += f"\n\n<input>\n{input_data}\n</input>"

                if instruction_only_prompt.strip():
                    compare_result = call_bedrock(instruction_only_prompt)
                else:
                    compare_result = call_bedrock(instruction if instruction.strip() else full_prompt)
                st.session_state["pa_compare_result"] = compare_result
                st.session_state["pa_compare_prompt"] = instruction_only_prompt or instruction

            with st.spinner("AI Judge is evaluating..."):
                judge_result = run_judge(full_prompt, result["text"])
                st.session_state["pa_judge_result"] = judge_result

            # --- History tracking ---
            if "pa_history" not in st.session_state:
                st.session_state["pa_history"] = []
            scores = parse_judge_scores(judge_result["text"])
            st.session_state["pa_history"].append({
                "iteration": len(st.session_state["pa_history"]) + 1,
                "prompt": full_prompt,
                "response": result["text"],
                "p_avg": scores["p_avg"],
                "r_avg": scores["r_avg"],
                "prompt_feedback": scores["prompt_feedback"],
            })

    # --- Tabs ---
    tab_full, tab_compare, tab_judge, tab_history, tab_challenge = st.tabs(
        ["📄 Full Prompt", "⚖️ Compare", "🧑‍⚖️ AI Judge", "📈 History", "🎯 Challenge Mode"]
    )

    with tab_full:
        if "pa_full_result" in st.session_state:
            result = st.session_state["pa_full_result"]
            with st.expander("Assembled Prompt", expanded=False):
                st.code(st.session_state.get("pa_full_prompt", ""), language="xml")
            st.markdown("**Response:**")
            st.markdown(result["text"])
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Input Tokens", result["input_tokens"])
            col_b.metric("Output Tokens", result["output_tokens"])
            col_c.metric("Latency", f"{result['latency']:.2f}s")
        else:
            st.info("Click 'Run Prompt' to see results here.")

    with tab_compare:
        if "pa_full_result" in st.session_state and "pa_compare_result" in st.session_state:
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**✅ All Components**")
                with st.expander("Prompt sent"):
                    st.code(st.session_state.get("pa_full_prompt", ""), language="xml")
                full_r = st.session_state["pa_full_result"]
                st.markdown(full_r["text"])
                st.caption(
                    f"Tokens: {full_r['input_tokens']} in / {full_r['output_tokens']} out | "
                    f"Latency: {full_r['latency']:.2f}s"
                )
            with col_right:
                st.markdown("**⚠️ Instruction Only (no context/format)**")
                with st.expander("Prompt sent"):
                    st.code(st.session_state.get("pa_compare_prompt", ""), language="xml")
                cmp_r = st.session_state["pa_compare_result"]
                st.markdown(cmp_r["text"])
                st.caption(
                    f"Tokens: {cmp_r['input_tokens']} in / {cmp_r['output_tokens']} out | "
                    f"Latency: {cmp_r['latency']:.2f}s"
                )
            st.info(
                "💡 Notice how removing Context and Output Format typically leads to "
                "less focused, less structured responses."
            )
        else:
            st.info("Click 'Run Prompt' to see the comparison.")

    with tab_judge:
        if "pa_judge_result" in st.session_state:
            judge_text = st.session_state["pa_judge_result"]["text"]
            scores = parse_judge_scores(judge_text)

            # Overall metrics
            col_overall_p, col_overall_r = st.columns(2)
            with col_overall_p:
                st.metric("📝 Prompt Quality (avg)", f"{scores['p_avg']:.1f}/10" if scores["p_avg"] else "N/A")
            with col_overall_r:
                st.metric("💬 Response Quality (avg)", f"{scores['r_avg']:.1f}/10" if scores["r_avg"] else "N/A")

            # Prompt breakdown
            st.markdown("#### Prompt Breakdown")
            cols_p = st.columns(5)
            for col, label, key in zip(cols_p,
                ["Clarity", "Specificity", "Structure", "Context", "Output Guidance"],
                ["p_clarity", "p_specificity", "p_structure", "p_context", "p_output"]):
                val = scores[key]
                col.metric(label, f"{val}/10" if val is not None else "N/A")

            # Response breakdown
            st.markdown("#### Response Breakdown")
            cols_r = st.columns(5)
            for col, label, key in zip(cols_r,
                ["Accuracy", "Completeness", "Format", "Relevance", "Coherence"],
                ["r_accuracy", "r_completeness", "r_format", "r_relevance", "r_coherence"]):
                val = scores[key]
                col.metric(label, f"{val}/10" if val is not None else "N/A")

            # Feedback
            if scores["prompt_feedback"]:
                st.info(f"💡 **Prompt Feedback:** {scores['prompt_feedback']}")
            if scores["response_feedback"]:
                st.info(f"📝 **Response Feedback:** {scores['response_feedback']}")

            with st.expander("Full Judge Output"):
                st.markdown(judge_text)
        else:
            st.info("Click 'Run Prompt' to see the AI Judge evaluation.")

    with tab_history:
        history = st.session_state.get("pa_history", [])
        if history:
            st.markdown("#### Iteration History")
            st.markdown("Track how your prompt scores improve as you iterate.")

            # Score progression chart
            if len(history) >= 2:
                import plotly.graph_objects as go
                fig = go.Figure()
                iterations = [h["iteration"] for h in history]
                p_avgs = [h["p_avg"] for h in history]
                r_avgs = [h["r_avg"] for h in history]
                fig.add_trace(go.Scatter(x=iterations, y=p_avgs, mode="lines+markers", name="Prompt Quality"))
                fig.add_trace(go.Scatter(x=iterations, y=r_avgs, mode="lines+markers", name="Response Quality"))
                fig.update_layout(
                    xaxis_title="Iteration",
                    yaxis_title="Score (out of 10)",
                    yaxis=dict(range=[0, 10.5]),
                    height=300,
                    margin=dict(t=20, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

            # History table
            for i, h in enumerate(reversed(history)):
                with st.expander(f"Iteration {h['iteration']} — Prompt: {h['p_avg']:.1f}/10 | Response: {h['r_avg']:.1f}/10" if h["p_avg"] else f"Iteration {h['iteration']}"):
                    st.code(h["prompt"], language="xml")
                    st.markdown(f"**Response:** {h['response'][:300]}{'...' if len(h['response']) > 300 else ''}")
                    if h.get("prompt_feedback"):
                        st.caption(f"💡 {h['prompt_feedback']}")

            if st.button("🗑️ Clear History", key="pa_clear_history"):
                st.session_state["pa_history"] = []
                st.rerun()
        else:
            st.info("Run prompts to build your iteration history. Each run is tracked so you can see your improvement over time.")

    with tab_challenge:
        st.markdown("#### 🎯 Challenge Mode")
        st.markdown(
            "Pick a challenge, craft a prompt that meets the acceptance criteria, "
            "and score ≥ 8 on the AI Judge to pass."
        )

        challenge_name = st.selectbox(
            "Select a challenge:",
            list(CHALLENGES.keys()),
            key="pa_challenge_select",
        )
        challenge = CHALLENGES[challenge_name]

        st.markdown(f"**Scenario:** {challenge['scenario']}")
        st.success(f"**Goal:** {challenge['goal']}")
        st.markdown(f"**Passing score:** {challenge['passing_score']}/10 average")

        st.markdown("---")
        st.markdown("Build your prompt using the components above, then click **Run Prompt** to attempt the challenge.")

        # Check if latest history entry meets the challenge
        history = st.session_state.get("pa_history", [])
        if history:
            latest = history[-1]
            if latest["p_avg"] is not None and latest["r_avg"] is not None:
                overall_avg = (latest["p_avg"] + latest["r_avg"]) / 2
                if overall_avg >= challenge["passing_score"]:
                    st.success(
                        f"🎉 Challenge passed! Overall score: {overall_avg:.1f}/10 "
                        f"(Prompt: {latest['p_avg']:.1f}, Response: {latest['r_avg']:.1f})"
                    )
                else:
                    st.warning(
                        f"Not quite — your last score was {overall_avg:.1f}/10 "
                        f"(need ≥ {challenge['passing_score']}). "
                        f"Use the judge feedback to refine your prompt and try again."
                    )

    create_footer()



main()
