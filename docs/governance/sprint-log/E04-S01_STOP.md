# STOP — Epic 04 / Sprint S01

## Objective

ResearchCase/Claim/Evidence contracts et completeness policy. Stop
condition: "vérité typée" (typed truth) -- schema/claim lineage tests.

## Outputs

- `contracts/evidence_v1.schema.yaml`: `CanonicalEvidenceV1`. Per
  `08_EVIDENCE_DECISION_AND_GATES.md`, carries source, locator,
  `evidence_type` (which of fact/publication/observation/consultation date
  `dated_at` records), a bounded `excerpt` (never the full document), a
  content `hash`, `license`, `entity_refs`, `supports_claim_ids`/
  `contests_claim_ids`, `freshness`, and `evidence_grade` (reusing Epic
  03's P1/P2/U1/W1/N0 scale). Immutable by convention -- a correction is a
  new Evidence record, never an edit.
- `contracts/claim_v1.schema.yaml`: `CanonicalClaimV1`. `claim_type` is one
  of the three sub-automated truth types from
  `02_DOMAIN_AND_TRUTH_MODEL.md`: `fact` (an accepted observation),
  `inference` (an explicable conclusion from other claims/evidence), or
  `hypothesis` (needs an owner and a due date). A claim is never edited in
  place: `status` moves `active -> superseded` via a new claim's
  `supersedes_claim_id`, or `active -> retracted`.
- `contracts/research_case_v1.schema.yaml`: `CanonicalResearchCaseV1`.
  Product-blind by construction -- no product/offer field exists anywhere
  on the object. Tracks `blockers` (each with `opened_at`/`resolved_at`)
  and an optional `origin_signal_id` linking back to Epic 03's
  `ResearchQueued` handoff.
- `app/research_policy.py`:
  - `can_transition_case(current, next, *, open_blockers)`: the case state
    machine (`open -> in_progress/blocked -> in_review -> accepted/
    reopened`, `accepted -> stale -> reopened`). A case can never reach
    `accepted` while `open_blockers > 0`, mirroring
    `08_EVIDENCE_DECISION_AND_GATES.md`'s "a score never turns ... an open
    critical blocker into PURSUE".
  - `validate_claim_lineage(claim, evidence_by_id, claims_by_id)`: a
    `fact` claim needs >=1 `evidence_id` that exists and isn't
    graded `N0`; an `inference` needs `evidence_ids` or
    `derived_from_claim_ids` that exist; a `hypothesis` needs
    `hypothesis_owner` and `hypothesis_due_at`. Returns the first
    `ClaimLineageError` found, or `None`.
  - `is_claim_type_promotion(old, new)`: pure predicate (hypothesis <
    inference < fact) for callers/tests to assert that no automated path
    silently promotes a claim's truth type.
  - `compute_completeness(claims)`: Gate #1 from the evidence/decision
    doc's gate order -- a case is complete once it has at least one
    *active* `fact` claim; superseded/retracted claims don't count.
- `tests/test_research_policy.py`: 23 tests covering the case transition
  table (including the blocker-gates-acceptance rule), claim lineage for
  all three claim types (valid and invalid cases, missing
  evidence/claim references), the promotion predicate, and completeness
  (empty, complete, superseded-doesn't-count, hypothesis-only-is-
  incomplete).

## Evidence

`python -m unittest tests.test_research_policy -v`: 23/23 pass.
Full `python scripts/check_release.py`: 0 errors (after installing this
fresh container's missing runtime deps -- `itsdangerous`, `authlib`,
`python-multipart`, `pillow`, `ruff`, `coverage`, `python-docx` -- none of
which are code changes, just container setup).
