# 🧠 Prompt Engineering Workshop

A hands-on, multipage Streamlit application for demonstrating prompt engineering best practices with Amazon Bedrock models.

**Duration:** 90 minutes  
**Reference:** [Prompt Engineering Guide](https://www.promptingguide.ai/)

## Workshop Pages

| # | Page | Topics |
|---|------|--------|
| 1 | Foundations & LLM Settings | Prompt elements, temperature, top-p, general tips |
| 2 | Zero-Shot & Few-Shot | Direct prompting vs. example-based prompting |
| 3 | Chain-of-Thought & Reasoning | CoT, zero-shot CoT, self-consistency |
| 4 | Advanced Techniques | Prompt chaining, generate knowledge, tree of thoughts, meta prompting |
| 5 | Agentic Prompting & Tool Use | ReAct, function calling, agent loops, context engineering |
| 6 | Safety & Adversarial | Prompt injection, jailbreaking, defense strategies |

## Prerequisites

- Python 3.10+
- AWS account with Amazon Bedrock access enabled
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Model access granted in the Bedrock console for your chosen models

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
cd app
streamlit run Home.py
```

## Configuration

- Select your AWS region and model from the sidebar on the Home page
- The selection persists across all pages during your session

## Supported Models

All models use the **Bedrock Converse API** (`client.converse()`):

- Claude Sonnet 4 (Anthropic)
- Claude 3.5 Haiku (Anthropic)
- Amazon Nova Pro
- Amazon Nova Lite
- Amazon Nova Micro
- Llama 3.1 70B Instruct (Meta)
- Llama 3.1 8B Instruct (Meta)
- Mistral Large
- DeepSeek-R1

## Project Structure

```
app/
├── Home.py                          # Workshop intro & configuration
├── pages/
│   ├── 1_Foundations_LLM_Settings.py
│   ├── 2_Zero_Shot_Few_Shot.py
│   ├── 3_Chain_of_Thought.py
│   ├── 4_Advanced_Techniques.py
│   ├── 5_Agentic_Prompting.py
│   └── 6_Safety_Adversarial.py
└── utils/
    ├── __init__.py
    └── bedrock_client.py            # Shared Bedrock Converse API helper
```
