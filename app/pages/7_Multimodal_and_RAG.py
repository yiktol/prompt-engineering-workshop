import streamlit as st
import base64
from utils.bedrock_client import invoke_model, get_bedrock_client
from utils.config_panel import render_config_panel
from utils.styles import apply_custom_styles

st.set_page_config(page_title="Multimodal & RAG", page_icon="🖼️", layout="wide")
apply_custom_styles()

main_col, config_col = st.columns([7, 3])
render_config_panel(config_col)

# Knowledge Base config on the right side
with config_col:
    with st.container(border=True):
        st.markdown("##### 🗄️ Knowledge Base")
        kb_id = st.text_input(
            "Knowledge Base ID:",
            value="",
            placeholder="e.g. ABCDEF1234",
            key="kb_id",
            help="Enter your Bedrock Knowledge Base ID.",
        )
        kb_num_results = st.number_input(
            "Results to retrieve:",
            min_value=1,
            max_value=10,
            value=3,
            key="kb_num_results",
        )
        if not kb_id:
            st.caption("Create one in [Bedrock Console](https://console.aws.amazon.com/bedrock/home#/knowledge-bases)")

with main_col:
    st.title("🖼️ Multimodal & RAG Prompting")
    st.markdown("Extend prompt engineering to images and external knowledge retrieval.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "🖼️ Multimodal Prompting", "📚 RAG Prompting", "🔬 Advanced RAG"
    ])

    # --- Tab 1: Multimodal Prompting ---
    with tab1:
        st.markdown("""
**Multimodal prompting** sends both text and images to the model.
The Bedrock Converse API supports images natively with Claude and Nova models.

Use cases:
- Image description and captioning
- Visual Q&A (charts, diagrams, screenshots)
- Document/receipt extraction
- Multimodal Chain-of-Thought reasoning
""")

        st.markdown("---")
        st.markdown("#### Upload an Image")

        uploaded_file = st.file_uploader(
            "Upload an image (PNG, JPG, GIF, WEBP):",
            type=["png", "jpg", "jpeg", "gif", "webp"],
            key="multimodal_upload",
        )

        image_prompt = st.text_area(
            "Prompt for the image:",
            value="Describe this image in detail. What do you see? If there is text, extract it.",
            height=80,
            key="image_prompt",
        )

        # Preset prompts for different use cases
        preset = st.selectbox(
            "Or choose a preset prompt:",
            [
                "Custom (use text above)",
                "Describe the image",
                "Extract all text/data from this image",
                "Analyze this chart and summarize the key insights",
                "What's wrong in this image? Identify any issues.",
                "Multimodal CoT: Describe what you see, then reason step by step to answer the question.",
            ],
            key="mm_preset",
        )

        if preset != "Custom (use text above)":
            image_prompt = preset

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded image", use_container_width=True)

        if st.button("🔍 Analyze Image", key="run_multimodal", type="primary"):
            if not uploaded_file:
                st.warning("Please upload an image first.")
            else:
                with st.spinner("Analyzing image..."):
                    try:
                        # Read and encode image
                        image_bytes = uploaded_file.getvalue()
                        media_type = uploaded_file.type or "image/png"
                        # Map MIME type to Converse API format
                        format_map = {
                            "image/png": "png",
                            "image/jpeg": "jpeg",
                            "image/gif": "gif",
                            "image/webp": "webp",
                        }
                        img_format = format_map.get(media_type, "png")

                        # Build multimodal message
                        client = get_bedrock_client()
                        model_id = st.session_state.get("selected_model_id", "amazon.nova-lite-v1:0")
                        temperature = st.session_state.get("inference_temperature", 0.7)
                        max_tokens = st.session_state.get("inference_max_tokens", 1024)

                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "image": {
                                            "format": img_format,
                                            "source": {"bytes": image_bytes},
                                        }
                                    },
                                    {"text": image_prompt},
                                ],
                            }
                        ]

                        response = client.converse(
                            modelId=model_id,
                            messages=messages,
                            inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
                        )

                        result = response["output"]["message"]["content"][0]["text"]
                        st.success(result)

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        st.markdown("---")
        st.markdown("#### Multimodal CoT")
        st.markdown("""
**Multimodal Chain-of-Thought** (from [promptingguide.ai](https://www.promptingguide.ai/techniques/multimodalcot))
uses a two-stage approach:

1. **Rationale generation** — Model describes what it sees and reasons about it
2. **Answer inference** — Model uses the rationale to produce a final answer

This improves accuracy on complex visual reasoning tasks like math word problems
with diagrams, scientific figures, or multi-step visual puzzles.

**Prompt pattern:**
```
Look at this image carefully.

Step 1: Describe what you observe in the image.
Step 2: Based on your observations, reason step by step.
Step 3: Provide your final answer.
```
""")

    # --- Tab 2: RAG Prompting ---
    with tab2:
        st.markdown("""
**Retrieval Augmented Generation (RAG)** grounds LLM responses in external knowledge.
Instead of relying solely on training data, the model receives retrieved context
and generates answers based on that evidence.

**RAG Pipeline:** Query → Retrieve → Augment Prompt → Generate
""")

        st.markdown("---")

        # --- Bedrock Knowledge Base Integration ---
        st.markdown("#### 🗄️ Amazon Bedrock Knowledge Base")
        st.markdown("Connect to a real Knowledge Base to retrieve and generate with your own data. Configure the **Knowledge Base ID** in the right panel →")

        kb_id = st.session_state.get("kb_id", "")
        kb_num_results = st.session_state.get("kb_num_results", 3)

        if kb_id:
            kb_query = st.text_area(
                "❓ Query the Knowledge Base:",
                value="What are the main features of this product?",
                height=60,
                key="kb_query",
            )

            kb_mode = st.radio(
                "Mode:",
                ["Retrieve & Generate (end-to-end)", "Retrieve Only (show chunks)"],
                key="kb_mode",
                horizontal=True,
            )

            if st.button("🔍 Query Knowledge Base", key="run_kb", type="primary"):
                region = st.session_state.get("aws_region", "us-east-1")
                model_id = st.session_state.get("selected_model_id", "amazon.nova-lite-v1:0")

                with st.spinner("Querying Knowledge Base..."):
                    try:
                        import boto3
                        bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=region)

                        if kb_mode == "Retrieve Only (show chunks)":
                            # Retrieve only
                            response = bedrock_agent.retrieve(
                                knowledgeBaseId=kb_id,
                                retrievalQuery={"text": kb_query},
                                retrievalConfiguration={
                                    "vectorSearchConfiguration": {
                                        "numberOfResults": kb_num_results,
                                    }
                                },
                            )

                            results = response.get("retrievalResults", [])
                            if not results:
                                st.warning("No results found.")
                            else:
                                st.markdown(f"**📄 Retrieved {len(results)} chunks:**")
                                for i, chunk in enumerate(results):
                                    content = chunk.get("content", {}).get("text", "")
                                    score = chunk.get("score", 0)
                                    source = chunk.get("location", {}).get("s3Location", {}).get("uri", "Unknown")
                                    with st.expander(f"Chunk {i+1} (score: {score:.3f}) — {source}"):
                                        st.write(content)

                                # Offer to use retrieved chunks for RAG prompt
                                st.markdown("---")
                                st.markdown("**Use these chunks with a structured RAG prompt:**")
                                combined_context = "\n\n".join(
                                    [f"[Chunk {i+1}]: {r.get('content', {}).get('text', '')}" for i, r in enumerate(results)]
                                )
                                rag_prompt_with_kb = f"""Answer the question based ONLY on the provided context. If the answer is not in the context, say "I don't have enough information."

Cite your sources using [Chunk N].

Context:
---
{combined_context}
---

Question: {kb_query}

Answer (with citations):"""
                                if st.button("Generate Answer from Chunks", key="run_kb_generate"):
                                    with st.spinner("Generating..."):
                                        answer = invoke_model(rag_prompt_with_kb, temperature=0.3)
                                    st.success(answer)

                        else:
                            # Retrieve and Generate
                            response = bedrock_agent.retrieve_and_generate(
                                input={"text": kb_query},
                                retrieveAndGenerateConfiguration={
                                    "type": "KNOWLEDGE_BASE",
                                    "knowledgeBaseConfiguration": {
                                        "knowledgeBaseId": kb_id,
                                        "modelArn": f"arn:aws:bedrock:{region}::foundation-model/{model_id}",
                                        "retrievalConfiguration": {
                                            "vectorSearchConfiguration": {
                                                "numberOfResults": kb_num_results,
                                            }
                                        },
                                    },
                                },
                            )

                            # Display generated response
                            output = response.get("output", {}).get("text", "No response generated.")
                            st.markdown("**🤖 Generated Answer:**")
                            st.success(output)

                            # Display citations
                            citations = response.get("citations", [])
                            if citations:
                                st.markdown("**📚 Citations:**")
                                for i, citation in enumerate(citations):
                                    refs = citation.get("retrievedReferences", [])
                                    for ref in refs:
                                        content = ref.get("content", {}).get("text", "")[:200]
                                        source = ref.get("location", {}).get("s3Location", {}).get("uri", "Unknown")
                                        st.caption(f"[{i+1}] {source}")
                                        st.text(content + "...")

                    except Exception as e:
                        error_msg = str(e)
                        if "ResourceNotFoundException" in error_msg:
                            st.error("❌ Knowledge Base not found. Check the ID and region.")
                        elif "AccessDeniedException" in error_msg:
                            st.error("❌ Access denied. Ensure your credentials have `bedrock-agent-runtime` permissions.")
                        else:
                            st.error(f"❌ Error: {error_msg}")
        else:
            st.info("💡 Enter a Knowledge Base ID in the right panel to query your own data.")

        st.markdown("---")
        st.markdown("#### 📝 Simulated RAG Demo")
        st.markdown("No Knowledge Base? Compare RAG prompt strategies with simulated documents below.")

        # Simulated retrieved documents
        retrieved_docs = st.text_area(
            "📄 Retrieved Documents (simulated knowledge base):",
            value="""Document 1 (Source: AWS Blog, 2024-11-15):
Amazon Bedrock now supports over 100 foundation models from providers including Anthropic, Meta, Mistral, and Cohere. Pricing varies by model, with Amazon Nova Micro starting at $0.035 per million input tokens.

Document 2 (Source: AWS Documentation, 2024-12-01):
Amazon Bedrock Guardrails allows you to implement safeguards for generative AI applications. It supports content filtering, denied topics, word filters, sensitive information filters (PII), and contextual grounding checks.

Document 3 (Source: AWS re:Invent 2024 Keynote):
AWS CEO Matt Garman announced that enterprise adoption of generative AI on AWS has tripled year-over-year, with financial services and healthcare being the top adopting industries.""",
            height=200,
            key="rag_docs",
        )

        user_question = st.text_area(
            "❓ User Question:",
            value="What safety features does Amazon Bedrock offer and how much does it cost?",
            height=60,
            key="rag_question",
        )

        st.markdown("---")

        rag_col1, rag_col2 = st.columns(2)

        with rag_col1:
            st.markdown("**❌ Naive RAG (context stuffing)**")
            naive_prompt = f"""{retrieved_docs}

Question: {user_question}
Answer:"""
            st.code(naive_prompt[:300] + "...", language=None)

        with rag_col2:
            st.markdown("**✅ Structured RAG (with instructions)**")
            structured_rag_prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context documents. If the answer is not in the context, say "I don't have enough information to answer this."

