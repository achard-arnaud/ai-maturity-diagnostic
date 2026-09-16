# STOP — Epic 08 / Sprint S02

## Objective

Currentness/authority/warm-path evidence policies. Stop condition:
"ready strict" -- stale/conflict gold cases.

## Outputs

- `app/target_currentness.py`: `evaluate_readiness(role,
  currentness_is_current, currentness_requires_review,
  influence_confidence)`. Strict, explicit conditions for readiness:
  - A currentness conflict requiring human review (Epic 02's
    `CurrentnessConflict` path) blocks outright, whatever the role.
  - A relationship that isn't current blocks outright, whatever the
    role.
  - For authority-bearing roles (`sponsor`/`champion` -- S01's
    `AUTHORITY_ROLES`), `low`/`unknown` influence confidence blocks: a
    job title alone is never accepted as proof of authority. Every other
    role needs no confidence threshold at all.
  - Multiple failing conditions are all reported, not just the first.
- `tests/test_target_currentness.py`: 9 tests, the gold cases named in
  the Epic's own invariants -- current+strong-confidence sponsor is
  ready; a stale relationship blocks regardless of role; a currentness
  conflict blocks; the title-alone-never-proves-authority gold case
  (current relationship, sponsor role, but only "unknown" confidence --
  blocked); low-confidence champion also blocked; a non-authority role
  needs no confidence at all; a blocker role is ready regardless of
  confidence; medium confidence is sufficient for a sponsor; a
  conflict-and-weak-confidence case reports both reasons.

## Evidence

`python -m unittest tests.test_target_currentness -v`: 9/9 pass.
Full `python scripts/check_release.py`: 0 errors.
