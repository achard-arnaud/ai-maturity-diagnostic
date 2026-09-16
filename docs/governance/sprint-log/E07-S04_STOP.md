# STOP — Epic 07 / Sprint S04

## Objective

Review/decision/override/stale lifecycle. Stop condition: "override
borné" (bounded override) -- RBAC/audit/expiry.

## Outputs

- `app/fit_lifecycle.py`:
  - Transition table: `draft -> in_review -> decided -> stale ->
    in_review` (a stale fit is re-reviewed, not restarted from draft).
  - `decide_fit`: RBAC-gated to the `fit_reviewer` role
    (`FitAuthorizationError` otherwise). A `PURSUE` verdict is
    absolutely refused while any hard gate has failed or any blocker is
    open -- **no override parameter can make this true**; `REJECT`/
    `HOLD` never require gates or a score at all (you can always reject
    or hold, regardless of the state of the world). Once gates/blockers
    are clear, a `PURSUE` below `PURSUE_SCORE_THRESHOLD` (0.5) requires a
    **bounded** override: a non-empty `override_reason` *and* a mandatory
    `override_expiry` -- an override is a temporary human judgment call,
    never permanent. Every decision appends a `FitDecided` audit event to
    Epic 01's `EventJournal`.
  - `mark_stale`/`reopen_fit`: each requires a non-empty reason.
  - `is_override_expired(verdict_record, now)`: a non-override verdict
    never expires; an override verdict is checked against its own
    `override_expiry`.
- `tests/test_fit_lifecycle.py`: 19 tests -- submit-for-review
  transitions; decide_fit RBAC rejection; the two absolutely-non-
  overridable cases (PURSUE blocked by a failed gate, PURSUE blocked by
  an open blocker -- both rejected even *with* an override reason and
  expiry supplied); PURSUE succeeding cleanly above threshold; PURSUE
  below threshold rejected with no override, rejected with a reason but
  no expiry, and succeeding once both reason and expiry are supplied;
  REJECT never needing gates or a score; unknown verdict rejected; the
  audit event; mark_stale/reopen reason requirements and successes; and
  override-expiry checking (never expires without override, not yet
  expired, expired).

## Evidence

`python -m unittest tests.test_fit_lifecycle -v`: 19/19 pass.
Full `python scripts/check_release.py`: 0 errors.
