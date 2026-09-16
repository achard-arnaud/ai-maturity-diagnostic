# STOP — Epic 07 / Sprint S01

## Objective

FitAssessment schema + input version locking. Stop condition: "mêmes
inputs=même base" (same inputs => same base) -- reproducibility tests.

## Outputs

- `contracts/fit_assessment_v1.schema.yaml`: `CanonicalFitAssessmentV1`.
  `input_lock` carries `demand_id`, `demand_version` (Epic 05's
  optimistic-concurrency version counter at lock time -- not just the
  demand_id, so a FitAssessment's inputs are exact even though the
  Demand may keep being edited afterward), `product_snapshot_id` (Epic
  06's immutable snapshot), and `input_hash`. `status`
  (draft/in_review/decided/stale), `gates`/`coverage`/`gaps`/
  `alternatives`/`counter_evidence`/`score`/`verdict` are all populated
  by later sprints (S02-S04); this Sprint only defines their shape.
  Structurally carries no targeting/person field -- Fit precedes
  targeting (Epic 08), never the reverse.
- `app/fit_policy.py`:
  - `compute_input_lock_hash(demand_id, demand_version,
    product_snapshot_id)`: deterministic sha256 over the three locked
    inputs.
  - `create_input_lock`/`InputLock`: the lock record itself.
  - `is_input_lock_current(lock, current_demand_version,
    current_snapshot_id)`: true only if nothing has moved since the lock
    was taken -- a demand edit or a new product snapshot publish both
    make a lock stale, detectably, never silently re-based.
- `tests/test_fit_policy.py`: 8 tests -- hash determinism (same inputs
  same hash; each of the three inputs independently changes the hash
  when varied) and the Sprint's own reproducibility property (two
  assessments locked to the identical demand_id/demand_version/
  product_snapshot_id triple are provably built on the same base; a lock
  detects staleness after either a demand edit or a new snapshot
  publish).

## Evidence

`python -m unittest tests.test_fit_policy -v`: 8/8 pass.
Full `python scripts/check_release.py`: 0 errors.
