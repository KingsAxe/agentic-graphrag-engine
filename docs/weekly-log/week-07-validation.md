# Week 7 Deferred Validation Log

Use this file to track the end-of-week checks that should be run only after implementation is complete and the local stack is healthy.

## Runtime Validation Still Pending

- [ ] Validate that document-scoped queries avoid unrelated workspace results.
- [ ] Validate multi-document scoped queries against mixed workspace history.
- [ ] Validate that invalid `document_ids` are rejected cleanly by the query API.
- [ ] Validate that job status lookups never expose cross-workspace data.
- [ ] Validate that `recent` document listings only return the authenticated workspace.
- [ ] Validate that reset-workspace only deletes the authenticated workspace's data.
- [ ] Validate frontend scope controls against the live backend.
- [ ] Run the full Week 7 verification flow end to end with PostgreSQL, Qdrant, and the API running.

## Environment Notes

- Runtime validation was deferred during development because PostgreSQL was unavailable in the current local environment when `tests/verify_week_07.py` was executed.
