# Challenge Mode — Sample Answers

This document provides example prompts that should score ≥ 8/10 on the AI Judge for each challenge. Use these as a reference after attempting the challenges yourself.

---

## Challenge 1: JSON Extraction Challenge

**Scenario:** Extract structured job posting data from a recruiter's informal message.

### Sample Prompt

| Component | Content |
|-----------|---------|
| **Instruction** | Extract all job posting details from the following recruiter message and return them as a single JSON object. |
| **Context** | You are a data extraction system that parses unstructured job descriptions into structured data. Only extract information explicitly stated in the text. If a field is not mentioned, use null. |
| **Input Data** | Hi, we have an opening for a Senior Backend Engineer at Netflix in Los Angeles, offering $180k-$220k. They need 5+ years of Go experience and Kubernetes expertise. The role is hybrid, 3 days in office. Apply by June 30, 2025. |
| **Output Format** | Return valid JSON with exactly these keys: "title", "company", "location", "salary_range", "requirements", "work_model", "deadline". Use strings for all values. The "requirements" field should be an array of strings. |

### Why This Works

- **Clarity:** Single action verb ("Extract") with explicit scope ("all job posting details")
- **Context:** Defines the persona and sets a rule for missing data (use null)
- **Input Data:** Clearly separated from instruction
- **Output Format:** Specifies exact JSON keys, data types, and handles the array case

---

## Challenge 2: Concise Summary Challenge

**Scenario:** Summarize a technical quantum computing article into exactly 2 CEO-friendly sentences.

### Sample Prompt

| Component | Content |
|-----------|---------|
| **Instruction** | Summarize the following technical article into exactly 2 sentences written for a non-technical CEO. Focus on business impact and timeline, not technical mechanisms. |
| **Context** | You are a technology advisor who translates complex research into executive-friendly insights. Avoid all jargon — if a 10-year-old wouldn't understand a word, don't use it. |
| **Input Data** | Recent breakthroughs in quantum computing show significant progress: researchers achieved qubit stability for over 1 millisecond (a 10x improvement), new error correction codes reduced computational errors by 99.9%, and three major companies have announced commercial quantum services targeting 2027-2029 availability for enterprise customers. |
| **Output Format** | Return exactly 2 sentences. First sentence: what happened and why it matters. Second sentence: what it means for business timelines. Total must be under 50 words. |

### Why This Works

- **Clarity:** "Exactly 2 sentences" leaves no room for misinterpretation
- **Context:** The "10-year-old" rule provides a concrete jargon threshold
- **Input Data:** Provides the actual content to summarize
- **Output Format:** Specifies sentence count, content per sentence, and word limit

---

## Challenge 3: Tone Control Challenge

**Scenario:** Inform a loyal customer about a 20% price increase while retaining them.

### Sample Prompt

| Component | Content |
|-----------|---------|
| **Instruction** | Write a short message informing a long-term customer that their subscription price will increase by 20% starting next month. The message must retain the customer by being empathetic and offering a loyalty incentive. |
| **Context** | You are a customer success manager at a B2B SaaS company. The customer has been on the Enterprise plan for 3 years and has always been a positive, engaged user. Your tone should be warm, honest, and appreciative — never corporate or robotic. |
| **Input Data** | Customer name: Alex. Current plan: Enterprise ($500/month). New price: $600/month effective next billing cycle. Loyalty incentive available: 2 months free at the new rate, or a locked rate of $550/month for 12 months. |
| **Output Format** | Write the message in under 80 words. Structure: 1) Acknowledge their loyalty (1 sentence), 2) State the change directly (1 sentence), 3) Offer the incentive with both options (1-2 sentences), 4) Close warmly (1 sentence). Do not use bullet points. |

### Why This Works

- **Clarity:** Clear action with dual requirements (inform + retain)
- **Context:** Establishes relationship history and exact tone requirements
- **Input Data:** Provides specific numbers and incentive options — no guessing needed
- **Output Format:** Word limit enforced, structural guidance per sentence, style constraint (no bullets)

---

## General Tips for Passing Challenges

1. **Use all 4 components** — Prompts that use instruction + context + input + output format consistently score higher than those missing components.

2. **Be specific about constraints** — "Under 80 words" is better than "keep it short." "Exactly 2 sentences" is better than "be concise."

3. **Define what NOT to do** — Adding negative constraints ("no jargon", "never use bullet points", "do not include information not in the text") prevents common failure modes.

4. **Specify data types in structured output** — For JSON challenges, state whether values should be strings, arrays, numbers, or null.

5. **Give the model a persona** — "You are a customer success manager" produces better tone control than no context at all.

6. **Iterate using judge feedback** — If you score 6-7, read the prompt feedback carefully. It usually points to the exact component that needs strengthening.
