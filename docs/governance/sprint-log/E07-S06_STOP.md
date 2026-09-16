# STOP — Epic 07 / Sprint S06

## Objective

UI Fit workbench + E2E Demand→Fit. Stop condition: "target creation
gated" -- visual/functional E2E.

As with every prior Epic's "UI" sprint, this means the gate/read-model
layer a UI (and Epic 08) consumes, not frontend HTML/JS.

## Outputs

- `app/fit_targeting_gate.py`: `can_create_target_plan(fit_assessment,
  now)` -- the one function Epic 08 (Buying Committee and Target Plans)
  must call before creating a TargetPlan. Returns `(allowed, reason)`;
  blocks unless the assessment's `status == "decided"` **and**
  `verdict.verdict == "PURSUE"` **and**, if that PURSUE came from a
  score override, the override has not expired (an expired override is
  a standing authorization that must be re-reviewed, not honored
  forever).
- `tests/test_fit_targeting_gate.py`: 5 unit tests on the gate itself
  (not-decided, REJECT-verdict, PURSUE allows, expired override blocks,
  unexpired override allows) plus the Sprint's own E2E gate: 3 full
  chains through every module this Epic built --
  `create_input_lock` (S01) -> `submit_for_review`/`can_compute_score`
  (S02) -> `compute_coverage`/`compute_explainable_score` (S03) ->
  `decide_fit` (S04) -> `fit_store` persistence (S05) ->
  `can_create_target_plan` (this Sprint). One chain ends in a clean
  PURSUE that authorizes targeting; one hits a failed hard gate (PURSUE
  correctly raises, REJECT is decided instead, and targeting stays
  blocked); one confirms a still-draft assessment never authorizes
  targeting.

## Evidence

`python -m unittest tests.test_fit_targeting_gate -v`: 8/8 pass.
Full `python scripts/check_release.py`: 0 errors.
Legacy network suite (35 tests) re-verified unchanged.

## Epic 07 status

All 6 Sprints closed (S01 FitAssessment schema and input version
locking; S02 hard gates/blockers/resolvers, no score bypass; S03
explainable scoring/coverage/gaps/alternatives; S04 review/decision/
override/stale lifecycle with bounded overrides; S05 API with 409/
idempotence; S06 the targeting gate and full E2E). Epic acceptance
(decision reproducible, contradictory visible, invalidation on
superseded input, TargetPlan impossible before an authorized verdict) is
verified: S01 proves reproducibility via input-lock hashing; S02's
exhaustive gate matrix proves no bypass exists; S04 proves overrides are
bounded and audited; S06 proves the targeting gate holds end-to-end.
