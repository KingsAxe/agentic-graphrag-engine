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

## Success Criteria

*   Handles multi-document analysis accurately.
*   Produces explainable reasoning outputs with confidence scores.
*   Maintains a persistent, evolving knowledge graph.
*   Scales horizontally via distributed queuing.
*   Demonstrates production-grade architectural patterns.
