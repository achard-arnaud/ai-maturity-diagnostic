# STOP — Epic 07 / Sprint S03

## Objective

Explainable scoring/coverage/gaps/alternatives. Stop condition:
"justification lisible" (readable justification) -- gold cases/
calibration.

## Outputs

- `app/fit_scoring.py`: never decides *how* a dimension is covered
  (domain-specific, supplied by the caller as `dimension_checks`) --
  only aggregates, weighs, and explains.
  - `compute_coverage`: covered/gaps/coverage_ratio from caller-supplied
    per-dimension checks.
  - `compute_explainable_score`: a weighted sum where every factor
    reports its own name/weight/contribution (mirrors Epic 03's
    `signal_screening` explicability pattern) -- never a bare float with
    no breakdown; a human-readable `explanation` string names each
    dimension as covered/gap alongside its weight.
  - `validate_alternatives`/`validate_counter_evidence`: reject a vague
    or empty placeholder entry outright -- every alternative needs a
    real description and rationale, every counter-evidence entry a real
    statement.
- `tests/test_fit_scoring.py`: 14 tests -- coverage (empty/full/partial
  with gaps correctly listed); score factor-per-dimension, the Sprint's
  own readability gold case (the explanation string names each dimension
  and its covered/gap status legibly), uncovered contributes zero,
  covered contributes its weight, a calibration gold case (adding a
  covered dimension never lowers the total score), and the empty-input
  fallback explanation; alternatives/counter-evidence validation
  (valid passes, missing description/rationale/statement rejected).

## Evidence

`python -m unittest tests.test_fit_scoring -v`: 14/14 pass.
Full `python scripts/check_release.py`: 0 errors.
