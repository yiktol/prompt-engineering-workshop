# Iterative Refinement Lab — Challenge Mode Sample Answers

This document provides example prompts that should score ≥ 8.5/10 on the AI Judge for the Iterative Refinement Challenge. The goal is to reach that score in 4 iterations or fewer. Use these as a reference after attempting the challenges yourself.

---

## Sample 1: Marketing Slogan Track

**Goal:** Reach ≥ 8.5/10 on memorability, relevance, and conciseness for a tech-themed coffee shop slogan.

### Iteration 1 — Establish Baseline (Expected: ~5-6/10)

```text
Write a slogan for a coffee shop called ByteBrew that caters to software developers.
```

**Why it's weak:** No tone, no constraints, no examples. The model will produce something generic.

### Iteration 2 — Add Context + Tone (Expected: ~6.5-7.5/10)

```text
Write a slogan for 'ByteBrew', a specialty coffee shop for software developers located in a tech hub.

Tone: clever and witty, with a subtle tech/coding pun. Should feel modern and energetic — not corporate, cheesy, or forced.

The slogan should feel natural when spoken aloud and be memorable enough to put on a t-shirt.
```

**What improved:** Context (audience, location, vibe) and explicit tone guidance. The "t-shirt test" gives the model a concrete quality bar.

### Iteration 3 — Add Constraints + Examples (Expected: ~7.5-8.5/10)

```text
Write a slogan for 'ByteBrew', a specialty coffee shop for developers in a tech hub.

Tone: clever, witty, modern. A subtle tech pun that doesn't try too hard.

Constraints:
- Maximum 6 words
- Must sound natural when spoken aloud
- Do NOT use these overused words: 'brew', 'byte', 'code', 'hack', 'fuel'
- No questions or exclamation marks

Examples of great slogans (for reference, not to copy):
- 'Where ideas percolate.' (metaphor, clever)
- 'Debug your morning.' (tech pun, short)
- 'Think different.' (confident, minimal)

Write exactly one slogan:
```

**What improved:** Hard word limit, banned overused words, style examples calibrate quality, single-output constraint prevents rambling.

### Iteration 4 — Full Structured Prompt (Expected: ≥ 8.5/10)

```text
<instruction>
Generate one marketing slogan for the coffee shop described below.
</instruction>

<context>
Business: ByteBrew — specialty coffee for software developers and startup teams
Location: Downtown tech hub, surrounded by startups and coworking spaces
Vibe: Modern, energetic, community-driven. Quiet focus zones + collaboration areas.
USP: Coding-themed drinks, fastest WiFi in the district, hosts weekly dev meetups
</context>

<constraints>
- Maximum 6 words
- Must include a subtle tech/programming pun or metaphor
- Tone: clever, confident, modern (NOT corporate, cheesy, or trying too hard)
- Must pass the "t-shirt test" — sounds great on merch
- Must sound natural when spoken aloud in conversation
- Do NOT use: 'brew', 'byte', 'code', 'hack', 'fuel', 'power', 'boost'
- No questions, no exclamation marks
</constraints>

<examples>
- 'Where ideas percolate.' (metaphor, natural, clever)
- 'Debug your morning.' (tech pun, concise, actionable)
</examples>

<output_format>
Return ONLY the slogan — no explanation, no alternatives, no quotation marks.
</output_format>
```

**Why this passes:**
- **Structure:** XML delimiters separate concerns cleanly — the model knows exactly what each section means
- **Specificity:** Word limit, banned words, and tone descriptors leave no room for generic output
- **Examples:** Calibrate the quality bar without being copied
- **Output control:** "ONLY the slogan" prevents padding that would hurt conciseness scores
- **Negative constraints:** Banning overused words forces genuine creativity

---

## Sample 2: API Documentation Track

**Goal:** Reach ≥ 8.5/10 on clarity, completeness, and developer-friendliness for REST API docs.

### Iteration 1 — Establish Baseline (Expected: ~4-5/10)

```text
Write documentation for a REST API endpoint that creates users.
```

**Why it's weak:** No specifics about fields, errors, or format. Output will be vague or inventive.

### Iteration 2 — Add Specifics + Audience (Expected: ~6-7/10)

```text
Write documentation for this REST API endpoint:

POST /api/v2/users — Creates a new user account

Fields:
- email (string, required)
- name (string, required)
- role (enum: admin | member | viewer, optional, defaults to "member")
- team_id (uuid, required)

Authentication: Bearer token required.
Audience: Experienced backend developers. Be concise and technical.
```

**What improved:** Concrete field definitions, auth info, and audience targeting. The model can now produce accurate docs instead of guessing.

