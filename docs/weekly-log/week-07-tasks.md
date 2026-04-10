# Week 7 Task Tracker

Use this file as the live implementation checklist for Week 7. Check items off as they are completed.

## Retrieval Scoping and Query Controls

- [x] Add backend support for document-scoped retrieval.
- [x] Add backend support for multi-document retrieval scope.
- [x] Extend the query request model to accept retrieval scope inputs.
- [x] Update query route handling to pass scope into retrieval execution.
- [x] Include retrieval scope details in reasoning trace output.
- [x] Add frontend controls for selecting query scope.
- [ ] Validate that document-scoped queries avoid unrelated workspace results.

## Workspace Safety and Auth Consistency

- [x] Audit all document routes for workspace-safe filtering.
- [x] Audit query routes for workspace-safe filtering.
- [x] Audit reset flows for workspace-safe behavior.
- [x] Ensure duplicate upload checks are workspace-specific and consistent.
- [x] Ensure missing job and lookup errors are consistent across routes.
- [ ] Verify no route returns cross-workspace data.

## Job Lifecycle Visibility and Failure Handling

- [x] Expand backend job status responses for clearer terminal states.
- [x] Improve frontend status rendering for `PENDING`, `PROCESSING`, `COMPLETED`, and `FAILED`.
- [x] Add a retry or rerun path for failed ingestion jobs.
- [x] Improve empty and error states in the workspace console.
- [x] Confirm users can diagnose job outcomes without backend log access.

## Regression Verification and Developer Feedback Loops

- [x] Add a Week 7 verification script for scoped retrieval.
- [x] Add verification coverage for document status and trace output.
- [x] Add verification coverage for workspace isolation behavior.
- [x] Update runbook documentation for Week 7 workflow changes.
- [x] Update launch documentation for new query-scoping behavior.

## Release Readiness

- [x] Review the full Week 7 checklist for remaining gaps.
- [ ] Run verification flow end to end.
- [x] Update the Week 7 log with completed work and outcomes.
