# STOP — Epic 03 / Sprint S05

## Objective

Discover queue/API/read models. Stop condition: "tri et filtres stables"
(stable sort and filters).

## Outputs

- `app/signal_store.py`: workspace-scoped, `ArtifactStore`-backed JSONL
  storage for `CanonicalSignalV1` records — same shape as Epic 02's
  `network_v1_store.py` (upsert-by-id, cursor pagination). `list_signals`
  supports `status`/`source_kind` filters and always sorts by
  `signal_id`, so a given filter over an unchanged signal set returns
  identical order on every call, regardless of insertion order.
- `app/signal_routes.py`: `GET /api/v1/workspaces/{workspace_id}/signals`
  (paginated, filtered) and `.../{signal_id}` (deep link). Reuses
  `require_workspace_access`, wired into `app/server.py`'s `build_app`.
- `tests/test_signal_store.py`: 7 tests (round-trip, isolation, both
  filters, explicit order-independence test, pagination).
- `tests/test_signal_routes.py`: 7 tests against the real FastAPI app —
  auth, bounded pagination, deep link, unknown-signal 404, and two IDOR
  checks (list and single-entity cross-workspace 404).

## Evidence

`python -m unittest tests.test_signal_store tests.test_signal_routes -v`:
14/14 pass.
