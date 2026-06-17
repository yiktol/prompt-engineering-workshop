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


st.set_page_config(page_title="Strategy Comparison", page_icon="⚖️", layout="wide")

@st.cache_resource
def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Sample tasks — designed to show when each strategy wins
# ---------------------------------------------------------------------------
SAMPLE_TASKS = {
    "Classify email sentiment": {
        "task": "Classify the sentiment of this email",
        "input_text": (
            "Hi Team, I wanted to flag that the deployment last night caused three production outages. "
            "Customers are frustrated and our SLA metrics are suffering. We need to address this urgently "
            "before the next release. - Alex"
        ),
        "best_strategy": "few-shot",
        "why": "Classification with nuanced tone (urgent but professional, not angry) benefits from examples that calibrate the labels.",
    },
    "Solve math problem": {
        "task": "Solve this math word problem",
        "input_text": (
            "A store sells notebooks for $3.50 each and pens for $1.25 each. If Maria bought 4 notebooks "
            "and some pens, and spent exactly $21.75 in total, how many pens did she buy?"
        ),
        "best_strategy": "chain-of-thought",
        "why": "Multi-step arithmetic requires showing work to avoid errors. CoT forces the model to reason through each step.",
    },
    "Extract entities": {
        "task": "Extract all named entities from this text",
        "input_text": (
            "On January 15, 2024, Amazon Web Services announced that Dr. James Rodriguez, VP of Machine "
            "Learning at their Seattle headquarters, would lead the new Bedrock Agents initiative alongside "
            "the Tokyo and London teams."
        ),
        "best_strategy": "few-shot",
        "why": "Entity extraction needs consistent formatting. Few-shot examples define the exact output schema by demonstration.",
    },
    "Simple factual lookup": {
        "task": "Answer this factual question",
        "input_text": "What is the capital of Australia?",
        "best_strategy": "zero-shot",
        "why": "Simple recall questions need no extra scaffolding. Zero-shot is fastest and cheapest — CoT would be overkill.",
    },
    "Multi-step logic puzzle": {
        "task": "Solve this logic puzzle",
        "input_text": (
            "Five friends — Alice, Bob, Carol, Dave, and Eve — sit in a row. Alice is not next to Bob. "
            "Carol sits in the middle. Dave is next to Eve. Bob is at one end. "
            "Who sits next to Carol on both sides?"
        ),
        "best_strategy": "chain-of-thought",
        "why": "Constraint satisfaction requires systematic elimination. Without step-by-step reasoning, models often guess incorrectly.",
    },
    "Ambiguous classification": {
        "task": "Classify this customer message as: Complaint, Question, Feedback, or Request",
        "input_text": (
            "Hi, I noticed your pricing page still shows the old rates from last month. "
            "Just thought you'd want to know. Also, will there be a discount for annual plans?"
        ),
        "best_strategy": "few-shot",
        "why": "This message contains multiple intents. Few-shot examples showing multi-label classification calibrate the model's judgment.",
    },
    "Summarize article": {
        "task": "Summarize this article in 2 sentences",
        "input_text": (
            "Quantum computing is approaching a critical inflection point. Google's Willow chip demonstrated "
            "error correction below the threshold needed for practical computation, solving in minutes what "
            "would take classical supercomputers billions of years. IBM's roadmap targets 100,000 qubits by "
            "2033. However, challenges remain: qubits require near-absolute-zero temperatures, error rates "
            "still limit practical applications, and the programming paradigm requires entirely new algorithmic thinking."
        ),
        "best_strategy": "zero-shot",
        "why": "Summarization is a well-understood task. A clear instruction with length constraint is sufficient — examples or CoT add unnecessary tokens.",
    },
}

