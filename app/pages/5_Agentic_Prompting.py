import streamlit as st
from utils.bedrock_client import invoke_model, invoke_model_with_tools
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Agentic Prompting & Tool Use", page_icon="🤖", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

with main_col:
    st.title("🤖 Agentic Prompting & Tool Use")
    st.markdown("Agentic AI = prompting + **tool use** + **planning** + **iterative reasoning**.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 ReAct", "🔧 Function Calling", "🧬 Strands Agent", "🏗️ Context Engineering"
    ])

    # --- Tab 1: ReAct ---
    with tab1:
        st.markdown("""
The **ReAct** pattern interleaves:
- **Thought** — reason about what to do next
- **Action** — decide which tool to call
- **Observation** — result feeds back into reasoning
""")
        react_prompt = st.text_area(
            "ReAct-style prompt:",
            value="""You are a helpful assistant using the ReAct format (Thought/Action/Observation).
Tools: search(query), calculate(expression), lookup(term)

Question: What is the population of France multiplied by 2?

Thought 1: I need to find the population of France.
Action 1: search("population of France 2024")
Observation 1: Approximately 68 million.

Thought 2: Now multiply by 2.
Action 2: calculate("68000000 * 2")
Observation 2: 136000000

Final Answer: 136 million.

---
Now answer: If a company has 5,000 employees and each produces $200,000 in revenue, what is the total revenue in billions?""",
            height=320, key="react_prompt",
        )
        if st.button("Run ReAct", key="run_react"):
            with st.spinner("Reasoning and acting..."):
                st.success(invoke_model(react_prompt, temperature=0.3))

    # --- Tab 2: Function Calling ---
    with tab2:
        st.markdown("""
**Function Calling** allows the model to invoke structured tools with typed parameters.
Bedrock's Converse API supports this natively via `toolConfig`.
""")
        tools = [
            {"toolSpec": {"name": "get_weather", "description": "Get current weather for a location.", "inputSchema": {"json": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["location"]}}}},
            {"toolSpec": {"name": "calculate", "description": "Perform a math calculation.", "inputSchema": {"json": {"type": "object", "properties": {"expression": {"type": "string", "description": "Math expression"}}, "required": ["expression"]}}}},
            {"toolSpec": {"name": "search_database", "description": "Search a product database.", "inputSchema": {"json": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}}}},
        ]
        st.markdown("**Defined Tools:** " + ", ".join([f"`{t['toolSpec']['name']}`" for t in tools]))
        tool_prompt = st.text_area(
            "User message (model decides which tool to call):",
            value="What's the weather like in Seattle? Also, calculate 15% tip on a $85 dinner bill.",
            height=80, key="tool_prompt",
        )
        if st.button("Run with Tools", key="run_tools"):
            with st.spinner("Model deciding tools..."):
                response = invoke_model_with_tools(
                    prompt=tool_prompt,
                    system_prompt="You are a helpful assistant. Use the available tools to answer.",
                    tools=tools,
                )
            if "error" in response:
                st.error(f"Error: {response['error']}")
            else:
                message = response.get("output", {}).get("message", {})
                for block in message.get("content", []):
                    if "text" in block:
                        st.markdown(f"**Text:** {block['text']}")
                    elif "toolUse" in block:
                        st.markdown(f"🔧 **Tool Call:** `{block['toolUse']['name']}`")
                        st.json(block["toolUse"].get("input", {}))
                st.caption(f"Stop reason: {response.get('stopReason', 'unknown')} — In a real agent, you'd execute the tool and feed results back.")

    # --- Tab 3: Strands Agent ---
    with tab3:
        st.markdown("""
**[Strands Agents SDK](https://strandsagents.com/)** is AWS's open-source framework for building AI agents.
It provides a model-driven approach with automatic tool selection and execution loops.

Key features:
- Automatic **agent loop** (reason → tool call → observe → repeat)
- Built-in tools (`calculator`, `current_time`, etc.)
- Custom tools via `@tool` decorator
- Native **Amazon Bedrock** integration
- Observability with traces and metrics
""")

        st.markdown("---")

        st.markdown("#### Agent Code")
        st.code('''from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, current_time

# Custom tool
@tool
def word_count(text: str) -> int:
    """Count the number of words in a text.

    Args:
        text: The input text to count words in.

    Returns:
        The number of words.
    """
    return len(text.split())

# Create agent with Bedrock model
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-east-1",
)

agent = Agent(
    model=model,
    tools=[calculator, current_time, word_count],
    system_prompt="You are a helpful assistant. Use tools when needed.",
)

# Run the agent
result = agent("What time is it and what is 42 * 17?")
''', language="python")

        st.markdown("---")
        st.markdown("#### Live Demo")

        agent_prompt = st.text_area(
            "Ask the Strands agent:",
            value="What is the current time? Also calculate 1234 * 5678 and tell me the square root of 144.",
            height=80,
            key="strands_prompt",
        )

        model_id = st.session_state.get("selected_model_id", "amazon.nova-lite-v1:0")
        region = st.session_state.get("aws_region", "us-east-1")

        if st.button("🚀 Run Strands Agent", key="run_strands", type="primary"):
            with st.spinner("Agent is thinking and using tools..."):
                try:
                    from strands import Agent, tool
                    from strands.models import BedrockModel
                    from strands_tools import calculator, current_time

                    @tool
                    def word_count(text: str) -> int:
                        """Count the number of words in a text.

                        Args:
                            text: The input text to count words in.

                        Returns:
                            The number of words.
                        """
                        return len(text.split())

                    bedrock_model = BedrockModel(
                        model_id=model_id,
                        region_name=region,
                    )

                    agent = Agent(
                        model=bedrock_model,
                        tools=[calculator, current_time, word_count],
                        system_prompt="You are a helpful assistant. Use your tools when needed to answer questions accurately.",
                        callback_handler=None,
                    )

                    result = agent(agent_prompt)

                    # Display result
                    st.markdown("**🤖 Agent Response:**")
                    st.success(str(result))

                    # Display metrics
                    if hasattr(result, "metrics"):
                        metrics = result.metrics.get_summary()
                        st.markdown("---")
                        st.markdown("**📊 Agent Metrics:**")
                        met_cols = st.columns(4)
                        usage = metrics.get("accumulated_usage", {})
                        with met_cols[0]:
                            st.metric("Cycles", metrics.get("total_cycles", "N/A"))
                        with met_cols[1]:
                            st.metric("Input Tokens", usage.get("inputTokens", "N/A"))
                        with met_cols[2]:
                            st.metric("Output Tokens", usage.get("outputTokens", "N/A"))
                        with met_cols[3]:
                            duration = metrics.get("total_duration", 0)
                            st.metric("Duration", f"{duration:.1f}s")

                        # Tool usage
                        tool_usage = metrics.get("tool_usage", {})
                        if tool_usage:
                            st.markdown("**🔧 Tools Used:**")
                            for tool_name, info in tool_usage.items():
                                stats = info.get("execution_stats", {})
                                st.markdown(
                                    f"- `{tool_name}` — called {stats.get('call_count', 0)}x, "
                                    f"success rate: {stats.get('success_rate', 0)*100:.0f}%"
                                )

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # --- Tab 4: Context Engineering ---
    with tab4:
        st.markdown("""
**Context Engineering** is designing the full context window:
- System prompt with role and constraints
- Tool definitions
- Retrieved knowledge (RAG)
- Conversation history and state
- Output format instructions
""")
        system_prompt_example = st.text_area(
            "System prompt (context engineering example):",
            value="""You are a senior financial analyst AI assistant at a Fortune 500 company.

## Role & Constraints
- You provide data-driven insights only
- Never give investment advice or predictions
- Always cite your reasoning
- If uncertain, say so explicitly

## Available Tools
- query_database(sql): Run read-only SQL queries
- get_market_data(ticker, period): Fetch market data
- generate_chart(data, chart_type): Create a visualization

## Output Format
- Use markdown tables for comparisons
- Include confidence levels (high/medium/low)
- End with "Limitations" section

## Current Context
- Date: 2024-Q4
- User role: VP of Strategy
- Access level: Full financial data""",
            height=300, key="context_eng",
        )
        context_user_msg = st.text_area(
            "User message:",
            value="How did our cloud spending trend over the last 4 quarters?",
            height=60, key="context_user",
        )
        if st.button("Run with Engineered Context", key="run_context"):
            with st.spinner("Generating..."):
                result = invoke_model(context_user_msg, system_prompt=system_prompt_example, temperature=0.3)
            st.write(result)
