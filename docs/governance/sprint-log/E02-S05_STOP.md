# STOP — Epic 02 / Sprint S05

## Objective

Person 360 et Account 360 composés, provenance visible. Stop condition:
"pas de fusion de vérités" (no fusion of truths).

## Outputs

- `app/person_view.py`: `get_person_360(root, workspace_id, entity_id,
  as_of=...)` composes the v1 person record, its relationships (each
  tagged with a computed `currentness` via S02's `evaluate_currentness`,
  never fabricated), and the companies those relationships point at --
  as three distinct top-level sections, following the same pattern
  `app.account_view.get_account_360` already established for
  company/qualification/reach/blocker-actions. A relationship's own
  `provenance`/`evidence_grade` is never copied onto the person or the
  company, and vice versa.
- A contradictory relationship (S02's `CurrentnessConflict`, e.g.
  `current_status: former` with no `valid_to`) surfaces in the view as
  `currentness: {is_current: null, requires_human_review: true, reason:
  ...}` rather than crashing the whole 360 view or silently guessing.
- `GET /api/v1/workspaces/{workspace_id}/people/{entity_id}/360` added to
  `app/network_v1_routes.py`, same workspace-scoped auth as every other
  v1 route.
- `tests/test_person_view.py`: 6 tests (unknown person -> None,
  multi-section composition, currentness attached without mutating
  provenance, contradictory relationship -> human-review flag, a
  relationship pointing at a not-yet-backfilled company is omitted not
  crashed, another person's relationships are excluded).
- 2 more route tests in `tests/test_network_v1_routes.py` (200 with all
  three sections present, cross-workspace 404).

## Evidence

`python -m unittest tests.test_person_view tests.test_network_v1_routes -v`:
16/16 pass (6 + 10).

## Remaining

`app.account_view.get_account_360` (the legacy company-centric 360) is
untouched by this Sprint -- Epic 02 doesn't require merging the legacy and
v1 360 views into one endpoint, and doing so would itself risk exactly the
"fusion de vérités" this Sprint's stop condition forbids. Both 360 views
coexist: legacy for the existing UI, v1 `/people/{entity_id}/360` for
whatever consumes the new API surface going forward.