Rules:
- Cite your sources using [Source: document name]
- Be concise and factual
- Do not make up information beyond what's in the context

Context Documents:
---
{retrieved_docs}
---

User Question: {user_question}

Answer (with citations):"""
            st.code(structured_rag_prompt[:300] + "...", language=None)

        if st.button("Compare RAG Approaches", key="run_rag"):
            rag_col1, rag_col2 = st.columns(2)
            with rag_col1:
                with st.spinner("Naive RAG..."):
                    naive_result = invoke_model(naive_prompt, temperature=0.3)
                st.write(naive_result)
            with rag_col2:
                with st.spinner("Structured RAG..."):
                    structured_result = invoke_model(structured_rag_prompt, temperature=0.3)
                st.write(structured_result)

        st.markdown("---")
        st.markdown("""
#### 💡 RAG Prompt Best Practices

| Practice | Why |
|----------|-----|
| **Instruct to use only provided context** | Reduces hallucination |
| **Require citations** | Makes answers verifiable |
| **Add "say I don't know"** | Prevents fabrication when context is insufficient |
| **Use delimiters for context** | Separates retrieved docs from instructions |
| **Specify output format** | Consistent, parseable responses |
""")

    # --- Tab 3: Advanced RAG ---
    with tab3:
        st.markdown("""