FEW_SHOT_EXAMPLES = {
    "Classify email sentiment": [
        {"input": "Great news! The client loved our proposal and wants to proceed immediately.", "output": "POSITIVE"},
        {"input": "The meeting has been rescheduled to next Tuesday at 2pm.", "output": "NEUTRAL"},
        {"input": "I'm disappointed with the lack of progress this sprint. We missed two deadlines.", "output": "NEGATIVE"},
    ],
    "Solve math problem": [
        {"input": "If a shirt costs $20 and is on 25% sale, what's the final price?", "output": "Sale amount = $20 × 0.25 = $5. Final price = $20 - $5 = $15."},
        {"input": "A car travels 180 miles in 3 hours. What is its average speed?", "output": "Average speed = 180 miles ÷ 3 hours = 60 mph."},
    ],
    "Extract entities": [
        {"input": "Microsoft CEO Satya Nadella spoke at Build 2024 in Redmond.", "output": "Persons: Satya Nadella | Organizations: Microsoft | Events: Build 2024 | Locations: Redmond"},
        {"input": "The FDA approved Pfizer's new vaccine on March 1, 2024.", "output": "Organizations: FDA, Pfizer | Products: vaccine | Dates: March 1, 2024"},
    ],
    "Simple factual lookup": [
        {"input": "What is the capital of France?", "output": "Paris"},
        {"input": "What is the capital of Japan?", "output": "Tokyo"},
    ],
    "Multi-step logic puzzle": [
        {"input": "If A > B and B > C, who is smallest?", "output": "Step 1: A > B means A is larger than B. Step 2: B > C means B is larger than C. Step 3: Therefore C is the smallest."},
    ],
    "Ambiguous classification": [
        {"input": "Your app crashes every time I open settings. Fix this!", "output": "Complaint"},
        {"input": "Love the new dashboard! The dark mode is great, but the font could be bigger.", "output": "Feedback (positive with suggestion)"},
        {"input": "Can I upgrade my plan mid-cycle?", "output": "Question"},
    ],
    "Summarize article": [
        {"input": "Electric vehicles saw record sales in 2023, with Tesla delivering 1.8M units. BYD surpassed BMW in global revenue. Charging infrastructure grew 40% year-over-year.", "output": "EV sales hit records in 2023: Tesla delivered 1.8M cars, BYD overtook BMW in revenue, and charging networks expanded 40%."},
    ],
}

# ---------------------------------------------------------------------------
# Strategy tips
# ---------------------------------------------------------------------------
STRATEGY_TIPS = {
    "Zero-shot": {
        "when": "Simple, well-defined tasks where the model already understands the format",
        "examples": "Factual Q&A, simple summarization, translation, basic classification",
        "pros": "Cheapest (fewest tokens), fastest, simplest to implement",
        "cons": "May produce inconsistent formatting, struggles with ambiguous tasks",
    },
    "Few-shot": {
        "when": "Tasks requiring consistent output format, nuanced classification, or pattern matching",
        "examples": "Entity extraction, sentiment with edge cases, data transformation, custom formats",
        "pros": "Calibrates the model's output precisely, handles ambiguity well",
        "cons": "More tokens (higher cost), examples may bias the model, requires good examples",
    },
    "Chain-of-Thought": {
        "when": "Multi-step reasoning, math, logic, tasks where showing work improves accuracy",
        "examples": "Math word problems, logic puzzles, complex analysis, debugging, planning",
        "pros": "Dramatically improves reasoning accuracy, catches errors through decomposition",
        "cons": "Most tokens (highest cost), slowest, verbose output may need post-processing",
    },
}

# ---------------------------------------------------------------------------
# Challenge mode
# ---------------------------------------------------------------------------
CHALLENGES = [
    {
        "task": "Determine whether this code has a bug and explain what it does",
        "input_text": (
            "def fibonacci(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    return fibonacci(n-1) + fibonacci(n-2)\n\n"
            "print(fibonacci(-3))"
        ),
        "best_strategy": "chain-of-thought",
    },
    {
        "task": "Classify this support ticket priority as: P1-Critical, P2-High, P3-Medium, P4-Low",
        "input_text": "The login page is showing a blank white screen for all users since this morning. No one can access the platform.",
        "best_strategy": "few-shot",
    },
    {
        "task": "What is the square root of 144?",
        "input_text": "",
        "best_strategy": "zero-shot",
    },
    {
        "task": "Determine who owns the fish in this logic puzzle",
        "input_text": (
            "There are 3 houses in a row: red, blue, green. The cat owner lives in the red house. "
            "The dog owner lives next to the blue house. The fish owner does not live in the green house. "
            "The blue house is in the middle."
        ),
        "best_strategy": "chain-of-thought",
    },
    {
        "task": "Convert this natural language date to ISO format (YYYY-MM-DD)",
        "input_text": "The third Wednesday of March 2025",
        "best_strategy": "chain-of-thought",
    },
]

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