### Iteration 3 — Add Format + Error Codes (Expected: ~7.5-8.5/10)

```text
Write documentation for POST /api/v2/users (create user account).

Auth: Bearer token (required).

Request body fields:
- email: string, required, must be valid email
- name: string, required, 2-100 characters
- role: enum [admin, member, viewer], optional, default: "member"
- team_id: uuid, required, must reference an existing team

Include these sections in this exact order:
1. One-line description
2. Request body (table: field | type | required | description)
3. Success response (201) with example JSON
4. Error codes (table: status | condition | example message)
5. curl example with all fields

Error codes to document: 400, 401, 403, 409, 422

Constraints:
- Under 250 words total
- Use markdown formatting
- Be concise — no filler phrases like "This endpoint allows you to..."
```

**What improved:** Explicit section order, table format requests, specific error codes, word limit, and anti-pattern guidance ("no filler phrases").

### Iteration 4 — Full Structured Prompt (Expected: ≥ 8.5/10)

```text
<instruction>
Write REST API reference documentation for the endpoint below. Follow the output structure exactly.
</instruction>

<endpoint>
Method: POST
Path: /api/v2/users
Purpose: Create a new user account and assign to a team
Auth: Bearer token (required, scope: users:write)
Rate limit: 100 requests/minute per API key
</endpoint>

<fields>
| Field   | Type   | Required | Validation                        |
|---------|--------|----------|-----------------------------------|
| email   | string | yes      | Valid email format, max 254 chars  |
| name    | string | yes      | 2-100 chars, no special characters |
| role    | enum   | no       | admin, member, viewer. Default: member |
| team_id | uuid   | yes      | Must reference existing team       |
</fields>

<error_codes>
- 400: Invalid request body (missing field or validation failure)
- 401: Missing or expired Bearer token
- 403: Token lacks users:write scope
- 409: Email already registered
- 422: team_id references non-existent team
</error_codes>

<constraints>
- Under 250 words total
- Use markdown with code blocks for JSON examples
- Be terse and technical — no introductory filler
- Include realistic example values in JSON (not "string" or "example")
- curl example must include Authorization header and Content-Type
</constraints>

<output_format>
## POST /api/v2/users
[one sentence description]

### Request
[field table: name | type | required | notes]

### Response (201 Created)
```json
[realistic example response with id, timestamps]
```

### Errors
[table: status | condition]

### Example
```bash
[complete curl command]
```
</output_format>
```

**Why this passes:**
- **Completeness:** Every required section is spelled out — the model can't skip anything
- **Field table in input:** Giving structured data as input produces structured output
- **Realistic values constraint:** Prevents lazy placeholders like `"string"` in JSON examples
- **Error codes pre-defined:** Ensures accuracy — the model documents what you specify, not what it invents
- **Word limit + "no filler":** Forces developer-friendly density over verbose documentation
- **curl constraint:** Requiring auth header and content-type catches a common omission

---

## Sample 3: Bug Report Summary Track

**Goal:** Reach ≥ 8.5/10 on accuracy, completeness, and structure for extracting Jira-format bug summaries.

### Iteration 1 — Establish Baseline (Expected: ~4-5/10)

```text
Summarize this bug report:

User says login page crashes on mobile after the latest update.
```

**Why it's weak:** Minimal input, no format requirements. The model will produce a freeform paragraph.

### Iteration 2 — Add Full Report + Role (Expected: ~6-7/10)

```text
You are a QA lead preparing bug tickets for sprint planning.

Summarize this bug report into a structured format suitable for Jira:

Reporter: jane.doe@company.com
Date: 2024-03-15
Severity: High
Environment: iOS 17.3, Safari, iPhone 15 Pro

Description: After updating to v2.4.1, the login page crashes immediately when tapping the 'Sign In' button. The page goes white, then Safari shows 'A problem occurred with this webpage.' Happens 100% of the time. Works fine on desktop Chrome. Cleared cache, restarted phone — same issue. Other users in #support-mobile confirm.

Be technical and concise. Focus on reproduction steps and impact.
```

**What improved:** Full bug report data, persona (QA lead), and guidance on what to prioritize. Output will be relevant but format may be inconsistent.

### Iteration 3 — Add Example + Required Fields (Expected: ~7.5-8.5/10)

