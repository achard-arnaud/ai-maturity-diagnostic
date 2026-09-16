# STOP — Epic 04 / Sprint S07

## Objective

Evals de contamination, coverage et factuality. Stop condition: "seuils
de release atteints" (release thresholds reached) -- gold set thresholds.

## Outputs

- `app/research_evals.py`: a gold-set-style eval suite over a set of
  `ResearchCase`s and `Claim`s.
  - `check_contamination(claims)`: case-insensitive scan of each claim's
    free-text `statement` for banned product/offer vocabulary
    (`CONTAMINATION_TOKENS`). This is content-level, complementing S05's
    structural (field-shape) contamination guard.
  - `compute_coverage(cases, claims_by_case)`: share of cases whose claim
    set passes S01's gate-1 completeness.
  - `compute_factuality(claims, evidence_by_id, claims_by_id)`: share of
    `fact`-typed claims whose lineage validates cleanly via S01's
    `validate_claim_lineage`.
  - `run_evals(cases, claims, evidence_by_id, thresholds)`: runs all
    three and returns an `EvalReport`. Default `EvalThresholds`:
    `max_contamination=0` (zero tolerance -- any contaminated claim fails
    the whole eval regardless of coverage/factuality), `min_coverage=0.8`,
    `min_factuality=0.9`. Thresholds are overridable per caller.
- `tests/test_research_evals.py`: 14 tests -- contamination
  clean/flagged/case-insensitive; coverage empty/full/partial; factuality
  no-fact-claims/valid/invalid; and 5 gold-set threshold tests at the
  `run_evals` level (clean set passes; a contaminated set fails even
  though coverage/factuality would pass; low coverage fails; low
  factuality fails; custom lenient thresholds let a set through that the
  defaults would reject).

## Evidence

`python -m unittest tests.test_research_evals -v`: 14/14 pass.
Full `python scripts/check_release.py`: 0 errors.

## Epic 04 status

All 7 Sprints closed (S01 ResearchCase/Claim/Evidence contracts and
completeness; S02 queue/ownership/SLA/blockers/resume; S03 orchestration
passes with budget/checkpoints; S04 contradiction/falsifier/side-story
bounded workflows; S05 Company 360 read model; S06 review/accept/reopen/
stale lifecycle; S07 contamination/coverage/factuality evals).
