# STOP — Epic 02 / Sprint S02

## Objective

Temporal Role/Employment et currentness policy. Stop condition: "rôle
courant explicable" (current role must be explainable).

## Outputs

- `app/network_temporal.py`: `evaluate_currentness(relationship, as_of)`
  combines `CanonicalRelationshipV1.current_status` with the
  `valid_from`/`valid_to` interval S01 introduced, instead of trusting
  `current_status` alone. `valid_to` is inclusive (last valid day, not
  first invalid day) -- documented explicitly after a boundary test caught
  the ambiguity during writing this Sprint.
  - `status: invalidated` -> never current.
  - `valid_to` in the past -> not current, even if `current_status` still
    says `current` (a writer that forgot to update the status doesn't
    silently stay "current" forever).
  - `valid_from` in the future -> not current yet.
  - `status: former` with no `valid_to` set -> raises
    `CurrentnessConflict`: this is a genuinely contradictory record (says
    it ended but the interval is still open) and this Sprint's "role
    courant explicable" stop condition means surfacing that to a human,
    not guessing.
- `tests/test_network_temporal.py`: 9 tests covering every branch above
  plus the exact day boundary.

## Evidence

`python -m unittest tests.test_network_temporal -v`: 9/9 pass.

## Remaining

S03 (identity resolution) will call `evaluate_currentness` when deciding
whether a candidate duplicate's relationships still support a merge; S04's
read models expose `is_current`/`reason` on each relationship rather than
raw `current_status`.
