# ADR-003: Claim Validation Approach

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

The Validation Engine is one of SovereignRAG V2's core differentiators. The system promises
"verifiable, explainable outputs" — which means that when a claim is extracted from a document
or synthesized by the LLM, the system must be able to:

1. Assess its confidence level with a numeric score
2. Detect whether it contradicts claims from other sources already stored in the graph
3. Provide a traceable justification for both the score and the contradiction flag

This is architecturally non-trivial. The approach chosen determines how the Validation Engine
is implemented, how it integrates with the Graph Service, and how confidence scores are displayed
in the UI.

---

## Decision Drivers

- Contradiction detection must be explainable — a flag is not sufficient without a reason
- Confidence scores must be deterministic and reproducible for the same inputs
- The system must handle partial contradictions (claim A and claim B overlap but neither
  fully refutes the other)
- The approach must not require ground truth labels — the system operates on unlabeled documents
- The approach must be operable locally (Phase 1) without large GPU infrastructure

---

## Options Considered

### Option A: LLM-as-Judge

A dedicated LLM prompt receives a candidate claim and a set of related claims retrieved from
the graph. The LLM is instructed to:

- Assign a confidence score (0.0 to 1.0)
- Identify any contradictions with the provided claims
- Produce a short natural language justification

**Prompt structure:**
```
Given the following claim:
  [CANDIDATE CLAIM]

And the following related claims from the knowledge base:
  [CLAIM 1] (source: doc_id, date)
  [CLAIM 2] (source: doc_id, date)

Task:
  1. Score confidence in the candidate claim: 0.0 (unsupported) to 1.0 (strongly supported)
  2. Identify any direct contradictions with the related claims
  3. Provide a one-paragraph justification
```

| Factor | Assessment |
|---|---|
| Explanation quality | High — natural language justification |
| Contradiction detection | Good — handles nuanced/partial contradictions |
| Reproducibility | Low — LLM outputs are non-deterministic |
| Local operability | Depends on model size — small models (7B) give poor results |
| Cost | High if using external API at scale |
| Implementation complexity | Low — primarily prompt engineering |
| Ground truth required | No |

**Risks:** Non-determinism means the same claim can receive different scores on re-evaluation.
Small local models perform poorly at nuanced contradiction reasoning. At scale, LLM-as-judge
becomes expensive.

---

### Option B: Embedding Similarity with Threshold Rules

Candidate claims are embedded and compared against stored claims using cosine similarity. Scores
are computed from similarity thresholds. Contradictions are detected by pairing high-similarity
claim embeddings with semantic negation patterns.

**Scoring model:**
```
confidence = weighted_average(
    source_recency_score,         # newer sources weighted higher
    source_agreement_score,       # ratio of supporting vs. contradicting claims
    embedding_similarity_score    # similarity to high-confidence stored claims
)
```

**Contradiction detection:**
- Retrieve top-K semantically similar claims
- Apply a negation classifier or compare polarity embeddings
- Flag pairs with similarity > 0.85 but opposite sentiment/polarity

| Factor | Assessment |
|---|---|
| Explanation quality | Low — numeric scores without natural language rationale |
| Contradiction detection | Moderate — negation patterns miss subtle contradictions |
| Reproducibility | High — fully deterministic |
| Local operability | High — runs on sentence-transformers with no GPU |
| Cost | Low — no LLM calls |
| Implementation complexity | Medium — scoring formula and threshold tuning required |
| Ground truth required | No |

**Risks:** Semantic similarity does not reliably detect contradictions. Two claims can be highly
similar in embedding space while contradicting each other (e.g., "X causes Y" vs "X does not
cause Y"). Negation classifiers add complexity and are domain-sensitive.

---

### Option C: Hybrid — Embedding Pre-filter + LLM Verdict

Use embedding similarity as a fast pre-filter to retrieve the most relevant claims from the
graph, then call the LLM only for claims that exceed a similarity threshold. This bounds the
LLM call volume while preserving explanation quality for the cases that matter.

**Pipeline:**
```
1. Embed candidate claim
2. Retrieve top-K similar claims from vector store (cosine similarity)
3. If max_similarity < LOW_THRESHOLD:
      confidence = low (no related claims found), no contradiction check
4. If LOW_THRESHOLD <= max_similarity < HIGH_THRESHOLD:
      confidence = heuristic score (embedding-based), no LLM call
5. If max_similarity >= HIGH_THRESHOLD:
      call LLM-as-judge on top-K claims
      confidence = LLM_score
      contradiction = LLM_verdict
```

**Confidence score formula:**
```
confidence = (
    0.4 * source_agreement_ratio    +
    0.3 * source_recency_weight     +
    0.3 * llm_score (if invoked)
)
```

| Factor | Assessment |
|---|---|
| Explanation quality | High for high-relevance cases |
| Contradiction detection | High — LLM invoked where it matters |
| Reproducibility | Medium — deterministic for low-similarity cases, non-deterministic for LLM path |
| Local operability | High — LLM only called selectively |
| Cost | Controlled — LLM calls bounded by threshold |
| Implementation complexity | High — two-stage pipeline with threshold tuning |
| Ground truth required | No |

**Risks:** Threshold calibration requires empirical tuning. The hybrid boundary means confidence
scores are not computed by a single consistent method across all claims, which may be confusing
to present in the UI. Requires careful logging to show which path each claim took.

---

## Comparison Summary

| Criterion | LLM-as-Judge | Embedding + Rules | Hybrid |
|---|---|---|---|
| Explanation quality | High | Low | High |
| Contradiction accuracy | High | Moderate | High |
| Reproducibility | Low | High | Medium |
| Local operability | Low-Medium | High | High |
| Inference cost | High | Negligible | Controlled |
| Implementation complexity | Low | Medium | High |
| Production suitability | Medium | Medium | High |

---

## Recommendation

**Option C: Hybrid.**

The embedding pre-filter keeps inference cost bounded and makes the system operable locally
without a GPU. The LLM verdict provides the explainability that is central to the product
positioning. The threshold design also gives a natural path to improve the system: as the
LLM is fine-tuned in V2.2, the threshold can be lowered to invoke it more frequently as
cost decreases.

The key implementation requirement is that every validation result must be logged with its
pipeline path (embedding-only vs. LLM-invoked), so the UI can display an appropriate
confidence indicator and the reasoning trace is fully auditable.

---

## Decision

**[ ] LLM-as-Judge**  
**[ ] Embedding Similarity with Threshold Rules**  
**[ ] Hybrid (Embedding Pre-filter + LLM Verdict)**  

_Mark the selected option and update status to "Accepted" when decided._
