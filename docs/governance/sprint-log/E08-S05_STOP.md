# STOP — Epic 08 / Sprint S05

## Objective

API people↔target plan + privacy controls. Stop condition: "accès
borné" (bounded access) -- IDOR/PII/pagination.

## Outputs

- `app/target_plan_store.py`: workspace-scoped `ArtifactStore`-backed
  storage for `CanonicalTargetPlanV1` (upsert, status filter, cursor
  pagination) and `CanonicalStakeholderRoleV1` (scoped per plan).
- `app/target_plan_routes.py`: `GET
  /api/v1/workspaces/{workspace_id}/target-plans` (bounded 1-100
  pagination, 400 outside that range), `GET .../target-plans/{id}`,
  `GET .../target-plans/{id}/stakeholders`, `GET
  .../target-plans/{id}/committee-graph` (thin wrapper over Epic 08
  S04's `build_committee_graph`, active stakeholders only). Every route
  requires auth and 404s a plan/stakeholders/graph invisible to the
  calling workspace -- the same IDOR-safe convention as every other v1
  route: a plan belonging to another workspace looks identical to a
  nonexistent one. Wired into `app/server.py`.
- `tests/test_target_plan_store.py` (6), `tests/test_target_plan_routes.py`
  (8): round-trip/isolation/filter/pagination at the store layer; auth
  required, pagination bounded both above 100 and below 1, cross-
  workspace 404 on the plan/stakeholders/committee-graph routes (the
  Sprint's core "accès borné" property), own-workspace access succeeding
  normally, and the committee-graph route correctly returning nodes for
  active stakeholders.

## Evidence

`python -m unittest tests.test_target_plan_store tests.test_target_plan_routes -v`:
14/14 pass. Full `python scripts/check_release.py`: 0 errors.
