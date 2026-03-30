# ADR-005: Embedding Model Selection

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

Every document chunk ingested by SovereignRAG V2 is converted into a dense vector embedding.
These embeddings drive the vector similarity search leg of the hybrid retrieval system. The
choice of embedding model affects:

- The quality of retrieval (recall and precision)
- The dimensionality of stored vectors (storage and memory cost)
- The inference latency during ingestion and query
- The cost model (local vs. API)
- The consistency requirement: **all embeddings in the store must use the same model**. Changing
  the embedding model requires re-embedding the entire knowledge graph — a costly operation
  on a populated database.

This decision must be made before any ingestion code is written.

---

## Decision Drivers

- Must be operable locally in Phase 1 without recurring API cost
- Must produce embeddings of sufficient quality for domain-specific document analysis
- Must support batched encoding for efficient ingestion
- Embedding dimensionality should be manageable for local deployment
- Must have a stable, versioned release available to pin
- Should not lock the system into a provider that becomes unavailable

---

## Options Considered

### Option A: OpenAI text-embedding-3-small / text-embedding-3-large

OpenAI's hosted embedding API. Matryoshka-compatible, meaning embeddings can be truncated
to lower dimensions without significant quality loss.

| Factor | Assessment |
|---|---|
| Quality | High — consistently strong on MTEB benchmarks |
| Dimensionality | 1536 (small), 3072 (large) — can be truncated to 256/512 |
| Local operability | No — requires internet and API key |
| Latency (ingestion) | Network-bound — adds latency per batch |
| Cost | $0.02 / 1M tokens (small), $0.13 / 1M tokens (large) |
| Model versioning | Stable — pinnable by model name |
| Re-embedding risk | High — if OpenAI deprecates or changes the model, full re-embed required |
| Batch support | Yes — up to 2048 inputs per request |

**Risks:** Requires internet connectivity. API cost accumulates with volume. Any OpenAI-side
model deprecation forces a full re-indexing of the knowledge graph. Violates the "local-first"
positioning of the system.

---

### Option B: BGE-M3 (BAAI General Embedding, Multi-functionality)

A state-of-the-art open-weight embedding model from BAAI. Supports dense, sparse (lexical),
and ColBERT (multi-vector) retrieval from a single model. The most capable open embedding
model available as of 2026.

| Factor | Assessment |
|---|---|
| Quality | Very high — top MTEB scores for open models |
| Dimensionality | 1024 (dense), sparse vectors vary |
| Local operability | Yes — runs on CPU or GPU |
| Latency (CPU ingestion) | ~50-200ms per batch of 32 chunks (CPU); ~5-20ms (GPU) |
| Cost | Zero — weights are freely downloadable |
| Model versioning | Stable — pinned by Hugging Face revision hash |
| Re-embedding risk | Low — model is self-hosted |
| Batch support | Yes |
| Multi-vector support | Yes — enables ColBERT-style retrieval |

**Risks:** CPU inference is slower than API calls for large ingestion jobs. Requires
~1.5GB GPU VRAM or ~2GB RAM for CPU inference. Initial model download required.

---

### Option C: sentence-transformers/all-MiniLM-L6-v2

A lightweight, widely-used sentence transformer model. Fast CPU inference, small memory
footprint. The de facto default for local RAG prototypes.

| Factor | Assessment |
|---|---|
| Quality | Moderate — adequate for general tasks, weak on domain-specific content |
| Dimensionality | 384 — very compact |
| Local operability | Yes — runs efficiently on CPU |
| Latency (CPU ingestion) | ~5-20ms per batch of 32 chunks (CPU) |
| Cost | Zero |
| Model versioning | Stable |
| Re-embedding risk | Low |
| Batch support | Yes |
| Multi-vector support | No |

**Risks:** 384 dimensions is low for complex document analysis. Retrieval quality
degrades on domain-specific or technical content. This model is appropriate for demos
and prototypes, not for a production portfolio system claiming high retrieval quality.

---

### Option D: Cohere Embed v3

Cohere's hosted embedding API. Strong multilingual support, input-type-aware
(search_query vs. search_document distinction improves retrieval quality).

| Factor | Assessment |
|---|---|
| Quality | High — competitive with OpenAI on most benchmarks |
| Dimensionality | 1024 |
| Local operability | No — API-only |
| Latency (ingestion) | Network-bound |
| Cost | $0.10 / 1M tokens |
| Model versioning | Stable |
| Re-embedding risk | High — API dependency |
| Input-type distinction | Yes — separate embeddings for queries vs. documents |

**Risks:** Same API dependency risks as OpenAI. Slightly lower cost, but still recurring
and internet-dependent.

---

## Comparison Summary

| Criterion | OpenAI | BGE-M3 | all-MiniLM-L6-v2 | Cohere |
|---|---|---|---|---|
| Quality | High | Very High | Moderate | High |
| Local operability | No | Yes | Yes | No |
| Recurring cost | Yes | No | No | Yes |
| Dimensionality | 1536/3072 | 1024 | 384 | 1024 |
| CPU feasibility | N/A | Yes (slower) | Yes (fast) | N/A |
| Sparse vector support | No | Yes | No | No |
| Provider lock-in risk | High | None | None | High |

---

## Recommendation

**BGE-M3 for production quality; all-MiniLM-L6-v2 as a development fallback.**

BGE-M3 is the correct choice for a system that claims high-quality retrieval as a core
feature. Its native sparse vector support also aligns with the hybrid retrieval architecture —
dense and sparse embeddings from a single model simplifies the ingestion pipeline.

For local development where speed matters more than retrieval quality, all-MiniLM-L6-v2
can be used as a configurable fallback. The embedding model must be specified in the service
configuration and stored alongside each embedding record in the vector database, so that
model provenance is always known.

The `EmbeddingService` interface must be model-agnostic. The concrete implementation is
injected via configuration, making a future model swap a configuration change rather than
a code change — at the cost of a full re-embedding run.

---

## Decision

**[ ] OpenAI text-embedding-3-small**  
**[ ] OpenAI text-embedding-3-large**  
**[ ] BGE-M3 (recommended)**  
**[ ] all-MiniLM-L6-v2 (development only)**  
**[ ] Cohere Embed v3**  

_Mark the selected option and update status to "Accepted" when decided._
