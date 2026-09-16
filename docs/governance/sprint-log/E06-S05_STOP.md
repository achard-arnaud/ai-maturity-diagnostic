# STOP — Epic 06 / Sprint S05

## Objective

API/search/diff/read models. Stop condition: "deep links stables"
(stable deep links) -- contract/performance fixtures.

## Outputs

- `app/product_store.py`: flat `ArtifactStore`-backed storage for
  `CanonicalProductV1` (upsert-by-id, stable sort); visibility filtering
  is deliberately not this layer's job -- it happens at the route layer
  via S04's `product_visibility`.
- `app/product_diff.py`: `diff_snapshot_content(old, new)` -- pure,
  read-only. Scalar fields (`name`/`description`) report `{old, new}`
  only when changed; list fields (`exclusions`/`hard_gates`/
  `capabilities`) report `{added, removed}` as set differences, so
  reordering an otherwise-unchanged list never shows up as a diff.
- `app/product_routes.py`:
  `GET /api/v1/workspaces/{workspace_id}/products` (visibility-filtered
  list), `GET .../products/{product_id}` (deep link, 404s if invisible
  to this workspace -- same "unknown and invisible look identical"
  discipline as every other v1 route's IDOR handling), `GET
  .../products/{product_id}/snapshots/{snapshot_id}` (deep link,
  cross-checks the snapshot's own `product_id` and `owner_scope`), `GET
  .../products/{product_id}/diff?from_snapshot_id=...&to_snapshot_id=...`
  (thin wrapper over the pure diff function). Wired into
  `app/server.py`.
- `tests/test_product_store.py` (4), `tests/test_product_diff.py` (6):
  store round-trip/upsert/sort; diff identical/scalar-change/list-add/
  list-remove/reorder-is-not-a-diff/unchanged-fields-absent.
- `tests/test_product_routes.py` (8): auth required; list shows shared +
  own-workspace only; another workspace's product 404s; the Sprint's
  core property -- **deep links stable**: fetching the same product or
  snapshot id twice returns byte-identical JSON both times; unknown
  snapshot 404s; the diff route's output matches calling the pure
  function directly (contract fixture).

## Evidence

`python -m unittest tests.test_product_store tests.test_product_diff tests.test_product_routes -v`:
17/17 pass. Full `python scripts/check_release.py`: 0 errors.
