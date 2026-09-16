# STOP — Epic 05 / Sprint S03

## Objective

Claim/Evidence links, confidence et contradiction. Stop condition:
"provenance complète" (complete provenance) -- lineage/stale tests.

## Outputs

- `app/demand_evidence.py`:
  - `link_claim`/`unlink_claim`: idempotent claim_ids mutation (re-linking
    or unlinking a claim_id already in/out of the list is a no-op).
  - `has_complete_provenance(demand, claims_by_id)`: a Demand with no
    known dimension trivially has complete (empty) provenance -- there
    is nothing yet to ground. Once any dimension is known, at least one
    *still-active* linked claim is required; a known field backed only
    by a superseded/retracted claim is incomplete provenance, exactly
    like an unbacked one.
  - `is_provenance_stale(demand, claims_by_id)`: true only when the
    Demand *has* linked claims but none remain active -- its grounding
    rotted out from under it even though the Demand record itself never
    changed. A Demand with no linked claims at all is not "stale" (it
    was never grounded to begin with; that's `has_complete_provenance`'s
    job to flag).
  - `compute_confidence(demand, claims_by_id)`: best `evidence_grade`
    (Epic 03/04's P1/P2/U1/W1/N0 scale) among the Demand's *active*
    linked claims only -- a superseded claim's grade never counts, even
    if it was P1.
- `tests/test_demand_evidence.py`: 18 tests -- link/unlink idempotence;
  provenance completeness (trivial-empty, known-without-claims,
  known-with-active-claim, known-with-only-superseded-claim); staleness
  (no claims, active claim, all-superseded/retracted, mixed with at
  least one active); confidence across the grade scale, best-of-multiple,
  and superseded claims excluded from the confidence calculation.

## Evidence

`python -m unittest tests.test_demand_evidence -v`: 18/18 pass.
Full `python scripts/check_release.py`: 0 errors.
