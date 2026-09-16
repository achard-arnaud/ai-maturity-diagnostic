# STOP — Epic 05 / Sprint S04

## Objective

Demand queue/API/read model et édition optimiste. Stop condition:
"mutation sûre" (safe mutation) -- auth/409/idempotence.

## Outputs

- `app/demand_store.py`: `ArtifactStore`-backed JSONL storage, same
  workspace-scoped shape as Epic 02/03/04's stores, plus optimistic
  concurrency:
  - `create_demand`: refuses (`DemandAlreadyExists`) if `demand_id`
    already exists -- never silently replaces a record. Returns version 1.
  - `get_demand`: returns `(demand, version)`.
  - `update_demand(mutator, expected_version)`: applies `mutator` only if
    `expected_version` matches the record's current stored version;
    otherwise raises `DemandConflict` -- a stale edit is refused, not
    silently overwritten, and the caller must re-fetch and retry. Version
    is an internal store-tracked counter, never part of the
    `CanonicalDemandV1` schema itself.
  - `list_demands`: `status`/`company_entity_id` filters, stable sort,
    cursor pagination.
- `app/demand_routes.py`: `GET/POST /api/v1/workspaces/{workspace_id}/demands`,
  `GET/PATCH .../demands/{demand_id}`. Reuses `require_workspace_access`
  for the same IDOR-safe cross-workspace 404. `POST` on an existing
  `demand_id` returns 409. `PATCH` requires `expected_version` in the
  body (400 if absent) and returns 409 on a stale version, 404 on an
  unknown demand. Wired into `app/server.py`'s `build_app`.
- `tests/test_demand_store.py` (11): round-trip at version 1, duplicate
  create refused, isolation, correct-version update bumps version,
  stale-version update refused, missing-demand update refused,
  concurrent-edit-second-one-conflicts (the core optimistic-concurrency
  property), filters, pagination.
- `tests/test_demand_routes.py` (9): auth required, own-workspace list,
  cross-workspace 404, version surfaced on GET, duplicate create 409,
  correct-version PATCH succeeds and bumps version, stale-version PATCH
  409, missing expected_version 400, unknown-demand PATCH 404.

## Evidence

`python -m unittest tests.test_demand_store tests.test_demand_routes -v`:
20/20 pass. Full `python scripts/check_release.py`: 0 errors.
