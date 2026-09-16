# STOP — Epic 09 / Sprint S05

## Objective

API Reach: Sequences, Tasks, Touchpoints. Stop condition: "stable v1"
-- read routes for sequences/steps/tasks/touchpoints, following the
same workspace-scoped, IDOR-safe, bounded-pagination convention as
every other v1 route (Epic 02-08).

## Outputs

- `app/reach_store.py`: workspace-scoped JSONL storage for
  `CanonicalSequenceV1`, `CanonicalStepV1`, `CanonicalTaskV1`,
  `CanonicalTouchpointV1` -- `put_sequence`/`get_sequence` (raises
  `SequenceNotFound`), `list_sequences` (status filter, bounded
  pagination), `put_step`/`list_steps_for_sequence` (ordered by
  `order`), `put_task`/`list_tasks_for_sequence`,
  `put_touchpoint`/`list_touchpoints_for_step`.
- `app/reach_routes.py`: `GET .../sequences`,
  `GET .../sequences/{id}`, `GET .../sequences/{id}/steps`,
  `GET .../sequences/{id}/tasks`,
  `GET .../sequences/{id}/steps/{step_id}/touchpoints` -- all gated
  through `require_workspace_access`, pagination bounded 1-100, every
  nested resource 404s on a cross-workspace `sequence_id` before
  touching the child collection (no leaking existence via a 200 on
  another workspace's child data).
- Wired `create_v1_reach_router(ROOT)` into `app/server.py`.
- `tests/test_reach_store.py`: 9 tests -- put/get, not-found, upsert,
  status filter, workspace isolation, nonpositive-limit rejection,
  step ordering, task/touchpoint scoping.
- `tests/test_reach_routes.py`: 10 tests -- unauthenticated 401,
  pagination bounds (above 100, below 1), own-workspace success for
  every route, cross-workspace 404 for sequence/steps/touchpoints.

## Evidence

`python -m unittest tests.test_reach_store tests.test_reach_routes -v`:
19/19 pass.
Full `python scripts/check_release.py`: 0 errors.
