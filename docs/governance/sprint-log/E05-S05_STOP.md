# STOP — Epic 05 / Sprint S05

## Objective

UI Demands + dossier compte + resolvers. Stop condition: "unknowns
visibles" (unknowns visible) -- E2E detect→qualify.

As with Epic 02 S05 (Person 360) and Epic 04 S05 (Company 360), "UI" in
this Sprint means the resolver/read-model layer a UI consumes, not
frontend HTML/JS -- no frontend framework has been touched by any Epic
02-04 Sprint either; that remains explicitly deferred UX work.

## Outputs

- `app/demand_resolver.py`: `resolve_qualification_blocker(demand)`.
  Per `08_EVIDENCE_DECISION_AND_GATES.md`'s resolver contract
  (`why_blocked`/`required_state_or_evidence`/`owner_capability`/`cta`/
  `postcondition`/`cost_estimate`/`expiry`): turns S02's bare
  missing-dimension checklist into a full, actionable contract. Returns
  `None` when the demand isn't blocked.
- `app/company360_view.py` extended: the dossier now includes a
  `demands` section (Epic 04's Company 360 view, cross-Epic reuse) --
  each Demand annotated with `unknown_dimensions` (the list of
  not-yet-known field names), so unknowns are always visible in the
  dossier, never silently dropped.
- `app/demand_routes.py`: added `GET
  /api/v1/workspaces/{workspace_id}/demands/{demand_id}/resolver`,
  returning `{"blocked": false}` or `{"blocked": true, ...contract
  fields}`.
- `tests/test_demand_resolver.py` (3): passing checklist returns `None`;
  failing checklist returns a full contract with every field populated;
  the missing-buying-signal case is named in `why_blocked`.
- `tests/test_company360_view.py`: added a demands-integration test
  proving `unknown_dimensions` correctly lists unknown fields
  (`population`, `budget`) and excludes known ones (`problem`,
  `sponsor`).
- `tests/test_demand_routes.py`: added the resolver route test and the
  Sprint's E2E gate -- `test_e2e_detect_to_qualify_keeps_unknowns_visible`:
  detect (GET a fresh demand, several dimensions unknown) -> resolver
  reports blocked (no buying signal) -> transition to qualifying ->
  supply the missing sponsor via PATCH -> resolver clears (not blocked)
  -> final demand state still shows `population`/`budget` explicitly
  unknown, `sponsor` explicitly known -- qualifying never hides or
  fabricates the dimensions that remain unknown.

## Evidence

`python -m unittest tests.test_demand_resolver tests.test_company360_view tests.test_demand_routes -v`:
23/23 pass. Full `python scripts/check_release.py`: 0 errors.
