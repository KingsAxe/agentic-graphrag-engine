# SovereignRAG V2 - Production System

## Vision

A graph-native AI analysis copilot that constructs, reasons over, and evolves a persistent knowledge graph with verifiable, explainable outputs. This system is a GraphRAG and Agent-based analysis platform featuring persistent memory, structured reasoning, and validation.

## Architecture

The system is decomposed into coordinated, scalable services:

1.  **API Gateway**: FastAPI service handling authentication, routing, and rate-limiting.
2.  **Ingestion Service**: Parses documents (PDF, text, URLs) and dispatches background processing jobs.
3.  **Graph Service**: Manages the Neo4j knowledge graph for persistent entity and relationship storage.
4.  **Retrieval Service**: Hybrid search combining dense vector retrieval (Qdrant) and graph traversal (Neo4j).
5.  **Agent Service**: Orchestrates reasoning workflows using LangGraph and custom tool-calling.
6.  **LLM Service**: Abstracts model execution (initially API-based, migrating to fine-tuned local models).
7.  **Validation Engine**: Detects contradictions across sources, computes confidence scores, and verifies claims.
8.  **Task Queue System**: Celery workers backed by Redis for asynchronous ingestion and analysis.
9.  **Frontend**: Next.js application with interactive graph visualization (Cytoscape.js) and insight panels.

## Technology Stack

Based on system architecture decisions (ADRs):

*   **Vector Database**: Qdrant
*   **Graph Database**: Neo4j
*   **Relational Database**: PostgreSQL
*   **Task Queue**: Celery + Redis
*   **Agent Orchestration**: LangGraph
*   **Embedding Model**: BGE-M3
*   **Validation Approach**: Hybrid (Embedding Pre-filter + Selective LLM Verdict)
*   **Auth Mechanism**: API Key (V2.1) migrating to JWT (V2.3)
*   **Visualization**: Cytoscape.js

## Documentation

*   [Decisions & ADRs](./docs/decisions/)
*   [Weekly Roadmap](./docs/ROADMAP.md)
*   [Local Development Runbook](./docs/local-dev.md)
*   [Launch Commands](./docs/launch-commands.md)

## Launch Readiness

Copy `example.env` to `.env` before testing query or graph-extraction features. Local development now defaults to `LLM_PROVIDER=mock`, which avoids model downloads and keeps the ingestion, graph, worker, and query pipeline usable while you build. If you later want Ollama or Groq again, switch `LLM_PROVIDER` and set the matching config values.

Use `LOG_LEVEL=INFO` for normal startup and `LOG_LEVEL=DEBUG` when tracing launch issues.

For local constrained-network testing:

*   Keep `LLM_PROVIDER=mock` in `.env`.
*   The project will use mock embeddings, mock graph extraction, mock validation, and a mock query agent.
*   This mode is for wiring and iteration, not model-quality evaluation.

The API emits a startup readiness log and the root `GET /` endpoint returns a non-secret readiness summary showing whether the configured LLM provider and the core service endpoints are set.

## Frontend

A full Next.js frontend now lives in [frontend](./frontend). It includes:

* workspace-scoped upload and reset actions
* recent document and job tracking
* streamed reasoning traces from the query API
* a persistent query console for iterative testing

## Success Criteria

*   Handles multi-document analysis accurately.
*   Produces explainable reasoning outputs with confidence scores.
*   Maintains a persistent, evolving knowledge graph.
*   Scales horizontally via distributed queuing.
*   Demonstrates production-grade architectural patterns.
