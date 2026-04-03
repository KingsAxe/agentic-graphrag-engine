# Week 4 Log: Agent Orchestration and Hybrid Retrieval

**Date:** 2026-04-02
**Commit:** `feat: Week 4 - LangGraph agent and hybrid retrieval service`

**Completed Actions:**
* **Dependencies:** Added `langgraph`, `langchain`, and `langchain-openai` to `requirements.txt`.
* **Hybrid Retrieval:** Enhanced `QdrantService` and `Neo4jService` with search and traversal methods, enforcing strict `workspace_id` isolation.
* **Agent Scaffolding:** Implemented a LangGraph orchestrator in `orchestrator.py` using a ReAct-style loop (Agent -> Tool -> Agent).
* **Agent Tools:** Developed custom tools for the agent to query both the vector database (semantic search) and the knowledge graph (entity expansion).
* **API Integration:** Exposed the agent reasoning via a new `POST /api/v1/query` endpoint.
* **Architecture:** Grounded agent responses by providing workspace context directly to tools.
* **Stability Fixes:** 
    * Fixed a broken `langgraph` installation that caused `ToolNode` import errors.
    * Refactored `orchestrator.py` to use lazy initialization for the LangGraph application, preventing module-level crashes when `GROQ_API_KEY` is missing.
    * Created `example.env` to simplify environment setup for new deployments.
