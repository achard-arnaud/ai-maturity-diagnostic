# STOP — Epic 03 / Sprint S03

## Objective

SavedSearch, List, SmartList et Watchlist. Stop condition: "listes
versionnées" (versioned lists).

## Outputs

- `app/signal_lists.py`:
  - `matches_criteria`/`run_saved_search`: pure filter over signals;
    unknown criteria keys are rejected (never silently ignored); results
    always sorted by `signal_id`, so membership is deterministic
    regardless of input order.
  - `SignalList` (frozen dataclass): `list_id`, `workspace_id`, `kind`
    (`list`/`smart_list`/`watchlist`), `version`, `member_ids` (deduped,
    sorted tuple).
  - `create_list`/`update_list_members`: a plain List starts at version 1;
    every membership change returns a **new** object at version+1,
    leaving the prior version untouched (no in-place mutation).
  - `create_watchlist`: mechanically a List (same versioning) whose
    members are company `entity_id`s instead of `signal_id`s.
  - `materialize_smart_list`: re-runs a SavedSearch's criteria against the
    current signal set and returns a new versioned snapshot; re-running
    against unchanged signals reproduces identical membership (but a new
    version number, since it's a fresh materialization); re-running
    after signals change reflects the change.
- `tests/test_signal_lists.py`: 13 tests covering deterministic
  membership (order-independence, AND-ed criteria, unknown-key
  rejection), versioning (increment, immutability, dedup/sort), Watchlist
  mechanics, and SmartList re-materialization (stable vs. changed).

## Evidence

`python -m unittest tests.test_signal_lists -v`: 13/13 pass.

## Remaining

No storage layer yet for `SignalList`/signals themselves — S05 wires
read models (same `/api/v1/...` pattern as Epic 02).
