# Week 7 Log: Workspace Reliability, Retrieval Quality, and Evaluation

## Summary

Week 7 focused on hardening the research workspace loop rather than pushing directly into graph visualization. The core product shell from Week 6 is now stricter about workspace boundaries, more explicit about retrieval scope, and more usable when ingestion jobs fail or need to be rerun.

This week also established the test and documentation scaffolding needed to finish runtime validation later, once the local infrastructure is healthy again.

## Completed Work

### Retrieval Scoping and Query Controls

* Added scoped query support to the API with `scope` and `document_ids` inputs.
* Added backend validation so document-scoped queries can only reference documents in the authenticated workspace.
* Updated Qdrant retrieval so queries can run against:
  * the full workspace
  * a single document
  * a selected set of documents
* Added retrieval-scope trace events so the reasoning trace now states what corpus was searched.
* Updated the frontend query console with scope controls and document selection UI.

### Workspace Safety and Auth Consistency

* Audited the current document, query, and reset flows for workspace-bound filtering.
* Tightened query document-scope validation with typed IDs and deduplicated scope handling.
* Standardized key route error responses for duplicate uploads and missing jobs in the authenticated workspace.
* Updated the recent-documents route to return the latest job per document, which is safer for future retry flows.

### Job Lifecycle Visibility and Failure Handling

* Expanded job status payloads with:
  * terminal state visibility
  * retry availability
  * action hints for the frontend
* Added a retry route at `POST /api/v1/documents/{job_id}/retry`.
* Updated the frontend console so failed jobs can be retried from the UI.
* Improved status messaging so users get clearer next-step guidance without needing backend logs.

### Regression Verification and Documentation

* Added `tests/verify_week_07.py` for scoped retrieval verification.
* Added `tests/verify_week_07_workspace_isolation.py` for workspace-isolation verification.
* Updated local runbooks and launch docs with the new Week 7 verification flow.
* Added:
  * a live task tracker in `docs/weekly-log/week-07-tasks.md`
  * a deferred validation log in `docs/weekly-log/week-07-validation.md`

## Validation Status

### Completed During Development

* Python compile verification passed for updated API routes and test scripts.
* Static verification of the new request models, routing changes, retry flow, and query-scope plumbing is complete.

### Deferred to End-of-Week Runtime Validation

These checks were intentionally left for final validation after implementation:

* Confirm that document-scoped queries do not leak unrelated workspace results in a live stack.
* Confirm that cross-workspace document scope requests are rejected through the full API path.
* Confirm that recent-document and job-status routes do not expose cross-workspace data.
* Confirm retry behavior and frontend state transitions against live services.

## Current Constraints

* PostgreSQL was unavailable in the current local environment when the Week 7 runtime verification script was executed.
* Because of that infrastructure issue, runtime validation remains deferred even though the Week 7 development work is in place.
* Neo4j-backed graph behavior is still not the focus of this sprint and remains outside the main Week 7 hardening loop.

## Current Deliverables

Week 7 currently delivers:

* scoped retrieval support
* stricter workspace-safe routing
* retry-aware job lifecycle handling
* stronger developer verification scaffolding
* updated implementation and validation logs

## Next Focus

1. Bring the local stack fully online and run the deferred Week 7 validation checklist.
2. Close the remaining unchecked runtime items in `week-07-tasks.md` and `week-07-validation.md`.
3. If validation passes cleanly, use the next sprint for graph visualization and deeper product-layer UX work.