```text
Extract a structured bug summary from the report below. Use the exact format shown in the example.

Example:
Input: "Dashboard charts don't load on Firefox 120. Shows spinner forever. Started after deploy on March 10."
Output:
**Title:** Dashboard charts infinite loading on Firefox 120
**Severity:** Medium | **Component:** Dashboard
**Steps:** 1. Open dashboard in Firefox 120+ 2. Observe charts section
**Expected:** Charts render within 3s
**Actual:** Infinite loading spinner, no error in console
**Affected:** Firefox 120+ (Chrome OK)
**Workaround:** Use Chrome
**Regression:** Yes, since March 10 deploy

Now extract from this report:

Reporter: jane.doe@company.com | Date: 2024-03-15
Severity: High | Environment: iOS 17.3, Safari, iPhone 15 Pro
Description: After updating to v2.4.1, login page crashes on 'Sign In' tap. White screen, Safari error message. 100% reproducible. Desktop Chrome works fine. Cache cleared, phone restarted. Confirmed by multiple users in #support-mobile.

Required fields (do not omit any):
- Title (under 80 characters)
- Severity + Component
- Steps to Reproduce (numbered)
- Expected vs Actual
- Affected platforms
- Workaround
- Regression (yes/no + version)
```

**What improved:** Concrete example defines exact format, required fields list prevents omissions, field constraints (title under 80 chars) ensure quality.

### Iteration 4 — Full Structured Prompt (Expected: ≥ 8.5/10)

```text
<instruction>
Extract a structured bug summary from the raw report below. Output must match the specified format exactly. Do not add opinions, speculation, or information not present in the report.
</instruction>

<context>
You are a QA automation system that processes raw bug reports into sprint-ready Jira tickets.
Output must be immediately usable by engineers — no ambiguity, no missing fields.
</context>

<bug_report>
Reporter: jane.doe@company.com
Date: 2024-03-15
Severity: High
Environment: iOS 17.3, Safari, iPhone 15 Pro

Description: After updating to v2.4.1, the login page crashes immediately when tapping 'Sign In'. Page goes white, Safari displays 'A problem occurred with this webpage.' Reproduction rate: 100%. Works fine on desktop Chrome. Cleared cache, restarted phone — same result. Multiple users confirm in #support-mobile channel.
</bug_report>

<constraints>
- Only include information explicitly stated in the report
- Title must be under 80 characters
- Steps must be numbered and actionable
- If workaround is not mentioned, write "None known"
- Do not speculate about root cause
</constraints>

<output_format>
**Title:** [concise description, under 80 chars]
**Severity:** [Critical/High/Medium/Low] | **Component:** [affected area]
**Environment:** [OS, browser, device]
**Steps to Reproduce:**
1. [first step]
2. [second step]
3. [observed behavior]
**Expected:** [what should happen]
**Actual:** [what happens instead]
**Reproduction Rate:** [percentage or frequency]
**Affected:** [platforms/versions affected]
**Workaround:** [if any, else "None known"]
**Regression:** [Yes/No — since which version]
</output_format>
```

**Why this passes:**
- **No-speculation rule:** Prevents the model from inventing root causes or solutions not in the data
- **Exact field template:** Every field is pre-defined — impossible to miss one
- **Constraint on missing data:** "If workaround is not mentioned, write 'None known'" handles gaps gracefully
- **Reproduction rate field:** Captures a critical detail that basic summaries often miss
- **XML structure:** Clean separation between raw data and output expectations

---

## Sample 4: Product Feature Announcement (Custom Track — Not in App)

**Goal:** Reach ≥ 8.5/10 on clarity, engagement, and informativeness for a product feature announcement email to existing users.

### Iteration 1 — Establish Baseline (Expected: ~4-5/10)

```text
Write an email announcing a new feature to our users.
```

**Why it's weak:** No feature details, no audience info, no tone or format guidance. The model will hallucinate a generic feature and produce boilerplate marketing copy.

### Iteration 2 — Add Context + Audience (Expected: ~6-7/10)

```text
Write a feature announcement email for our project management SaaS product.

New feature: AI-powered task prioritization
What it does: Automatically analyzes task urgency, dependencies, and team workload to suggest the optimal order to tackle tasks each morning.
Available: Starting next Monday for all Pro and Enterprise users.

Audience: Existing users who are project managers and team leads. They're busy and scan emails quickly.
Tone: Excited but not hypey. Professional yet friendly.
```

**What improved:** Concrete feature details, audience targeting, and tone guidance. The model can now write something relevant, but format and length may be inconsistent.

### Iteration 3 — Add Constraints + Structure (Expected: ~7.5-8.5/10)

