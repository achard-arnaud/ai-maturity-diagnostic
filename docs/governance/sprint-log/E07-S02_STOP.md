# STOP — Epic 07 / Sprint S02

## Objective

Hard gates/blockers/resolvers policy engine. Stop condition: "aucun
score bypass" (no score bypass) -- exhaustive gate matrix.

## Outputs

- `app/fit_gates.py`:
  - `evaluate_hard_gates(product_snapshot, gate_checks)`: every
    `hard_gate` named on the (immutable) snapshot gets a `GateResult`; a
    gate with no corresponding check defaults to *not passed*
    (`"not yet evaluated"`) -- an unevaluated gate is never treated as
    silently satisfied.
  - `can_compute_score(gates, open_blocker_count)`: the single choke
    point this Sprint exists to build. Returns true in exactly one case:
    every gate passed **and** zero open blockers. No parameter or code
    path in this module can force a bypass.
  - `failed_gate_reasons`: human-readable reasons for every failed gate.
  - `resolve_gate_blocker(gate)`: a full
    `08_EVIDENCE_DECISION_AND_GATES.md` resolver contract for a failed
    gate (why_blocked/required_state_or_evidence/owner_capability/cta/
    postcondition/cost_estimate/expiry), `None` when the gate passed.
- `tests/test_fit_gates.py`: 10 tests, including the Sprint's own
  exhaustive gate matrix -- `test_exhaustive_matrix_over_three_gates_and
  _blocker_counts` walks all 8 pass/fail combinations across 3 gates
  times 3 blocker counts (24 cases total) and asserts `can_compute_score`
  matches "all gates passed AND zero blockers" in every single one, plus
  targeted cases (one failed gate among passing ones still blocks; an
  open blocker blocks even with every gate passed; zero gates and zero
  blockers allows scoring). Plus gate evaluation (missing check
  defaults unevaluated, reason carried through) and resolver contract
  shape tests.

## Evidence

`python -m unittest tests.test_fit_gates -v`: 10/10 pass.
Full `python scripts/check_release.py`: 0 errors.
