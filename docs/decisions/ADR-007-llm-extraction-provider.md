# ADR 007: LLM Provider for Graph Extraction

## Status
Accepted

## Context
During **Week 3 (Graph Construction)**, we need to extract structured data (Entities, Relationships, Claims) from chunked text to construct our Neo4j Knowledge Graph. The system requires an LLM capable of robustly outputting complex JSON structures matching our Python Pydantic schemas. 

We must decide whether to use a managed API provider (e.g., OpenAI `gpt-4o-mini`) or a direct provider (e.g., running open-source models like LLaMA 3 or Mistral directly on local hardware via vLLM/Ollama).

## Options Evaluated

### Option 1: Managed API Provider (OpenAI `gpt-4o-mini`)
Utilizing a cloud-hosted frontier model through a REST API.
*   **Pros:**
    *   **Guaranteed Structured Output:** The newest APIs support strict JSON parsing natively, meaning zero formatting errors when generating Neo4j Cypher schemas.
    *   **Zero Infrastructure Overhead:** No GPUs to provision, no model weights to load, perfect for rapid development and testing.
    *   **Speed:** Highly optimized latency across thousands of concurrent Celery requests.
*   **Cons:**
    *   **Data Privacy Constraints:** Data is sent off-site, which blocks highly sensitive or air-gapped enterprise usage.
    *   **Vendor Lock-In:** Reliance on OpenAI's internal ecosystem and uptime.
*   **Scalability:** Extremely high. We can fan-out massively within our Celery workers without hitting hardware bottlenecks on our side.
*   **Cost:** Variable (`gpt-4o-mini` is ~$0.15 per 1M input tokens). Exceptionally economical during Phase 1 development, but becomes expensive at massive production scale (millions of ingested documents).

### Option 2: Direct / Local Provider (Open-Weight Models via vLLM/Ollama)
Running models like `Llama-3-8B-Instruct` directly on our own hardware or dedicated cloud instances.
*   **Pros:**
    *   **Absolute Privacy:** Data never leaves the system's metal infrastructure. Sovereign control over the pipeline.
    *   **Fixed Costs:** You pay for the hardware instances, not the token usage per document. Infinite generations for a flat daily rate.
*   **Cons:**
    *   **Structured Output Volatility:** Smaller local models often struggle to output strict, deeply nested JSON perfectly. They require custom fallback parsers, retry loops, or constrained grammars (which slow down generation speed significantly).
    *   **DevOps Complexity:** Managing GPU VRAM, token batching, and load balancing for local LLMs is incredibly complex compared to simply hitting an endpoint.
*   **Scalability:** Hardware-bound. If we spike to 1,000 concurrent Celery extraction tasks, a single local GPU will buckle without a horizontally scaled cluster, causing massive message broker queues.
*   **Cost:** High upfront or monthly operational cost. Renting a cloud machine with an Nvidia A10G or better forces a minimum hourly cost, which only becomes cost-effective if token volume consistently exceeds the server cost.

## Decision
We will use **Option 1 (OpenAI Managed API)** for **Phase 1 (Development & Architecture Validation)**. 

## Rationale
In the current phase of SovereignRAG V2, our priority is building bulletproof orchestration logic (LangGraph) and structural database schemas (Neo4j). We need a reasoning engine that never fails to format JSON correctly, allowing us to debug our graph traversal logic rather than fighting the LLM's parsing errors.

`gpt-4o-mini` is cheap enough that cost is negligible during this build, and it scales infinitely without us having to manage complex GPU infrastructure. 

For **Phase 2 (Production/Enterprise Migration)**, as defined in our original roadmap, we will aggressively test and migrate to a direct provider (local open-weight model) once the system logic is perfect, utilizing an integration layer that allows us to seamlessly swap out the OpenAI client for a local endpoint.