```text
Write a feature announcement email for our project management tool.

Feature: AI-powered Task Prioritization
- Analyzes urgency, dependencies, and team workload overnight
- Presents a prioritized "Focus List" each morning at 9am
- Learns from your choices — improves over 2 weeks
- Available next Monday for Pro and Enterprise plans

Audience: Busy project managers who scan emails in under 30 seconds.
Tone: Confident, helpful, and concise. Not salesy or breathless.

Constraints:
- Subject line under 50 characters (include an emoji)
- Email body under 150 words
- Must include: what it does, when it's available, one concrete benefit, and a CTA
- Do NOT use: "revolutionary", "game-changing", "excited to announce", "we're thrilled"
- No walls of text — use short paragraphs (2-3 sentences max each)

Structure:
1. Subject line
2. One-sentence hook (the benefit, not the feature)
3. What it does (2-3 sentences)
4. When + who gets it (1 sentence)
5. CTA button text
```

**What improved:** Word limit forces scanability, banned clichés push for authentic voice, section structure ensures completeness, and the "benefit, not feature" hook guidance improves engagement.

### Iteration 4 — Full Structured Prompt (Expected: ≥ 8.5/10)

```text
<instruction>
Write a product feature announcement email following the structure and constraints below exactly.
</instruction>

<context>
Product: TaskFlow — a project management SaaS for mid-size engineering teams
Sender: Product team (not marketing — voice should be builder-to-builder)
Audience: Existing Pro/Enterprise users who are engineering managers and tech leads
Reading behavior: Mobile-first, scan in under 20 seconds, decide to read or archive immediately
</context>

<feature>
Name: AI Task Prioritization ("Focus Mode")
What: Overnight analysis of task urgency, blockers, dependencies, and team capacity
Output: A personalized "Focus List" of 5 tasks delivered at 9am each morning
Learning: Adapts to user behavior over 2 weeks — reordering based on which tasks they actually tackle first
Availability: Next Monday, auto-enabled for Pro and Enterprise plans
Limitation: Requires at least 10 active tasks to generate meaningful prioritization
</feature>

<constraints>
- Subject line: under 50 characters, include one emoji, create curiosity
- Total body: under 120 words
- Paragraphs: max 2 sentences each
- Must include: one concrete time-saving stat or example, availability date, CTA
- Do NOT use: "revolutionary", "game-changing", "excited", "thrilled", "announce", "leverage", "unlock"
- Do NOT start with "Hi [Name]" — start with the benefit
- CTA should be action-oriented (verb + outcome), not generic ("Learn more")
- Mention the limitation honestly in one short sentence (builds trust)
</constraints>

<output_format>
**Subject:** [under 50 chars with emoji]

[Hook: 1 sentence — lead with the benefit to the reader]

[Body: what it does in plain language, 2-3 short sentences]

[Availability + limitation: 1-2 sentences]

**[CTA button text]**
</output_format>
```

**Why this passes:**
- **Builder-to-builder voice:** Specifying "product team, not marketing" fundamentally shifts tone away from hype
- **Reading behavior context:** "Mobile-first, 20 seconds" forces the model to prioritize scannability
- **Banned clichés:** Removing 7 overused words forces genuine, distinctive copy
- **Honesty constraint:** Requiring the limitation to be mentioned builds trust and differentiates from generic feature spam
- **Concrete CTA guidance:** "verb + outcome" (e.g., "See your Focus List →") beats "Learn more"
- **Word limit + paragraph limit:** Double constraint ensures both brevity and visual scannability

---

## Sample 5: Technical Interview Question (Custom Track — Not in App)

**Goal:** Reach ≥ 8.5/10 on difficulty calibration, clarity, and assessment value for a senior backend engineer interview question.

### Iteration 1 — Establish Baseline (Expected: ~4-5/10)

```text
Write a technical interview question for a backend engineer.
```

**Why it's weak:** No level, no topic, no format, no evaluation criteria. Output will be a random, possibly trivial or impossibly hard question with no rubric.

### Iteration 2 — Add Context + Level (Expected: ~6-7/10)

```text
Write a technical interview question for a Senior Backend Engineer position (5+ years experience).

Topic: System design — specifically around handling high-throughput event processing.

The question should take 20-30 minutes to discuss in a live interview. It should have no single "correct" answer — instead it should reveal how the candidate thinks about tradeoffs.

The candidate will be working on our real-time analytics pipeline processing 500K events/second.
```

**What improved:** Level calibration, topic focus, time constraint, and the "tradeoffs" framing ensures the question has depth rather than being a trivia quiz.

### Iteration 3 — Add Structure + Rubric (Expected: ~7.5-8.5/10)

