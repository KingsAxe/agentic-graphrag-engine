# ADR-001: Vector Database Selection

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

SovereignRAG V2 requires a vector database to store and retrieve dense embeddings produced during
document ingestion. The system performs hybrid retrieval — combining vector similarity search with
graph traversal — so the vector store must integrate cleanly alongside Neo4j without becoming a
bottleneck.

The plan currently references FAISS as a Phase 1 placeholder, with a note to migrate to a scalable
database later. This deferral is problematic: the ingestion schema, retrieval interface, and
service contracts all depend on which database is chosen. Locking in the decision now avoids a
costly migration mid-build.

---

## Decision Drivers

- Must support metadata filtering alongside vector search (filtering by document ID, workspace,
  date range, source type)
- Must be self-hostable for Phase 1 local deployment
- Must have a managed cloud offering for Phase 2 deployment
- Low operational complexity during development
- Python SDK maturity
- Horizontal scaling support for Phase 3

---

## Options Considered

### Option A: Qdrant

A purpose-built vector database written in Rust. Supports payload filtering, named vectors
(multiple embedding spaces per record), and sparse vectors for hybrid dense/sparse retrieval.

| Factor | Assessment |
|---|---|
| Self-hostable | Yes — Docker image, single binary |
| Managed cloud | Yes — Qdrant Cloud |
| Metadata filtering | Strong — rich payload filter DSL |
| Python SDK | Mature, actively maintained |
| Sparse vector support | Yes — enables BM25 hybrid retrieval natively |
| Performance | High — Rust core, HNSW index |
| Operational complexity | Low — stateless, simple config |
| Horizontal scaling | Yes — distributed mode available |
| Schema migration | Collections are versioned, migration is manageable |

**Risks:** Distributed mode requires Qdrant Cloud or manual cluster setup. Less widely adopted
than Pinecone, so community resources are thinner.

---

### Option B: Weaviate

A full-featured vector database with built-in modules for embedding generation, hybrid BM25+vector
search, and a GraphQL query interface.

| Factor | Assessment |
|---|---|
| Self-hostable | Yes — Docker Compose |
| Managed cloud | Yes — Weaviate Cloud |
| Metadata filtering | Strong — class-based schema with properties |
| Python SDK | Mature |
| Sparse vector support | Yes — via BM25 hybrid search module |
| Performance | Good — Go core |
| Operational complexity | Moderate — schema must be defined upfront, harder to iterate |
| Horizontal scaling | Yes — replication and sharding supported |
| Schema migration | Harder — schema changes require class recreation in older versions |

**Risks:** The upfront schema definition adds friction during early development. The GraphQL
interface adds a learning curve on top of an already complex system.

---

### Option C: ChromaDB

A lightweight, developer-first vector store designed for rapid prototyping. Embeds in-process or
runs as a server.

| Factor | Assessment |
|---|---|
| Self-hostable | Yes — runs in-process or as a server |
| Managed cloud | No — not production-managed |
| Metadata filtering | Basic — where clause filtering |
| Python SDK | Simple and minimal |
| Sparse vector support | No |
| Performance | Acceptable for small datasets, degrades at scale |
| Operational complexity | Very low |
| Horizontal scaling | No — single node only |
| Schema migration | Not applicable — schemaless |

**Risks:** ChromaDB has no managed cloud offering and no horizontal scaling. It is appropriate
for prototyping but would require a full migration at Phase 2. Using it now defers — rather
than eliminates — the vector DB decision.

---

## Comparison Summary

| Criterion | Qdrant | Weaviate | ChromaDB |
|---|---|---|---|
| Production readiness | High | High | Low |
| Self-hosted simplicity | High | Medium | High |
| Managed cloud | Yes | Yes | No |
| Metadata filtering | Strong | Strong | Basic |
| Hybrid retrieval | Yes | Yes | No |
| Horizontal scale | Yes | Yes | No |
| Dev iteration speed | High | Medium | High |
| Schema flexibility | High | Low-Medium | High |

---

## Recommendation

**Qdrant.**

It provides the best balance of development simplicity, production readiness, and operational
flexibility. Its payload filtering DSL is well-suited to the workspace-based multi-tenancy model
planned for V2.3. The named vector support also enables storing multiple embedding spaces per
document (e.g., chunk embedding + title embedding) without running separate collections.

ChromaDB should not be used even for Phase 1 — the migration cost at Phase 2 outweighs the
convenience. Weaviate is a credible alternative but the schema rigidity adds unnecessary friction
during the early build phase.

---

## Decision

**[ ] Qdrant**  
**[ ] Weaviate**  
**[ ] ChromaDB**  

_Mark the selected option and update status to "Accepted" when decided._
