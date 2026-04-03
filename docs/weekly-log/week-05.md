# Week 5 Log: The Validation Engine

**Date:** 2026-04-03
**Commit:** `feat: Week 5 - LLM-as-judge validation and confidence scoring`

**Completed Actions:**
* **Validation Engine:** Created `src/services/validation/engine.py` using Llama 3 (via Groq) as a judge to compare claims.
* **Similarity & Contradiction:** Implemented logic to detect contradictory vs. complementary claims using structured LLM output.
* **Confidence Scoring:** Defined a scoring formula: `(Agreement Weight * 0.4) + (LLM Score * 0.6) - Contradiction Penalty`.
* **Graph Metadata:** Enhanced `Neo4jService` to track and return claim support counts and document IDs.
* **Agent Integration:** Updated `expand_entity_tool` to automatically provide validation metadata when querying entities.
* **Verification:** Created `tests/verify_week_05.py` to demonstrate the engine's capability to detect factual mismatches in mock data.