```text
Write a system design interview question for a Senior Backend Engineer (5+ years, distributed systems experience).

Context: The role involves building real-time analytics pipelines processing 500K events/second with <200ms p99 latency.

Question requirements:
- Should be solvable in phases (starter → depth → edge cases)
- Must involve at least 2 competing design tradeoffs
- Should be answerable at multiple levels of sophistication
- Takes 20-30 minutes for a full discussion

Include:
1. The question itself (clear scenario + specific requirements)
2. Three follow-up probes (one easy, one medium, one hard)
3. Evaluation rubric with 3 levels: "Below bar" / "Meets bar" / "Exceeds bar"

Constraints:
- Do NOT use classic overused questions (design Twitter, design URL shortener, design chat)
- Scenario must be specific enough to constrain the solution space
- Numbers must be realistic for a mid-size SaaS company
```

**What improved:** Phased difficulty structure, follow-up probes test depth, rubric makes the question usable by other interviewers, and banning overused questions forces originality.

### Iteration 4 — Full Structured Prompt (Expected: ≥ 8.5/10)

```text
<instruction>
Design one technical interview question for the role and context below. Include the question, follow-ups, and a scoring rubric.
</instruction>

<role>
Position: Senior Backend Engineer
Level: IC4 (5-8 years experience, expected to own subsystems independently)
Team: Real-time Data Platform — processes event streams for product analytics
Must-have skills: Distributed systems, stream processing, data consistency tradeoffs
</role>

<context>
The company processes 500K events/second from web/mobile clients. Current stack: Kafka, Flink, ClickHouse. Events must be queryable within 200ms of ingestion (p99). The team is evaluating whether to add exactly-once delivery guarantees, which would impact throughput.
</context>

<question_requirements>
- Scenario-based: present a realistic business problem, not an abstract design prompt
- Must involve at minimum these tradeoffs: consistency vs throughput, cost vs latency
- Solvable in layers: a junior could sketch something, a senior reveals subtle issues
- 20-30 minute discussion scope
- Do NOT use: "design Twitter", "design URL shortener", "design a chat system", or any FAANG-standard question
</question_requirements>

<constraints>
- Question text: under 100 words (interviewers read it aloud)
- Include realistic numbers (events/sec, latency targets, storage volumes)
- Follow-ups must probe different skills (one architecture, one failure modes, one scaling)
- Rubric must be specific enough that two interviewers would agree on scoring
</constraints>

<output_format>
## Question
[The scenario + what you're asking the candidate to design, under 100 words]

## Key Requirements
- [Bullet list of system requirements the candidate must address]

## Follow-up Probes
1. **[Easy — Architecture]:** [question]
2. **[Medium — Failure Modes]:** [question]  
3. **[Hard — Scale/Optimization]:** [question]

## Rubric
| Signal | Below Bar | Meets Bar | Exceeds Bar |
|--------|-----------|-----------|-------------|
| Architecture | [what this looks like] | [what this looks like] | [what this looks like] |
| Tradeoff reasoning | [what this looks like] | [what this looks like] | [what this looks like] |
| Failure handling | [what this looks like] | [what this looks like] | [what this looks like] |
</output_format>
```

**Why this passes:**
- **IC level specificity:** "IC4, owns subsystems independently" calibrates difficulty precisely — not too junior, not staff-level
- **Real stack context:** Mentioning Kafka/Flink/ClickHouse grounds the question in reality — candidates can reference real tools
- **Tradeoff requirement:** Forcing consistency-vs-throughput and cost-vs-latency ensures the question has no single right answer
- **100-word limit on question:** Forces conciseness — interviewers need to read it aloud naturally
- **Rubric table format:** Three levels × three signals gives interviewers a concrete scoring framework
- **Follow-up probe skills:** Explicitly targeting architecture, failure modes, and scaling ensures the question assesses breadth

---

## General Tips for Passing the Iterative Refinement Challenge

1. **Start simple, then layer** — Don't jump to a complex prompt on iteration 1. Start basic so you can clearly see what each addition improves. The judge feedback on iteration 1 tells you exactly what to fix.

2. **Use judge feedback directly** — The "suggestion" field from the judge is your roadmap. If it says "add more specificity about constraints," do exactly that in your next iteration.

3. **Add one technique per iteration** — The most efficient path is: baseline → context + tone → examples + constraints → full structure. Each step targets a different scoring dimension.

4. **Ban what you don't want** — Negative constraints ("do NOT use...", "never include...") are often more powerful than positive ones for preventing common failure modes.

5. **Specify output format last** — Once you have good content (high accuracy/relevance scores), tighten the format. Structure is the easiest dimension to fix — content quality requires earlier-stage work.

6. **Keep track of token cost** — The challenge doesn't penalize token count, but in production you'd want the shortest prompt that still hits 8.5. After passing, try trimming your prompt to find the minimum viable version.
