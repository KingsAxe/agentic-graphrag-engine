# Week 6 Upgrade Log

## Source

This log captures live testing feedback after the initial Week 6 frontend delivery.

## Logged Issues

### 1. Pending state feels static

**Observed:** Documents in `PENDING` state only showed a status label, which made ingestion feel idle rather than active.

**Action Taken:** Added animated loading dots beside `PENDING` and `PROCESSING` job pills in the frontend document list so the pending state visibly cycles while the job is waiting or running.

### 2. Duplicate uploads were allowed

**Observed:** The backend accepted duplicate uploads for the same filename in the same workspace, which polluted development retrieval and made test results noisier.

**Action Taken:** Added duplicate filename rejection in the upload route. The API now returns `409` when the current workspace already contains the same filename.

### 3. Query returned unrelated content, including the user's name

**Observed:** A query about `sample.txt` returned an extra line, `Kingsley Ohere November 03, 2025`, which did not belong to the target file.

**Cause:** Retrieval in the current development flow operates at the workspace level, so older vectors from prior uploaded documents can be returned unless the workspace is reset first. This is not model reasoning quality; it is retrieval contamination from shared workspace history.

**Next Fix Direction:** Add stronger document scoping controls for retrieval or a document selector in the query flow.

### 4. Graph lookup was skipped

**Observed:** The trace panel reported `Graph Lookup Skipped`.

**Cause:** Neo4j is still unavailable on `localhost:7687`, and mock mode is intentionally designed to skip graph reasoning rather than fail the entire query pipeline.

**Next Fix Direction:** Restore Neo4j connectivity so graph construction and graph lookup traces can run again.

### 5. UI is acceptable for testing but not final product direction

**Observed:** The current interface is useful for testing but does not reflect the intended final product quality or visual direction.

**Status:** Confirmed. The current frontend is a Week 6 operational console, not the final product design.

**Next Fix Direction:** Start a proper product-layer redesign after backend behavior and graph availability are stable enough to support higher-fidelity UX work.
