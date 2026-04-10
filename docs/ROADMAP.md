# SovereignRAG V2 Roadmap to Production

This document outlines the weekly cadence for building, testing, and deploying SovereignRAG V2 into a production-ready system. 

## Phase 1: Core Foundation (Weeks 1-3)

### Week 1: Infrastructure and API Shell
**Goal:** Establish the local development environment and core service shells.
*   Initialize Docker Compose with Neo4j, Qdrant, PostgreSQL, and Redis.
*   Setup the FastAPI Gateway with basic routing and API Key authentication middleware.
*   Implement the database connection managers for all storage layers.
*   Define the fundamental data models (SQLalchemy schemas, Pydantic models).

### Week 2: Ingestion and Task Processing
**Goal:** Build the asynchronous document processing pipeline.
*   Implement the Celery worker structure and task queues (`ingestion_queue`, `embedding_queue`).
*   Build document parsers (text, basic PDF).
*   Integrate the BGE-M3 embedding model.
*   Write pipeline logic: Upload document -> create task -> parse -> chunk -> embed -> store in Qdrant.

### Week 3: Graph Construction
**Goal:** Enable entity extraction and graph storage.
*   Define Neo4j node and relationship schemas.
*   Implement LLM prompts for extracting entities, relationships, and claims from chunks (Llama 3 via Groq).
*   Create Graph Service methods to write extracted data to Neo4j.
*   Update Celery pipeline to store graph data alongside vector embeddings.

## Phase 2: Intelligence Layer (Weeks 4-5)

### Week 4: Agent Orchestration and Hybrid Retrieval (COMPLETED)
**Goal:** Enable reasoning over the ingested data using Llama 3 (via Groq).
*   Implement the Retrieval Service (routing queries to Qdrant, querying Neo4j).
*   Setup LangGraph scaffolding for the Agent Service.
*   Implement basic agent tools: `search_vector`, `query_graph`, `expand_entity`.
*   Connect the Agent Service to the API Gateway for user queries.

### Week 5: The Validation Engine
**Goal:** Implement confidence scoring and contradiction detection.
*   Implement similarity thresholding for claim comparison.
*   Build the LLM-as-judge prompt for detecting contradictions in highly similar claims.
*   Define confidence scoring logic based on source recency and agreement.
*   Ensure agent reasoning traces include validation metadata.

## Phase 3: Product Layer (Weeks 6-7)

### Week 6: Workspaces and Frontend Initialization
**Goal:** Prepare the system for multi-tenant interaction.
*   Refactor API Key auth to respect Workspace boundaries in database queries.
*   Initialize the Next.js frontend project.
*   Build the core chat interface connecting to the API Gateway.
*   Implement reasoning trace streaming to the UI.

### Week 7: Workspace Reliability, Retrieval Quality, and Evaluation
**Goal:** Stabilize the product loop before adding the flagship graph experience.
*   Add stronger retrieval scoping so queries can be limited to selected documents or recent ingestion targets.
*   Improve workspace safety by tightening auth-bound workspace access across document, query, and reset flows.
*   Add better job lifecycle visibility in the frontend, including retry/failure states and clearer progress feedback.
*   Introduce regression verification for ingestion, scoped retrieval, and trace output so weekly progress is measurable.

## Phase 4: Scale and Deployment (Week 8)

### Week 8: Production Readiness
**Goal:** Transition from local deployment to a scalable cloud architecture.
*   Audit code for idempotency and error handling.
*   Set up managed cloud databases (Cloud SQL, Managed Qdrant, AuraDB).
*   Deploy backend services via Kubernetes or managed container services.
*   Implement CI/CD pipelines for automated testing and deployment.
