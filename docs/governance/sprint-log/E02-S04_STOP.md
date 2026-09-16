# STOP — Epic 02 / Sprint S04

## Objective

Read models + API v1 people/companies/relationships. Stop condition:
"deep links stables" (stable deep links), with auth/pagination/IDOR gates.

## Outputs

- `app/network_v1_store.py`: workspace-scoped JSONL storage for v1
  entities under `data/private/network_v1/<workspace_id>/...`, atomic via
  `ArtifactStore`, upsert-by-entity-id, cursor pagination
  (`list_entities(..., limit, cursor)` -> `Page(items, next_cursor)`).
  Deliberately separate from the legacy `data/private/network/*.jsonl`
  files (untouched, per ADR-009).
- `app/network_v1_routes.py`: the repo's **first** `/api/v1/...` routes
  (`06_ROUTE_CONTEXT_AND_API_MODEL.md`'s target shape), mounted at
  `/api/v1/workspaces/{workspace_id}/{people,companies,relationships}`
  (list, paginated) and `.../{entity_id}` (get, the stable deep link).
  Reuses `app.authruntime.deps.require_workspace_access` — the same
  dependency every other workspace-scoped route already uses, so a
  cross-workspace lookup 404s (never 403, per ADR-007 §1: don't disclose
  another workspace owns the object) exactly like the rest of the app.
  Wired into `app/server.py`'s `build_app` via `app.include_router(...)`.
- `tests/test_network_v1_store.py`: 6 tests (round-trip, upsert, workspace
  isolation, pagination cursor behavior).
- `tests/test_network_v1_routes.py`: 8 tests against the real FastAPI app
  (`starlette.testclient.TestClient` over `app.authruntime.app.create_app`
  + the new router) — unauthenticated 401, authenticated 200, a stable
  deep link by entity_id, pagination limit bounded to [1, 100], unknown
  entity 404, **two explicit IDOR tests** (a member of `ws-b` cannot list
  `ws-a`'s people, nor fetch a specific `ws-a` entity_id even if they
  already know it), and an admin bypass.

## Evidence

`python -m unittest tests.test_network_v1_store tests.test_network_v1_routes -v`:
14/14 pass.

## Remaining

No data actually populates these routes outside tests yet — S06's
migration/backfill is what puts real legacy-derived records into
`data/private/network_v1/`. S05 composes person/account 360 views on top
of this same store.