**Advanced RAG** techniques improve retrieval quality and generation accuracy
through prompt engineering at different stages of the pipeline.

Reference: [promptingguide.ai/research/rag](https://www.promptingguide.ai/research/rag)
""")

        st.markdown("---")
        st.markdown("#### 1. Query Rewriting")
        st.markdown("""
The user's original query may be vague or poorly structured for retrieval.
**Query rewriting** uses the LLM to reformulate the query before searching.
""")

        original_query = st.text_area(
            "Original user query:",
            value="How do I make my AI app safe?",
            height=60,
            key="adv_rag_query",
        )

        if st.button("Rewrite Query for Retrieval", key="run_rewrite"):
            rewrite_prompt = f"""You are a search query optimizer. Rewrite the following user question into 3 different search queries that would retrieve the most relevant documents from a technical knowledge base.

Original question: {original_query}

Generate 3 alternative queries that are:
1. More specific and technical
2. Use different terminology/synonyms
3. Break down into sub-questions if needed

Rewritten queries:"""
            with st.spinner("Rewriting..."):
                result = invoke_model(rewrite_prompt, temperature=0.3)
            st.success(result)

        st.markdown("---")
        st.markdown("#### 2. Contextual Compression")
        st.markdown("""
Retrieved documents often contain irrelevant information. **Contextual compression**
extracts only the relevant parts before passing to the generator.
""")

        long_doc = st.text_area(
            "Retrieved document (contains noise):",
            value="""Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models from leading AI companies. The service was launched in September 2023 and has since expanded significantly. Amazon Bedrock supports model customization through fine-tuning and continued pre-training. For safety, Amazon Bedrock Guardrails provides content filtering with configurable thresholds for hate, insults, sexual content, and violence. It also offers denied topic filters, word filters, PII detection and redaction, and contextual grounding checks to reduce hallucination. The service is available in multiple AWS regions including us-east-1, us-west-2, and eu-west-1. Pricing is based on input and output tokens processed.""",
            height=150,
            key="adv_rag_doc",
        )

        compression_question = st.text_area(
            "Question to answer:",
            value="What safety features does Bedrock provide?",
            height=60,
            key="adv_rag_compress_q",
        )

        if st.button("Compress then Answer", key="run_compress"):
            # Step 1: Compress
            compress_prompt = f"""Extract ONLY the sentences from the following document that are relevant to answering this question. Remove all irrelevant information.

Question: {compression_question}

Document:
{long_doc}

Relevant excerpts only:"""

            with st.spinner("Compressing..."):
                compressed = invoke_model(compress_prompt, temperature=0.1)
            st.markdown("**Compressed context:**")
            st.info(compressed)

            # Step 2: Answer with compressed context
            answer_prompt = f"""Answer the question based only on the provided context. Cite specific details.

Context: {compressed}

Question: {compression_question}

Answer:"""
            with st.spinner("Generating answer..."):
                answer = invoke_model(answer_prompt, temperature=0.3)
            st.markdown("**Answer:**")
            st.success(answer)

        st.markdown("---")
        st.markdown("#### 3. Self-RAG (Critique & Refine)")
        st.markdown("""
**Self-RAG** adds a self-reflection step where the model evaluates whether its
answer is actually supported by the retrieved context.
""")

        self_rag_context = st.text_area(
            "Context:",
            value="Amazon Nova Micro is the most affordable model on Bedrock at $0.035 per million input tokens. It supports text-only workloads with a 128K context window.",
            height=80,
            key="self_rag_ctx",
        )

        self_rag_question = st.text_area(
            "Question:",
            value="What is the context window size and pricing for Amazon Nova Micro?",
            height=60,
            key="self_rag_q",
        )

        if st.button("Run Self-RAG", key="run_self_rag"):
            # Step 1: Generate
            gen_prompt = f"""Answer based on the context provided.

Context: {self_rag_context}

Question: {self_rag_question}

Answer:"""
            with st.spinner("Generating..."):
                initial_answer = invoke_model(gen_prompt, temperature=0.3)
            st.markdown("**Initial answer:**")
            st.info(initial_answer)

            # Step 2: Critique
            critique_prompt = f"""You are a fact-checker. Evaluate whether the following answer is fully supported by the given context. 

Context: {self_rag_context}

Question: {self_rag_question}

Answer: {initial_answer}

Evaluation:
1. Is every claim in the answer supported by the context? (Yes/No for each claim)
2. Are there any hallucinated facts not in the context?
3. Is anything from the context missing in the answer?
4. Confidence score (1-5):

If issues found, provide a corrected answer."""
            with st.spinner("Self-critiquing..."):
                critique = invoke_model(critique_prompt, temperature=0.1)
            st.markdown("**Self-critique:**")
            st.success(critique)

        st.markdown("---")
        st.markdown("""
#### RAG Paradigms (from promptingguide.ai)

| Paradigm | Description |
|----------|-------------|
| **Naive RAG** | Simple retrieve → read → generate pipeline |
| **Advanced RAG** | Adds pre-retrieval (query rewriting) and post-retrieval (compression, reranking) |
| **Modular RAG** | Composable modules: routing, query transformation, retrieval, reranking, generation |
| **Self-RAG** | Model critiques its own output for faithfulness to retrieved context |
""")
