# STOP — Epic 12 / Sprint S03

Home, Discover and Research now render workspace-scoped queues from their
real endpoints inside the route-owned GTM view. Empty and error states are
explicit; sector or signal data is never promoted into demand by the client.

Evidence: `python -m unittest tests.test_gtm_upstream_spaces -v`.

## Correction (post-E13 closeout audit, 2026-09-17)

The claim above was **not accurate for Research** as originally shipped:
the space called `GET /api/v1/workspaces/{workspace}/research-cases`, but
no backend route by that name existed anywhere in `app/` (Home and
Discover were correct). `tests.test_gtm_upstream_spaces` did not catch this
because it only asserted the endpoint string appeared in the frontend
source, never that the backend served it. Found and fixed in the same
closeout pass: `app/research_routes.py` now exposes the route over the
already-existing (already-tested) `app.research_case_store.list_cases`/
`get_case`; the guarding test now fires a real request and checks for
401/403 (route exists) rather than only matching a string. See
`docs/audit/post-epic/DOCUMENTATION_DRIFT.md` item 8 for the full trace.
This note is appended rather than editing the paragraph above, so the
record shows what was actually claimed and verified at S03 time.
