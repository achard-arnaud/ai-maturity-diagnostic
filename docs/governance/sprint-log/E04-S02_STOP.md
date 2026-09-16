# STOP — Epic 04 / Sprint S02

## Objective

Queue, ownership, SLA, blockers et resume. Stop condition: "dossier
reprenable" (a case can be picked back up) -- transition/idempotence
tests.

## Outputs

- `app/research_queue.py`: pure functions over the
  `CanonicalResearchCaseV1` dict shape.
  - `claim_ownership`/`release_ownership`: claiming an unowned case sets
    `owner`; re-claiming with the *same* owner is idempotent (returns an
    equal dict, no state change); claiming with a *different* owner while
    already owned raises `OwnershipError` -- ownership must be released
    first.
  - `sla_deadline`/`is_sla_breached`: SLA is `created_at + 5 days`
    (`DEFAULT_SLA_DAYS`); `accepted`/`stale` cases never breach (a closed
    or intentionally-parked case isn't late).
  - `add_blocker`/`resolve_blocker`/`count_open_blockers`: adding a blocker
    forces `status = blocked`; resolving is idempotent (resolving an
    already-resolved or nonexistent blocker is a no-op, matching the same
    idempotence contract as Epic 03's `EventJournal` idempotency keys).
  - `resume_case`: raises `TransitionError` unless the case is currently
    `blocked` *and* has zero open blockers -- this is exactly "dossier
    reprenable": a case can always be resumed once its blockers clear, and
    never before.
- `app/research_case_store.py`: workspace-scoped `ArtifactStore`-backed
  JSONL storage for `CanonicalResearchCaseV1`, structurally identical to
  Epic 03's `signal_store.py` (upsert-by-`research_case_id`, stable sort,
  cursor pagination, `status`/`owner` filters).
- `tests/test_research_queue.py`: 14 tests (ownership claim/idempotent
  reclaim/conflict/release-then-reclaim; SLA deadline math, not-yet and
  past-breach, accepted-never-breaches; blocker add/resolve/idempotent
  double-resolve; resume rejected while open blocker or wrong status,
  accepted once cleared).
- `tests/test_research_case_store.py`: 8 tests, same shape as
  `test_signal_store.py` (round-trip, isolation, upsert, both filters,
  order-independence, pagination).

## Evidence

`python -m unittest tests.test_research_queue tests.test_research_case_store -v`:
22/22 pass. Full `python scripts/check_release.py`: 0 errors.
