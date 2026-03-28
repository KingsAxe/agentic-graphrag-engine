# Sovereign Research Engine

Local-first RAG for serious research.

Sovereign Research Engine is a privacy-preserving research workbench built for high-stakes knowledge synthesis. Instead of optimizing for generic chatbot behavior, it focuses on grounded retrieval, explicit reasoning audits, persistent knowledge capture, and full control over data, models, and storage.

The project follows a decoupled architecture:

- FastAPI handles orchestration and query endpoints.
- PostgreSQL with pgvector stores embeddings, citations, notebook entries, and chat state.
- Streamlit provides the research workbench UI.
- Local GGUF models and embedding models keep inference under operator control.

## Why it exists

Most RAG demos break down in real research workflows:

- Answers disappear into chat logs instead of becoming reusable knowledge.
- Retrieval misses exact technical terms, codes, and acronyms.
- Model confidence is implied, not inspected.
- Cloud-first tooling introduces privacy and IP risk.

Sovereign Research Engine is designed to fix those issues with an auditable, database-backed workflow.

## Core capabilities

### Epistemic audit

Each response is returned as a structured research object, not a raw string. The engine produces:

- A grounded answer
- A belief report
- An epistemic score
- Evidence quality notes
- Hallucination risk notes
- Citations tied to source material

### Crystallized knowledge

Verified answers are stored in PostgreSQL as durable research artifacts. Future queries can prioritize this verified knowledge over raw document chunks, creating a recursive knowledge loop without fine-tuning.

### Hybrid retrieval

The engine supports two retrieval modes:

- `precision`: vector retrieval plus BM25-style keyword retrieval for sharper technical lookup
- `exploratory`: multi-query expansion for broader conceptual recall

### Persistent document library

Ingested PDFs are chunked, embedded, indexed, and surfaced in a library view with metadata and previews, even when the original raw file is no longer available.

## Architecture

### 1. Engine

The Python engine is responsible for ingestion, retrieval, orchestration, and structured generation.

- FastAPI exposes the API
- LangChain LCEL wires the retrieval and generation graph
- `llama-cpp-python` runs local GGUF models

Key endpoints:

- `POST /ingest`
- `POST /query`
- `POST /verify`
- `GET /notebook/{session_id}`
- `GET /models`
- `GET /library`

### 2. Vault

PostgreSQL with pgvector acts as the system of record for:

- vector embeddings
- chunk metadata
- research notebook entries
- chat history

### 3. Workbench

The Streamlit UI provides a browser-based local workbench for:

- querying the knowledge base
- uploading evidence
- reviewing notebook entries
- browsing the library
- selecting models and retrieval modes

## Repository layout

```text
.
|-- app/
|   |-- api.py
|   |-- core/
|   |-- database/
|   `-- utils/
|-- ui/
|   |-- streamlit_app.py
|   |-- ui_utils.py
|   `-- pages/
|-- data/
|-- models/
|-- scripts/
|-- docker-compose.yml
`-- requirements.txt
```

## Quick start

### Prerequisites

- Python 3.10+
- PostgreSQL 15+ with `pgvector`
- one or more GGUF models in `models/llms/`
- a local embedding model path configured in `.env`

### Environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/yourdb
DEFAULT_LLM_MODEL=your-model.gguf
EMBEDDING_MODEL_PATH=./models/embeddings/...
LLM_MODELS_DIR=./models/llms
POSTGRES_VECTOR_DIM=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
```

### Database

Initialize the schema:

```bash
psql -d yourdb -f app/database/schema.sql
```

### Run the backend

```bash
uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload
```

### Run the workbench

```bash
streamlit run ui/streamlit_app.py
```

## Workflow

1. Ingest PDFs into the vault.
2. Ask research questions in the workbench.
3. Inspect the belief report and citations.
4. Verify strong answers into the notebook.
5. Reuse verified knowledge in later sessions.

## Design principles

- Local-first by default
- Database-first persistence
- Auditable outputs over opaque fluency
- Modular separation between UI, engine, and storage
- Retrieval designed for both semantic and exact-match research

## License

Distributed under the Apache License. See [LICENSE](LICENSE).
