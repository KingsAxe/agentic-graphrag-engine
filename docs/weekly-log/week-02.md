# Week 2 Log: Ingestion and Task Processing

**Date:** 2026-03-31
**Commit:** `feat: Week 2 - Async ingestion pipeline and Celery task execution`

**Completed Actions:**
* **Virtual Environment & Dependencies:** Resolved Python package installations, created the `RagV2` isolated environment, and implemented a strict `.gitignore` to prevent repository bloat.
* **Database Models:** Designed the `Document` and `IngestionJob` relational schema in PostgreSQL for reliable job polling and state tracking.
* **Celery Orchestration:** Configured `celery_app.py` linked to our Redis broker. Developed the `process_document_task` to handle extraction entirely asynchronously so the API gateway remains unblocked.
* **Document Parser:** Integrated `PyMuPDF` (`fitz`) to rapidly extract raw textual data from complex PDFs.
* **Semantic Vectorization:** Instantiated the `BAAI/bge-m3` embedding model locally via `sentence-transformers` for heavy, high-dimension (1024) dense encodings.
* **Qdrant Storage Wrapper:** Built `qdrant_service.py` to auto-initialize the `documents` collection and upsert text chunks tightly coupled with their semantic vectors and payload metadata (Workspace ID, Document ID, Chunk Index).
* **API Endpoints:** Added `POST /documents/upload` (for file handoff) and `GET /documents/{job_id}/status` (for client polling) to the FastAPI gateway.
* **Environment Bootstrapping:** Developed the `create_workspace.py` utility to dynamically generate API Auth Keys for local testing against the running Docker stack.
