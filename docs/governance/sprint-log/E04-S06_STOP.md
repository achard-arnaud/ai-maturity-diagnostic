# STOP — Epic 04 / Sprint S06

## Objective

Research review/accept/reopen/stale lifecycle. Stop condition: "review
explicite" (explicit review) -- role/audit tests.

## Outputs

- `app/research_review.py`: every state change is an explicit, audited
  action -- appends an event to Epic 01's `EventJournal`, same pattern as
  Epic 03's `signal_handoff.queue_research`.
  - `accept_case(root, case, claims, reviewer, reviewed_at)`: requires
    `status == "in_review"` and zero open blockers (via S01's
    `can_transition_case`), gate-1 completeness (S01's
    `compute_completeness` -- at least one active fact claim), a
    non-empty `reviewer`, and **separation of duties**: the reviewer must
    be distinct from the case's own `owner` -- the person who did the
    research does not also sign off on it. Appends `ResearchCaseAccepted`.
  - `reopen_case(root, case, reason, reopened_by, reopened_at)`: requires
    a non-empty reason and actor. Per the case state machine, only
    reachable from `in_review` or `stale` -- an `accepted` case must be
    explicitly marked `stale` first (mirrors
    `02_DOMAIN_AND_TRUTH_MODEL.md`'s "a fit is invalidated or marked
    stale when a referenced input changes", generalized to
    `ResearchCase`). Appends `ResearchCaseReopened` with the reason.
  - `mark_stale(root, case, stale_reason, marked_by, marked_at)`: requires
    a non-empty reason and actor, only from `accepted`. Appends
    `ResearchCaseMarkedStale`.
- `tests/test_research_review.py`: 15 tests -- accept rejected for no
  reviewer, same reviewer as owner, incomplete claim set, open blocker,
  and wrong status; accept succeeds and writes an audit event carrying
  the actor; reopen rejected for empty reason/actor and for going
  directly from `accepted` (must pass through `stale`); reopen from
  `stale` succeeds and the audit event carries the reason; mark_stale
  rejected for empty reason and from `open`, succeeds from `accepted`.

## Evidence

`python -m unittest tests.test_research_review -v`: 15/15 pass.
Full `python scripts/check_release.py`: 0 errors.
