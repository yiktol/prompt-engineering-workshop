import streamlit as st
import boto3
import time
import json
import re
import plotly.graph_objects as go
from utils.styles import load_css, sub_header, create_footer, AWS_COLORS
from utils.common import (
    render_sidebar,
    render_generator_model_selector,
    get_generator_model_id,
    render_judge_model_selector,
    get_judge_model_id,
)


st.set_page_config(page_title="Iterative Refinement Lab", page_icon="🔄", layout="wide")

@st.cache_resource
def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Scenario tracks
# ---------------------------------------------------------------------------
TRACKS = {
    "Marketing Slogan": {
        "description": "Iterate on a creative marketing slogan for a tech-themed coffee shop.",
        "judge_criteria": "memorability, relevance, conciseness",
        "steps": [
            {
                "title": "Step 1: Basic Prompt",
                "technique": "Baseline",
                "explanation": "Start with the simplest possible prompt. No context, no constraints. This establishes a baseline.",
                "default_prompt": "Write a slogan for a coffee shop.",
            },
            {
                "title": "Step 2: Add Context",
                "technique": "Context Injection",
                "explanation": "Add context about the business. The model can't read your mind — details improve relevance.",
                "default_prompt": (
                    "Write a slogan for a coffee shop called 'ByteBrew' that caters to software developers "
                    "and is located in a tech hub. The shop offers specialty coffee and has coding-themed decor."
                ),
            },
            {
                "title": "Step 3: Specify Tone",
                "technique": "Tone Specification",
                "explanation": "Define the tone and style. Be explicit about the emotional register.",
                "default_prompt": (
                    "Write a slogan for 'ByteBrew', a coffee shop for software developers in a tech hub. "
                    "Tone: clever and witty, with a subtle tech pun. Should feel modern and energetic, "
                    "not corporate or cheesy."
                ),
            },
            {
                "title": "Step 4: Add Few-shot Examples",
                "technique": "Few-shot Examples",
                "explanation": "Show the model what good looks like. Examples calibrate quality, length, and style.",
                "default_prompt": (
                    "Write a slogan for 'ByteBrew', a coffee shop for software developers in a tech hub.\n"
                    "Tone: clever and witty, with a subtle tech pun. Modern and energetic.\n\n"
                    "Examples of great coffee shop slogans:\n"
                    "- 'Life happens, coffee helps.' (simple, relatable)\n"
                    "- 'Fuel your passion.' (short, energetic)\n"
                    "- 'Where ideas percolate.' (metaphor, clever)\n\n"
                    "Now write one for ByteBrew:"
                ),
            },
            {
                "title": "Step 5: Add Constraints",
                "technique": "Constraint Setting",
                "explanation": "Set boundaries: word count, format, what to avoid. Constraints focus the output.",
                "default_prompt": (
                    "Write a slogan for 'ByteBrew', a coffee shop for software developers.\n"
                    "Tone: clever, witty, modern.\n\n"
                    "Constraints:\n"
                    "- Maximum 8 words\n"
                    "- Must include a subtle tech/coding pun\n"
                    "- Must sound natural when spoken aloud\n"
                    "- Do NOT use: 'brew', 'byte', 'code' (too obvious)\n\n"
                    "Examples of good slogans:\n"
                    "- 'Where ideas percolate.'\n"
                    "- 'Debug your morning.'\n\n"
                    "Write one slogan:"
                ),
            },
            {
                "title": "Step 6: Full Production Prompt",
                "technique": "XML Structure + Output Format",
                "explanation": "Combines all techniques with clear delimiters and structured output instructions.",
                "default_prompt": (
                    "<instruction>\nGenerate a marketing slogan for the coffee shop described below.\n</instruction>\n\n"
                    "<context>\nBusiness: ByteBrew — specialty coffee for software developers\n"
                    "Location: Tech hub, surrounded by startups\nVibe: Modern, energetic, community-oriented\n"
                    "USP: Coding-themed drinks, fast WiFi, quiet zones for deep work\n</context>\n\n"
                    "<constraints>\n- Maximum 8 words\n- Must include a subtle tech pun\n"
                    "- Tone: clever, witty, modern (NOT corporate or cheesy)\n"
                    "- Must be memorable when spoken aloud\n"
                    "- Do NOT use: 'brew', 'byte', 'code' (too obvious)\n</constraints>\n\n"
                    "<examples>\n- 'Where ideas percolate.' (metaphor, clever)\n"
                    "- 'Debug your morning.' (tech pun, short)\n</examples>\n\n"
                    "<output_format>\nProvide exactly 3 slogan options.\n"
                    "For each, write the slogan and one sentence explaining why it works.\n"
                    "Then state your top pick and why.\n</output_format>"
                ),
            },
        ],
    },
    "API Documentation": {
        "description": "Iterate on writing clear API endpoint documentation.",
        "judge_criteria": "clarity, completeness, developer-friendliness",
        "steps": [
            {
                "title": "Step 1: Basic Prompt",
                "technique": "Baseline",
                "explanation": "A vague request with no structure. See what you get.",
                "default_prompt": "Write documentation for a REST API endpoint.",
            },
            {
                "title": "Step 2: Add Context",
                "technique": "Context Injection",
                "explanation": "Specify the endpoint, method, and purpose.",
                "default_prompt": (
                    "Write documentation for a REST API endpoint:\n"
                    "POST /api/v2/users — Creates a new user account.\n"
                    "The API is for a SaaS project management platform."
                ),
            },
            {
                "title": "Step 3: Specify Audience",
                "technique": "Tone Specification",
                "explanation": "Define who reads this — junior devs? Experienced backend engineers?",
                "default_prompt": (
                    "Write documentation for POST /api/v2/users (create user) for a project management SaaS.\n"
                    "Audience: experienced backend developers integrating via REST.\n"
                    "Tone: concise, technical, no hand-holding. Get to the point."
                ),
            },
            {
                "title": "Step 4: Add Examples",
                "technique": "Few-shot Examples",
                "explanation": "Provide a sample request/response to define the format you want.",
                "default_prompt": (
                    "Write documentation for POST /api/v2/users.\n"
                    "Audience: experienced backend developers.\n\n"
                    "Include these sections: Description, Request Body, Response, Error Codes.\n\n"
                    "Example format:\n"
                    "### POST /api/v2/projects\n"
                    "Creates a new project.\n"
                    "**Request Body:**\n```json\n{\"name\": \"string\", \"team_id\": \"uuid\"}\n```\n"
                    "**Response (201):**\n```json\n{\"id\": \"uuid\", \"name\": \"...\", \"created_at\": \"ISO8601\"}\n```\n"
                    "**Errors:** 400 (validation), 401 (unauthorized), 409 (duplicate)\n\n"
                    "Now write the same format for POST /api/v2/users:"
                ),
            },
            {
                "title": "Step 5: Add Constraints",
                "technique": "Constraint Setting",
                "explanation": "Define field types, required vs optional, and validation rules.",
                "default_prompt": (
                    "Write documentation for POST /api/v2/users.\n\n"
                    "Fields: email (required, string, valid email), name (required, string, 2-100 chars), "
                    "role (optional, enum: admin|member|viewer, default: member), "
                    "team_id (required, uuid).\n\n"
                    "Constraints:\n"
                    "- Include request body with types\n- Include success response (201)\n"
                    "- Include all error codes (400, 401, 403, 409)\n"
                    "- Include a curl example\n- Under 300 words total"
                ),
            },
            {
                "title": "Step 6: Full Production Prompt",
                "technique": "XML Structure + Output Format",
                "explanation": "Fully structured prompt with delimiters and exact output spec.",
                "default_prompt": (
                    "<instruction>\nWrite REST API documentation for the endpoint below.\n</instruction>\n\n"
                    "<endpoint>\nPOST /api/v2/users\nPurpose: Create a new user account\n"
                    "Auth: Bearer token (required)\n</endpoint>\n\n"
                    "<fields>\n- email: string, required, must be valid email format\n"
                    "- name: string, required, 2-100 characters\n"
                    "- role: enum [admin, member, viewer], optional, default: member\n"
                    "- team_id: uuid, required, must reference existing team\n</fields>\n\n"
                    "<constraints>\n- Include: description, request body, success response, error table, curl example\n"
                    "- Under 300 words\n- Use markdown formatting\n- Be concise and technical\n</constraints>\n\n"
                    "<output_format>\nUse this structure:\n## POST /api/v2/users\n[description]\n"
                    "### Request Body\n[fields with types]\n### Response (201)\n[example response]\n"
                    "### Errors\n[table: code | condition]\n### Example\n[curl command]\n</output_format>"
                ),
            },
        ],
    },
    "Bug Report Summary": {
        "description": "Iterate on extracting structured summaries from raw bug reports.",
        "judge_criteria": "accuracy, completeness, structure",
        "steps": [
            {
                "title": "Step 1: Basic Prompt",
                "technique": "Baseline",
                "explanation": "A minimal request — see how the model handles ambiguity.",
                "default_prompt": "Summarize this bug report:\n\nUser says login page crashes on mobile after the latest update.",
            },
            {
                "title": "Step 2: Add Context",
                "technique": "Context Injection",
                "explanation": "Provide the full bug report with details.",
                "default_prompt": (
                    "Summarize this bug report:\n\n"
                    "Reporter: jane.doe@company.com\nDate: 2024-03-15\nSeverity: High\n"
                    "Environment: iOS 17.3, Safari, iPhone 15 Pro\n\n"
                    "Description: After updating to v2.4.1, the login page crashes immediately when "
                    "tapping the 'Sign In' button. The page goes white, then Safari shows 'A problem "
                    "occurred with this webpage.' Happens 100% of the time. Works fine on desktop Chrome. "
                    "Cleared cache, restarted phone — same issue. Other users in #support-mobile confirm."
                ),
            },
            {
                "title": "Step 3: Specify Format",
                "technique": "Tone Specification",
                "explanation": "Define the audience (engineering team) and format expectations.",
                "default_prompt": (
                    "You are a QA lead preparing a bug summary for the engineering sprint planning.\n\n"
                    "Summarize this bug report in a format suitable for a Jira ticket:\n\n"
                    "[same bug report as Step 2]\n\n"
                    "Be technical and concise. Focus on reproduction steps and impact."
                ),
            },
            {
                "title": "Step 4: Add Examples",
                "technique": "Few-shot Examples",
                "explanation": "Show the exact output format via example.",
                "default_prompt": (
                    "Summarize bug reports into structured Jira ticket format.\n\n"
                    "Example:\nInput: 'Dashboard charts don't load on Firefox 120. Shows spinner forever.'\n"
                    "Output:\n**Title:** Dashboard charts infinite loading on Firefox 120\n"
                    "**Severity:** Medium | **Component:** Dashboard\n"
                    "**Steps:** 1. Open dashboard 2. Observe charts area\n"
                    "**Expected:** Charts load within 3s\n**Actual:** Infinite spinner\n"
                    "**Affected:** Firefox 120+ | **Workaround:** Use Chrome\n\n"
                    "Now summarize this:\n[full bug report from Step 2]"
                ),
            },
            {
                "title": "Step 5: Add Constraints",
                "technique": "Constraint Setting",
                "explanation": "Add field requirements and length limits.",
                "default_prompt": (
                    "Summarize into Jira format. Required fields:\n"
                    "- Title (under 80 chars)\n- Severity (Critical/High/Medium/Low)\n"
                    "- Component\n- Steps to Reproduce (numbered)\n- Expected vs Actual\n"
                    "- Affected platforms\n- Workaround (if any)\n- Regression? (yes/no + version)\n\n"
                    "[full bug report]\n\nDo NOT include opinions or speculation."
                ),
            },
            {
                "title": "Step 6: Full Production Prompt",
                "technique": "XML Structure + Output Format",
                "explanation": "Complete structured prompt with delimiters.",
                "default_prompt": (
                    "<instruction>\nExtract a structured bug summary from the raw report below.\n</instruction>\n\n"
                    "<context>\nYou are a QA automation system processing bug reports for sprint planning.\n"
                    "Output must be clear, structured, and actionable for engineers.\n</context>\n\n"
                    "<bug_report>\nReporter: jane.doe@company.com\nDate: 2024-03-15\nSeverity: High\n"
                    "Environment: iOS 17.3, Safari, iPhone 15 Pro\nDescription: After updating to v2.4.1, "
                    "login page crashes on tap 'Sign In'. White screen, Safari error. 100% repro. "
                    "Desktop Chrome OK. Cache cleared. Confirmed by multiple users.\n</bug_report>\n\n"
                    "<output_format>\nUse this structure:\n"
                    "**Title:** [under 80 chars]\n"
                    "**Severity:** [Critical/High/Medium/Low] | **Component:** [area]\n"
                    "**Steps to Reproduce:**\n1. ...\n2. ...\n"
                    "**Expected:** [what should happen]\n"
                    "**Actual:** [what happens instead]\n"
                    "**Affected:** [platforms/versions]\n"
                    "**Workaround:** [if any, else 'None known']\n"
                    "**Regression:** [Yes/No, since version]\n</output_format>"
                ),
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# Technique reference
# ---------------------------------------------------------------------------
TECHNIQUES = {
    "Baseline": "No technique — establishes a reference point for measuring improvement.",
    "Context Injection": "Provide background info: who, what, where, why. The model can't infer what you don't say.",
    "Tone Specification": "Define voice, audience, and emotional register explicitly.",
    "Few-shot Examples": "Show 1-3 examples of desired output to calibrate format and quality.",
    "Constraint Setting": "Set boundaries: length, format, inclusions/exclusions, what to avoid.",
    "XML Structure + Output Format": "Use delimiters to separate sections and specify exact output schema.",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def call_bedrock(prompt, model_id=None):
    client = get_bedrock_client()
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    try:
        start = time.time()
        response = client.converse(modelId=model_id or get_generator_model_id(), messages=messages)
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


def judge_quality(response_text, track_criteria, judge_model_id=None):
    """Judge response quality on track-specific criteria. Returns scores dict + suggestion."""
    criteria_list = [c.strip() for c in track_criteria.split(",")]
    criteria_str = "\n".join(f"- {c}: rate 1-10" for c in criteria_list)

    judge_prompt = (
        f"You are an expert evaluator. Rate the following response on these criteria:\n"
        f"{criteria_str}\n\n"
        f"Response to rate:\n{response_text}\n\n"
        f"You MUST respond in EXACTLY this JSON format (no other text):\n"
        "{"
        + ", ".join(f'"{c}": N' for c in criteria_list)
        + ', "overall": N, "suggestion": "one sentence on what to improve next"'
        + "}\n"
        f"Where overall is the average of all scores rounded to one decimal."
    )
    result = call_bedrock(judge_prompt, model_id=judge_model_id)
    try:
        text = result["text"].strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        scores = json.loads(text)
        # Ensure all criteria present
        for c in criteria_list:
            if c not in scores:
                scores[c] = 5.0
            scores[c] = float(scores[c])
        if "overall" not in scores:
            scores["overall"] = sum(scores[c] for c in criteria_list) / len(criteria_list)
        scores["overall"] = float(scores["overall"])
        if "suggestion" not in scores:
            scores["suggestion"] = "Try adding more specificity."
        return scores
    except (json.JSONDecodeError, KeyError, ValueError, IndexError):
        default = {c: 5.0 for c in criteria_list}
        default["overall"] = 5.0
        default["suggestion"] = "Could not parse judge response."
        return default


def compute_diff_additions(prev_prompt, curr_prompt):
    """Return lines added in curr_prompt that aren't in prev_prompt."""
    prev_lines = set(prev_prompt.strip().splitlines())
    curr_lines = curr_prompt.strip().splitlines()
    additions = [line for line in curr_lines if line not in prev_lines and line.strip()]
    return additions


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    load_css()

    with st.sidebar:
        render_sidebar()
        render_generator_model_selector()
        render_judge_model_selector()
        if st.button("🗑️ Clear All", key="ir_clear_all"):
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("ir_")]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown(sub_header("Iterative Refinement Lab", icon="🔄"), unsafe_allow_html=True)
    st.markdown(
        "**Key Concept:** Prompt engineering is systematic iteration, not guesswork. "
        "Each refinement adds a specific technique that measurably improves quality."
    )

    # --- Technique reference ---
    with st.expander("💡 Technique Toolkit", expanded=False):
        for technique, desc in TECHNIQUES.items():
            st.markdown(f"- **{technique}:** {desc}")

    # --- Track selection ---
    def _on_track_change():
        # Clear results when switching tracks
        for key in list(st.session_state.keys()):
            if key.startswith("ir_") and key not in ["ir_track"]:
                st.session_state.pop(key, None)

    track_name = st.selectbox(
        "Select a scenario track:",
        list(TRACKS.keys()),
        key="ir_track",
        on_change=_on_track_change,
    )
    track = TRACKS[track_name]
    st.caption(f"📋 {track['description']} | Judge criteria: {track['judge_criteria']}")

    steps = track["steps"]
    total_steps = len(steps)

    # --- State init ---
    if "ir_current_step" not in st.session_state:
        st.session_state["ir_current_step"] = 0
    if "ir_results" not in st.session_state:
        st.session_state["ir_results"] = {}
    if "ir_scores" not in st.session_state:
        st.session_state["ir_scores"] = {}

    current_step = st.session_state["ir_current_step"]
    # Clamp in case track changed
    if current_step >= total_steps:
        current_step = 0
        st.session_state["ir_current_step"] = 0

    # --- Progress & navigation ---
    st.progress((current_step + 1) / total_steps, text=f"Step {current_step + 1} of {total_steps}")

    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("⬅️ Previous", disabled=(current_step == 0), key="ir_prev"):
            st.session_state["ir_current_step"] = max(0, current_step - 1)
            st.rerun()
    with col_info:
        step = steps[current_step]
        st.markdown(f"### {step['title']}")
    with col_next:
        if st.button("Next ➡️", disabled=(current_step >= total_steps - 1), key="ir_next"):
            st.session_state["ir_current_step"] = min(total_steps - 1, current_step + 1)
            st.rerun()

    # Technique badge + explanation
    st.markdown(f"🏷️ **Technique:** {step['technique']}")
    st.info(f"💡 {step['explanation']}")

    # --- Diff view: what changed from previous step ---
    if current_step > 0:
        prev_prompt = steps[current_step - 1]["default_prompt"]
        curr_prompt = step["default_prompt"]
        additions = compute_diff_additions(prev_prompt, curr_prompt)
        if additions:
            with st.expander(f"🔍 What's new in this step ({len(additions)} lines added)", expanded=False):
                for line in additions:
                    st.markdown(f"```diff\n+ {line}\n```")

    # --- Prompt editor ---
    prompt = st.text_area(
        "Edit the prompt:",
        value=step["default_prompt"],
        height=180,
        key=f"ir_prompt_{current_step}",
    )

    # Token estimate
    est_tokens = max(1, len(prompt) // 4)
    st.caption(f"📊 ~{est_tokens} tokens | {len(prompt)} characters")

    # --- Generate ---
    if st.button("🚀 Generate", type="primary", key=f"ir_generate_{current_step}"):
        with st.spinner("Calling Bedrock..."):
            result = call_bedrock(prompt)
            st.session_state["ir_results"][current_step] = result

        with st.spinner("AI Judge scoring..."):
            scores = judge_quality(result["text"], track["judge_criteria"], judge_model_id=get_judge_model_id())
            st.session_state["ir_scores"][current_step] = scores

    # --- Display result ---
    if current_step in st.session_state["ir_results"]:
        result = st.session_state["ir_results"][current_step]
        st.markdown("**Response:**")
        st.markdown(result["text"])
        st.caption(
            f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out | "
            f"Latency: {result['latency']:.2f}s"
        )

        if current_step in st.session_state["ir_scores"]:
            scores = st.session_state["ir_scores"][current_step]
            criteria_list = [c.strip() for c in track["judge_criteria"].split(",")]

            st.markdown("---")
            st.markdown("#### 📊 Quality Score")
            score_cols = st.columns(len(criteria_list) + 1)
            for i, c in enumerate(criteria_list):
                score_cols[i].metric(c.title(), f"{scores.get(c, 5):.1f}/10")
            score_cols[-1].metric("Overall", f"{scores['overall']:.1f}/10")

            # Suggestion from judge
            if scores.get("suggestion"):
                st.info(f"💡 **Next improvement:** {scores['suggestion']}")

    # --- Quality progression chart ---
    st.markdown("---")
    if st.session_state["ir_scores"]:
        st.markdown("### 📈 Quality Progression")
        step_numbers = sorted(st.session_state["ir_scores"].keys())
        criteria_list = [c.strip() for c in track["judge_criteria"].split(",")]

        fig = go.Figure()
        overall_scores = [st.session_state["ir_scores"][s]["overall"] for s in step_numbers]
        fig.add_trace(go.Scatter(
            x=[f"Step {s+1}" for s in step_numbers],
            y=overall_scores,
            mode="lines+markers",
            name="Overall",
            line=dict(width=3),
            marker=dict(size=10),
        ))
        for c in criteria_list:
            c_scores = [st.session_state["ir_scores"][s].get(c, 5) for s in step_numbers]
            fig.add_trace(go.Scatter(
                x=[f"Step {s+1}" for s in step_numbers],
                y=c_scores,
                mode="lines+markers",
                name=c.title(),
                line=dict(width=2, dash="dash"),
            ))
        fig.update_layout(
            xaxis_title="Step",
            yaxis_title="Score (1-10)",
            yaxis=dict(range=[0, 10.5]),
            height=300,
            margin=dict(t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Token cost progression
        if len(step_numbers) >= 2:
            token_data = []
            for s in step_numbers:
                r = st.session_state["ir_results"].get(s)
                if r:
                    token_data.append({
                        "step": f"Step {s+1}",
                        "input_tokens": r["input_tokens"],
                        "output_tokens": r["output_tokens"],
                        "quality": st.session_state["ir_scores"][s]["overall"],
                    })
            if token_data:
                st.markdown("#### Token Cost vs Quality")
                cost_cols = st.columns(len(token_data))
                for i, td in enumerate(token_data):
                    total = td["input_tokens"] + td["output_tokens"]
                    efficiency = td["quality"] / total * 100 if total > 0 else 0
                    cost_cols[i].metric(
                        td["step"],
                        f"{total} tokens",
                        help=f"Quality: {td['quality']:.1f}/10 | Efficiency: {efficiency:.2f}"
                    )

    # --- Before & After comparison (on final step) ---
    if current_step == total_steps - 1 and 0 in st.session_state["ir_results"] and (total_steps - 1) in st.session_state["ir_results"]:
        st.markdown("---")
        st.markdown("### 🏁 Before & After Comparison")
        col_before, col_after = st.columns(2)
        with col_before:
            st.markdown("**Step 1 (Basic):**")
            st.markdown(st.session_state["ir_results"][0]["text"])
            if 0 in st.session_state["ir_scores"]:
                st.metric("Score", f"{st.session_state['ir_scores'][0]['overall']:.1f}/10")
        with col_after:
            st.markdown(f"**Step {total_steps} (Refined):**")
            st.markdown(st.session_state["ir_results"][total_steps - 1]["text"])
            if (total_steps - 1) in st.session_state["ir_scores"]:
                score_before = st.session_state["ir_scores"].get(0, {}).get("overall", 0)
                score_after = st.session_state["ir_scores"][total_steps - 1]["overall"]
                delta = score_after - score_before
                st.metric("Score", f"{score_after:.1f}/10", delta=f"{delta:+.1f}")

        st.success(
            f"🎉 You've systematically improved a prompt through {total_steps} iterations! "
            "Each step added a specific technique: context, tone, examples, constraints, and structure."
        )

    # --- Export summary ---
    if len(st.session_state.get("ir_scores", {})) >= 2:
        with st.expander("📋 Export Summary", expanded=False):
            st.markdown("### Iteration Summary")
            for s in sorted(st.session_state["ir_scores"].keys()):
                step_info = steps[s] if s < len(steps) else {}
                score = st.session_state["ir_scores"][s]
                st.markdown(f"**{step_info.get('title', f'Step {s+1}')}** — Technique: {step_info.get('technique', 'N/A')} | Score: {score['overall']:.1f}/10")
                if s in st.session_state["ir_results"]:
                    with st.expander(f"Prompt & Response (Step {s+1})", expanded=False):
                        prompt_key = f"ir_prompt_{s}"
                        if prompt_key in st.session_state:
                            st.code(st.session_state[prompt_key], language="text")
                        st.markdown(f"**Response:** {st.session_state['ir_results'][s]['text'][:300]}...")

    # --- Challenge Mode ---
    st.markdown("---")
    st.markdown("### 🎯 Challenge Mode")
    with st.expander("🎯 Iterative Refinement Challenge", expanded=False):
        st.markdown(
            "**Goal:** Start with a basic prompt and reach an overall score of **≥ 8.5/10** "
            "in **4 iterations or fewer**. Each iteration, you refine the prompt based on judge feedback."
        )
        st.markdown(f"**Track:** {track_name} | **Judge criteria:** {track['judge_criteria']}")

        if "ir_challenge" not in st.session_state:
            st.session_state["ir_challenge"] = {"attempts": [], "passed": False}

        ch = st.session_state["ir_challenge"]
        attempts_used = len(ch["attempts"])
        max_attempts = 4

        if not ch["passed"] and attempts_used < max_attempts:
            ch_prompt = st.text_area(
                f"Your prompt (iteration {attempts_used + 1}/{max_attempts}):",
                height=150,
                key="ir_ch_prompt",
                placeholder="Write or refine your prompt here...",
            )

            if st.button(f"🚀 Submit Iteration ({max_attempts - attempts_used} remaining)", key="ir_ch_run"):
                if not ch_prompt.strip():
                    st.warning("Enter a prompt first.")
                else:
                    with st.spinner("Generating and judging..."):
                        result = call_bedrock(ch_prompt)
                        scores = judge_quality(result["text"], track["judge_criteria"], judge_model_id=get_judge_model_id())
                        ch["attempts"].append({
                            "prompt": ch_prompt,
                            "response": result["text"],
                            "scores": scores,
                        })
                        if scores["overall"] >= 8.5:
                            ch["passed"] = True

        # Show attempts
        if ch["attempts"]:
            for i, att in enumerate(ch["attempts"], 1):
                icon = "🎉" if att["scores"]["overall"] >= 8.5 else "📝"
                with st.expander(f"{icon} Iteration {i} — Score: {att['scores']['overall']:.1f}/10"):
                    st.code(att["prompt"], language="text")
                    st.markdown(f"**Response:** {att['response'][:300]}{'...' if len(att['response']) > 300 else ''}")
                    criteria_list = [c.strip() for c in track["judge_criteria"].split(",")]
                    score_cols = st.columns(len(criteria_list) + 1)
                    for j, c in enumerate(criteria_list):
                        score_cols[j].metric(c.title(), f"{att['scores'].get(c, 5):.1f}/10")
                    score_cols[-1].metric("Overall", f"{att['scores']['overall']:.1f}/10")
                    if att["scores"].get("suggestion"):
                        st.info(f"💡 {att['scores']['suggestion']}")

            # Status
            if ch["passed"]:
                st.success(f"🎉 Challenge passed in {len(ch['attempts'])} iteration(s)! Score: {ch['attempts'][-1]['scores']['overall']:.1f}/10")
            elif attempts_used >= max_attempts:
                best = max(att["scores"]["overall"] for att in ch["attempts"])
                st.warning(f"Challenge not passed. Best score: {best:.1f}/10 (needed ≥ 8.5). Reset and try again.")

        if st.button("🔄 Reset Challenge", key="ir_ch_reset"):
            st.session_state["ir_challenge"] = {"attempts": [], "passed": False}
            st.rerun()

    create_footer()



main()
