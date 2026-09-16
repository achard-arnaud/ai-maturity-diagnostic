# STOP — Epic 07 / Sprint S05

## Objective

API queue/detail/compare/read models. Stop condition: "stable v1" --
contract/409/idempotence.

## Outputs

- `app/fit_store.py`: same optimistic-concurrency shape as Epic 05's
  `demand_store` -- `create_fit` refuses an existing
  `fit_assessment_id`, `update_fit` requires a matching
  `expected_version` and raises `FitConflict` on a stale one, `list_fits`
  filters by `status`/`demand_id` with stable sort and cursor pagination.
- `app/fit_routes.py`: `GET/POST /api/v1/workspaces/{workspace_id}/
  fit-assessments`, `GET/PATCH .../fit-assessments/{id}`, `GET
  .../fit-assessments/compare?left_id=&right_id=` (registered *before*
  the `{fit_assessment_id}` catch-all route, so `compare` is never
  swallowed as a literal id). PATCH requires `expected_version` (400 if
  absent), 409 on a stale version or duplicate create, 404 on unknown.
  Wired into `app/server.py`.
- `tests/test_fit_store.py` (8), `tests/test_fit_routes.py` (7):
  round-trip/duplicate-refused/isolation/version-bump/stale-conflict/
  filters at the store layer; auth-required, cross-workspace 404,
  duplicate-create 409, stale-PATCH 409, missing-expected_version 400,
  the compare route correctly reporting a shared input lock, and an
  idempotence check (re-applying an update against the version the
  previous call returned succeeds safely, no double-application hazard).

## Evidence

`python -m unittest tests.test_fit_store tests.test_fit_routes -v`:
15/15 pass. Full `python scripts/check_release.py`: 0 errors.