def build_zero_shot(task, input_text):
    if input_text.strip():
        return f"{task}:\n\n{input_text}"
    return task


def build_few_shot(task, input_text, examples):
    prompt = f"{task}. Here are some examples:\n\n"
    for i, ex in enumerate(examples, 1):
        prompt += f"Example {i}:\nInput: {ex['input']}\nOutput: {ex['output']}\n\n"
    if input_text.strip():
        prompt += f"Now do the same for:\nInput: {input_text}\nOutput:"
    else:
        prompt += "Now do the same for the task above.\nOutput:"
    return prompt


def build_cot(task, input_text):
    base = f"{task}.\n\n"
    if input_text.strip():
        base += f"Input: {input_text}\n\n"
    base += (
        "Think through this step by step:\n"
        "1. First, identify the key information.\n"
        "2. Then, analyze what is being asked.\n"
        "3. Consider any edge cases or nuances.\n"
        "4. Finally, provide your answer.\n\n"
        "Show your reasoning, then give your final answer."
    )
    return base


def compute_efficiency(result, score):
    """Compute a quality-per-token efficiency score."""
    total_tokens = result["input_tokens"] + result["output_tokens"]
    if total_tokens == 0 or score is None:
        return None
    return (score / total_tokens) * 100  # quality points per 100 tokens


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    load_css()

    with st.sidebar:
        render_sidebar()
        render_generator_model_selector()
        render_judge_model_selector()
        if st.button("🗑️ Clear All", key="sc_clear_all"):
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("sc_")]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.session_state["sc_task"] = ""
            st.session_state["sc_input"] = ""
            st.rerun()

    st.markdown(sub_header("Strategy Comparison Lab", icon="⚖️"), unsafe_allow_html=True)
    st.markdown(
        "**Key Concept:** Match your prompting strategy (zero-shot, few-shot, chain-of-thought) "
        "to the complexity of the task. More complex tasks benefit from structured reasoning."
    )

    # --- Strategy reference ---
    with st.expander("💡 When to Use Each Strategy", expanded=False):
        cols = st.columns(3)
        for i, (strategy, info) in enumerate(STRATEGY_TIPS.items()):
            with cols[i]:
                st.markdown(f"**{strategy}**")
                st.markdown(f"🎯 *When:* {info['when']}")
                st.markdown(f"📋 *Examples:* {info['examples']}")
                st.markdown(f"✅ *Pros:* {info['pros']}")
                st.markdown(f"⚠️ *Cons:* {info['cons']}")

    # --- Session state init ---
    if "sc_task" not in st.session_state:
        first_sample = list(SAMPLE_TASKS.keys())[0]
        st.session_state["sc_task"] = SAMPLE_TASKS[first_sample]["task"]
        st.session_state["sc_input"] = SAMPLE_TASKS[first_sample]["input_text"]

    def _on_sample_change():
        s = st.session_state.get("sc_sample", "Custom")
        if s != "Custom" and s in SAMPLE_TASKS:
            st.session_state["sc_task"] = SAMPLE_TASKS[s]["task"]
            st.session_state["sc_input"] = SAMPLE_TASKS[s]["input_text"]
        else:
            st.session_state["sc_task"] = ""
            st.session_state["sc_input"] = ""

    sample = st.selectbox(
        "Load sample task:", ["Custom"] + list(SAMPLE_TASKS.keys()),
        key="sc_sample", on_change=_on_sample_change,
    )

    # Show expected best strategy hint for preset tasks
    if sample != "Custom" and sample in SAMPLE_TASKS:
        st.caption(f"💡 Expected best strategy: **{SAMPLE_TASKS[sample]['best_strategy']}** — {SAMPLE_TASKS[sample]['why']}")

    task = st.text_input("Task description:", key="sc_task")
    input_text = st.text_area("Input text:", height=100, key="sc_input")

    # --- Custom few-shot examples ---
    with st.expander("✏️ Edit Few-shot Examples (optional)", expanded=False):
        st.markdown("Provide your own examples for the few-shot strategy. Leave empty to use defaults.")
        num_examples = st.number_input("Number of examples:", min_value=1, max_value=5, value=2, key="sc_num_examples")
        custom_examples = []
        for i in range(int(num_examples)):
            col_in, col_out = st.columns(2)
            with col_in:
                ex_input = st.text_input(f"Example {i+1} input:", key=f"sc_ex_input_{i}")
            with col_out:
                ex_output = st.text_input(f"Example {i+1} output:", key=f"sc_ex_output_{i}")
            if ex_input.strip() and ex_output.strip():
                custom_examples.append({"input": ex_input, "output": ex_output})

    # Determine which few-shot examples to use
    if custom_examples:
        few_shot_examples = custom_examples
    else:
        sample_key = sample if sample != "Custom" else list(SAMPLE_TASKS.keys())[0]
        few_shot_examples = FEW_SHOT_EXAMPLES.get(sample_key, FEW_SHOT_EXAMPLES[list(FEW_SHOT_EXAMPLES.keys())[0]])

    # --- Run comparison ---
    if st.button("🚀 Compare Strategies", type="primary"):
        if not task.strip():
            st.warning("Please provide a task description.")
        else:
            zero_prompt = build_zero_shot(task, input_text)
            few_prompt = build_few_shot(task, input_text, few_shot_examples)
            cot_prompt = build_cot(task, input_text)

            with st.spinner("Running 3 strategy calls..."):
                zero_result = call_bedrock(zero_prompt)
                few_result = call_bedrock(few_prompt)
                cot_result = call_bedrock(cot_prompt)

            st.session_state["sc_zero"] = {"prompt": zero_prompt, "result": zero_result}
            st.session_state["sc_few"] = {"prompt": few_prompt, "result": few_result}
            st.session_state["sc_cot"] = {"prompt": cot_prompt, "result": cot_result}

            with st.spinner("AI Judge evaluating..."):
                judge_prompt = (
                    f"You are an impartial judge evaluating three responses to the same task.\n\n"
                    f"Task: {task}\nInput: {input_text}\n\n"
                    f"Response A (Zero-shot): {zero_result['text']}\n\n"
                    f"Response B (Few-shot): {few_result['text']}\n\n"
                    f"Response C (Chain-of-Thought): {cot_result['text']}\n\n"
                    f"Score each response on accuracy, completeness, and clarity (1-10).\n\n"
                    f"You MUST respond in EXACTLY this format:\n"
                    f"Zero-shot Score: X/10\n"
                    f"Few-shot Score: X/10\n"
                    f"Chain-of-Thought Score: X/10\n"
                    f"Winner: [strategy name]\n"
                    f"Reasoning: (2-3 sentences explaining why the winner is best and how the others compare)"
                )
                judge_result = call_bedrock(judge_prompt, model_id=get_judge_model_id())
                st.session_state["sc_judge"] = judge_result

            # Parse scores
            jt = judge_result["text"]
            z_score = re.search(r"Zero-shot Score:\s*(\d+)/10", jt)
            f_score = re.search(r"Few-shot Score:\s*(\d+)/10", jt)
            c_score = re.search(r"Chain-of-Thought Score:\s*(\d+)/10", jt)
            st.session_state["sc_scores"] = {
                "zero": int(z_score.group(1)) if z_score else None,
                "few": int(f_score.group(1)) if f_score else None,
                "cot": int(c_score.group(1)) if c_score else None,
            }

            # Track history
            if "sc_history" not in st.session_state:
                st.session_state["sc_history"] = []
            winner_match = re.search(r"Winner:\s*(.+)", jt)
            st.session_state["sc_history"].append({
                "task": task,
                "winner": winner_match.group(1).strip() if winner_match else "Unknown",
                "scores": st.session_state["sc_scores"].copy(),
            })

    # --- Tabs ---
    tab_sidebyside, tab_zero, tab_few, tab_cot, tab_verdict, tab_history, tab_challenge = st.tabs(
        ["📊 Side-by-Side", "Zero-shot", "Few-shot", "Chain-of-Thought", "🏆 Verdict", "📈 History", "🎯 Challenge"]
    )

    with tab_sidebyside:
        if all(k in st.session_state for k in ["sc_zero", "sc_few", "sc_cot"]):
            cols = st.columns(3)
            for col, label, key in zip(cols,
                ["Zero-shot", "Few-shot", "Chain-of-Thought"],
                ["sc_zero", "sc_few", "sc_cot"]):
                with col:
                    data = st.session_state[key]
                    score = st.session_state.get("sc_scores", {}).get(
                        {"sc_zero": "zero", "sc_few": "few", "sc_cot": "cot"}[key])
                    st.markdown(f"**{label}**")
                    if score is not None:
                        st.metric("Quality", f"{score}/10")
                    st.markdown(data["result"]["text"][:500] + ("..." if len(data["result"]["text"]) > 500 else ""))
                    total_tokens = data["result"]["input_tokens"] + data["result"]["output_tokens"]
                    st.caption(f"🪙 {total_tokens} tokens | ⏱️ {data['result']['latency']:.2f}s")
        else:
            st.info("Run the comparison to see all strategies side by side.")

    with tab_zero:
        if "sc_zero" in st.session_state:
            data = st.session_state["sc_zero"]
            with st.expander("Full Prompt Sent"):
                st.code(data["prompt"], language="text")
            st.markdown("**Response:**")
            st.markdown(data["result"]["text"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Input Tokens", data["result"]["input_tokens"])
            c2.metric("Output Tokens", data["result"]["output_tokens"])
            c3.metric("Latency", f"{data['result']['latency']:.2f}s")
        else:
            st.info("Run the comparison to see zero-shot results.")

    with tab_few:
        if "sc_few" in st.session_state:
            data = st.session_state["sc_few"]
            with st.expander("Full Prompt Sent"):
                st.code(data["prompt"], language="text")
            st.markdown("**Response:**")
            st.markdown(data["result"]["text"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Input Tokens", data["result"]["input_tokens"])
            c2.metric("Output Tokens", data["result"]["output_tokens"])
            c3.metric("Latency", f"{data['result']['latency']:.2f}s")
        else:
            st.info("Run the comparison to see few-shot results.")

    with tab_cot:
        if "sc_cot" in st.session_state:
            data = st.session_state["sc_cot"]
            with st.expander("Full Prompt Sent"):
                st.code(data["prompt"], language="text")
            st.markdown("**Response:**")
            st.markdown(data["result"]["text"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Input Tokens", data["result"]["input_tokens"])
            c2.metric("Output Tokens", data["result"]["output_tokens"])
            c3.metric("Latency", f"{data['result']['latency']:.2f}s")
        else:
            st.info("Run the comparison to see chain-of-thought results.")

    with tab_verdict:
        if "sc_judge" in st.session_state:
            scores = st.session_state.get("sc_scores", {})

            # Score metrics
            col_z, col_f, col_c = st.columns(3)
            col_z.metric("Zero-shot", f"{scores.get('zero', 'N/A')}/10" if scores.get("zero") else "N/A")
            col_f.metric("Few-shot", f"{scores.get('few', 'N/A')}/10" if scores.get("few") else "N/A")
            col_c.metric("Chain-of-Thought", f"{scores.get('cot', 'N/A')}/10" if scores.get("cot") else "N/A")

            # Cost efficiency
            st.markdown("#### Cost Efficiency (quality per 100 tokens)")
            if all(k in st.session_state for k in ["sc_zero", "sc_few", "sc_cot"]):
                eff_cols = st.columns(3)
                for col, label, key, score_key in zip(eff_cols,
                    ["Zero-shot", "Few-shot", "CoT"],
                    ["sc_zero", "sc_few", "sc_cot"],
                    ["zero", "few", "cot"]):
                    eff = compute_efficiency(st.session_state[key]["result"], scores.get(score_key))
                    with col:
                        st.metric(f"{label} Efficiency", f"{eff:.2f}" if eff else "N/A",
                                  help="Higher = more quality per token spent")

            st.markdown("---")
            st.markdown("#### 🏆 Judge Reasoning")
            st.markdown(st.session_state["sc_judge"]["text"])

            # Summary table
            st.markdown("#### Token Comparison")
            if all(k in st.session_state for k in ["sc_zero", "sc_few", "sc_cot"]):
                data_rows = []
                for label, key, score_key in [
                    ("Zero-shot", "sc_zero", "zero"),
                    ("Few-shot", "sc_few", "few"),
                    ("Chain-of-Thought", "sc_cot", "cot"),
                ]:
                    r = st.session_state[key]["result"]
                    data_rows.append({
                        "Strategy": label,
                        "Score": f"{scores.get(score_key, 'N/A')}/10",
                        "Input Tokens": r["input_tokens"],
                        "Output Tokens": r["output_tokens"],
                        "Total Tokens": r["input_tokens"] + r["output_tokens"],
                        "Latency (s)": f"{r['latency']:.2f}",
                    })
                st.table(data_rows)
        else:
            st.info("Run the comparison to see the AI judge verdict.")

    with tab_history:
        history = st.session_state.get("sc_history", [])
        if history:
            st.markdown("#### Strategy Win Tracker")
            st.markdown("See which strategies win for different task types to build your intuition.")

            # Win count summary
            wins = {"zero-shot": 0, "few-shot": 0, "chain-of-thought": 0, "other": 0}
            for h in history:
                w = h["winner"].lower()
                if "zero" in w:
                    wins["zero-shot"] += 1
                elif "few" in w:
                    wins["few-shot"] += 1
                elif "chain" in w or "cot" in w:
                    wins["chain-of-thought"] += 1
                else:
                    wins["other"] += 1

            win_cols = st.columns(3)
            win_cols[0].metric("Zero-shot Wins", wins["zero-shot"])
            win_cols[1].metric("Few-shot Wins", wins["few-shot"])
            win_cols[2].metric("CoT Wins", wins["chain-of-thought"])

            # History entries
            for i, h in enumerate(reversed(history)):
                scores_str = ""
                if h["scores"]:
                    parts = []
                    if h["scores"].get("zero") is not None:
                        parts.append(f"Z:{h['scores']['zero']}")
                    if h["scores"].get("few") is not None:
                        parts.append(f"F:{h['scores']['few']}")
                    if h["scores"].get("cot") is not None:
                        parts.append(f"C:{h['scores']['cot']}")
                    scores_str = " | ".join(parts)
                st.markdown(f"**{len(history) - i}.** {h['task'][:60]} → 🏆 {h['winner']} ({scores_str})")

            if st.button("🗑️ Clear History", key="sc_clear_history"):
                st.session_state["sc_history"] = []
                st.rerun()
        else:
            st.info("Run comparisons to build your strategy win history.")

    with tab_challenge:
        st.markdown("#### 🎯 Strategy Prediction Challenge")
        st.markdown(
            "Test your intuition: for each task, predict which strategy will win, "
            "then run it to check. Get 4 out of 5 correct to pass."
        )

        if "sc_challenge_state" not in st.session_state:
            st.session_state["sc_challenge_state"] = {"results": {}}

        ch_state = st.session_state["sc_challenge_state"]

        # Task selector
        task_labels = [f"Task {i+1}: {ch['task'][:50]}" for i, ch in enumerate(CHALLENGES)]
        selected_idx = st.selectbox("Select a task:", range(len(CHALLENGES)), format_func=lambda x: task_labels[x], key="sc_ch_select")
        ch = CHALLENGES[selected_idx]

        st.markdown(f"**Task:** {ch['task']}")
        if ch["input_text"]:
            st.code(ch["input_text"], language="text")

        # Prediction
        prediction = st.radio(
            "Your prediction — which strategy will win?",
            ["zero-shot", "few-shot", "chain-of-thought"],
            key=f"sc_ch_pred_{selected_idx}",
            horizontal=True,
        )

        # Run individual task
        if st.button("🚀 Run This Task", key="sc_run_single_challenge"):
            with st.spinner("Running all 3 strategies..."):
                zero_p = build_zero_shot(ch["task"], ch["input_text"])
                few_examples = FEW_SHOT_EXAMPLES.get(
                    ch["task"], FEW_SHOT_EXAMPLES[list(FEW_SHOT_EXAMPLES.keys())[0]]
                )
                few_p = build_few_shot(ch["task"], ch["input_text"], few_examples)
                cot_p = build_cot(ch["task"], ch["input_text"])

                zero_r = call_bedrock(zero_p)
                few_r = call_bedrock(few_p)
                cot_r = call_bedrock(cot_p)

            with st.spinner("AI Judge deciding winner..."):
                judge_p = (
                    f"You are a judge. Which response is best for this task?\n\n"
                    f"Task: {ch['task']}\nInput: {ch['input_text']}\n\n"
                    f"A (Zero-shot): {zero_r['text']}\n\n"
                    f"B (Few-shot): {few_r['text']}\n\n"
                    f"C (Chain-of-Thought): {cot_r['text']}\n\n"
                    f"Respond with EXACTLY one line: Winner: zero-shot OR few-shot OR chain-of-thought"
                )
                judge_r = call_bedrock(judge_p, model_id=get_judge_model_id())
                winner_text = judge_r["text"].lower()
                if "zero" in winner_text:
                    actual = "zero-shot"
                elif "few" in winner_text:
                    actual = "few-shot"
                else:
                    actual = "chain-of-thought"

            ch_state["results"][selected_idx] = {
                "prediction": prediction,
                "actual_winner": actual,
                "responses": {
                    "zero-shot": zero_r["text"],
                    "few-shot": few_r["text"],
                    "chain-of-thought": cot_r["text"],
                },
            }

        # Show result for current task
        if selected_idx in ch_state["results"]:
            r = ch_state["results"][selected_idx]
            is_correct = r["prediction"] == r["actual_winner"]
            icon = "✅" if is_correct else "❌"

            st.markdown(f"### {icon} Result")
            col_pred, col_actual = st.columns(2)
            col_pred.metric("Your Prediction", r["prediction"])
            col_actual.metric("Actual Winner", r["actual_winner"])

            with st.expander("See all responses"):
                resp_cols = st.columns(3)
                for col, strat in zip(resp_cols, ["zero-shot", "few-shot", "chain-of-thought"]):
                    with col:
                        label = f"🏆 {strat}" if strat == r["actual_winner"] else strat
                        st.markdown(f"**{label}**")
                        st.markdown(r["responses"][strat][:400] + ("..." if len(r["responses"][strat]) > 400 else ""))

        # Overall progress
        st.markdown("---")
        st.markdown("#### Overall Progress")
        completed = len(ch_state["results"])
        correct = sum(1 for r in ch_state["results"].values() if r["prediction"] == r["actual_winner"])
        total = len(CHALLENGES)

        prog_cols = st.columns(3)
        prog_cols[0].metric("Completed", f"{completed}/{total}")
        prog_cols[1].metric("Correct", f"{correct}/{completed}" if completed > 0 else "—")
        prog_cols[2].metric("Status", "🎉 Passed!" if correct >= 4 and completed == total else f"Need 4/{total}")

        # Per-task status
        for i, c in enumerate(CHALLENGES):
            if i in ch_state["results"]:
                r = ch_state["results"][i]
                icon = "✅" if r["prediction"] == r["actual_winner"] else "❌"
                st.markdown(f"{icon} Task {i+1}: {c['task'][:50]} — predicted **{r['prediction']}**, actual **{r['actual_winner']}**")
            else:
                st.markdown(f"⬜ Task {i+1}: {c['task'][:50]} — *not yet attempted*")

        if completed == total and correct >= 4:
            st.success("🎉 Challenge passed! You have strong strategy intuition.")
        elif completed == total:
            st.warning(f"Score: {correct}/{total}. Need ≥ 4 correct. Review the strategy tips and try again.")

        if st.button("🔄 Reset Challenge", key="sc_reset_challenge"):
            st.session_state["sc_challenge_state"] = {"results": {}}
            st.rerun()

    create_footer()



main()
