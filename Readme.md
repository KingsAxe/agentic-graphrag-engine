## **Sovereign Research Engine**

The Decoupled Sovereignty Pattern for High-Fidelity Knowledge Synthesis

### **Introduction**

The Sovereign Research Engine is a local-first, privacy-preserving Retrieval-Augmented Generation (RAG) system designed for high-stakes research environments. Unlike traditional “chatbots” that prioritize conversational fluidity, this engine prioritizes epistemic integrity, data sovereignty, and auditability.

It operates on the Decoupled Sovereignty Pattern, an architectural approach that separates the reasoning logic (Python/LLM) from the persistent memory (PostgreSQL) and the user interface (Streamlit). This ensures that the researcher retains ownership of their data, models, and crystallized knowledge, independent of cloud providers or API availability.

### **Problem Statement**

Modern RAG demos often fail in real research settings due to:

- Contextual amnesia: knowledge is trapped in ephemeral chat logs.

- Hallucination opacity: answers appear confident without evidence-based audit.

- Fragile retrieval: semantic-only search misses acronyms, codes, and exact technical terms.

- Data leakage risk: cloud-first workflows compromise privacy and IP.

### **What This Solves**

Sovereign Research Engine upgrades RAG into a true research workbench:

**Epistemic Transparency**
Every answer includes a structured Belief Report (self-audit) and citations.

**Crystallization (Lab Notebook)**
Verified answers become permanent knowledge artifacts in PostgreSQL and are reused in future queries (recursive grounding).

**Hybrid Retrieval**
Dense vector search plus BM25 keyword retrieval plus optional multi-query expansion for higher recall on technical material.

**Local Vault and Document Library**
Ingested documents are persisted in a stable location and indexed in PostgreSQL. A Library view shows what is stored (including previews), even if the raw PDFs are later moved or deleted.

### **System Architecture**

The system is split into three sovereign layers:

1) The Engine (Python and FastAPI)
Role: Stateless reasoning and orchestration

### **Components:**

**Orchestration:** LangChain (LCEL) for deterministic pipelines

**Inference:** llama-cpp-python for local GGUF models (Qwen, Llama, etc.)

**API:** FastAPI exposed only on local loopback (127.0.0.1)

Core endpoints (local-only):

POST /ingest — upload and index a PDF

POST /query — run a research query (returns Belief Report plus citations)

POST /verify — crystallize an answer

GET /notebook/{session_id} — retrieve lab notebook entries

GET /models — available GGUF models

GET /library — document library (previews plus availability status)

2) The Vault (PostgreSQL and pgvector)
Role: Persistent memory and source of truth

#### **Stores:**

Vector embeddings (BGE-Small, 384 dims)

Chunk metadata (source, page numbers, identifiers)

Research notebook entries (research_entries)

Chat history (optional)

3) The UI Layer (Streamlit Workbench)
Role: Rapid research interface in the browser (local-only)

Calls FastAPI endpoints directly

Provides Workbench, Ingest, Notebook, Settings, and Library pages

**Key Capabilities**

Epistemic Audit Layer
The engine outputs structured objects, not raw strings. Each response contains:

Answer

Belief Report

epistemic score (0.0–1.0)

evidence quality

hallucination risk

reasoning trace (audit narrative)

Citations with source and page references

Hybrid Retrieval Modes

Precision Mode: Vector and BM25 weighted ensemble (best for exact technical retrieval)

Exploratory Mode: Multi-query expansion for broader conceptual coverage

Recursive Grounding
Verified knowledge is saved into research_entries and prioritized in future responses. This creates a knowledge feedback loop without model fine-tuning.

Persistent Local Document Library

PDFs are saved to a stable user data directory (per OS) during ingestion.

The Vault stores enough context (metadata plus previews) to display a library even if raw files are deleted.

Repository Structure
sovereign-research-engine/
├── app/                        # Python Engine (FastAPI + RAG)
│   ├── core/                   # Ingest, model management, rag chain
│   ├── database/               # PGVector + schema + notebook CRUD
│   └── api.py                  # FastAPI endpoints
├── ui/                         # Streamlit Workbench UI (calls FastAPI)
│   ├── streamlit_app.py
│   ├── ui_utils.py
│   └── pages/
├── data/                       # Raw evidence (dev only; desktop uses user dir)
├── models/                     # GGUF + embedding models
├── scripts/                    # DB reset, utilities
├── .env
├── requirements.txt
└── README.md

**Installation and Setup**

Prerequisites

Python 3.10+

PostgreSQL 15+ with pgvector

GGUF model(s) in models/llms/

Embedding model path set in .env

Configure Environment
Create .env in repo root:

DATABASE_URL=postgresql://user:pass@localhost:5432/yourdb
EMBEDDING_MODEL_PATH=./models/embeddings/...
LLM_MODELS_DIR=./models/llms
MODEL_PATH=./models/llms/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
POSTGRES_VECTOR_DIM=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=100


Initialize Database
Run the schema:

psql -d yourdb -f app/database/schema.sql

Run (Development)

Start FastAPI Engine

uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload


Start Streamlit Workbench UI

streamlit run ui/streamlit_app.py

**Usage Workflow**

Ingestion
Upload PDF research papers via the Ingest page. The system performs hashing to prevent duplicate indexing.

Querying
Select a mode (Precision vs Exploratory) and submit your query via the Workbench.

Review
Examine the Belief Report attached to the answer and check citations.

Crystallization
If the answer is accurate, verify it. This commits the finding to the Lab Notebook, reinforcing the system’s future performance.

Library
Browse the Library to see what has been indexed, including previews and whether the original PDF is still present on disk.

**Contribution**

This project adheres to strict architectural standards to maintain sovereignty and modularity.

Stateless Logic
Ensure all new chains in rag_chain.py remain stateless.

Type Safety
All API exchanges must be defined via Pydantic models.

Database First
All state must persist in PostgreSQL; no in-memory session storage for research artifacts.

**License**

Distributed under the Apache License. See LICENSE for more information.