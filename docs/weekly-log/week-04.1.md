# Week 4.1 Log: Strategic Pivot to Open Source LLMs

**Date:** 2026-04-02
**Subject:** Transition from OpenAI to Llama 3 (via Groq)

**Overview:**
To ensure long-term sustainability, cost-efficiency, and alignment with the "local-first" vision of SovereignRAG, we have pivoted our Intelligence Layer from proprietary OpenAI models to Open Source alternatives.

**Key Changes:**
* **Model Selection:** Adopted **Llama 3 (70B)** as the primary engine for both structured data extraction and agentic reasoning.
* **Provider Integration:** Integrated **Groq** as the API provider to maintain high-speed inference while using open-weights models.
* **Infrastructure Updates:**
    * Updated `src/core/config.py` to support `GROQ_API_KEY` and configurable model selection.
    * Refactored `src/services/graph/extractor.py` to use LangChain's structured output wrappers compatible with Llama 3.
    * Re-architected the LangGraph orchestrator in `src/services/agent/orchestrator.py` to run on `ChatGroq`.
* **Rationale:** This move removes the dependency on paid, closed-source models and prepares the codebase for future self-hosting or custom fine-tuning on proprietary datasets.
