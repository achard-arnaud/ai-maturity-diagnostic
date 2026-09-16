# STOP — Epic 03 / Sprint S04

## Objective

Screening score explicable + hard exclusions. Stop condition: "score
borné à recherche" (score bounded to research, never fit).

## Outputs

- `app/signal_screening.py`: `compute_research_priority_score(signal)`.
  - Hard exclusions run first and are absolute: `dismissed`/`expired`
    status, or a signal past its freshness window, always scores 0 with
    a stated reason — never overridden by how well-evidenced the signal
    looks (mirrors the qualification module's hard-gate-before-score
    rule).
  - Otherwise, an explicable weighted score (`evidence_grade` 0.6,
    `source_kind` 0.4), each factor carrying `name`/`weight`/
    `contribution`, exposed via `.explanation()`.
  - Structurally guarded to never resemble a fit/offer score: no
    product/catalog knowledge is used, and a test walks the result
    type's own fields plus every factor name for `fit`/`offer`/
    `recommend`/`product`/`catalog`.
- `tests/test_signal_screening.py`: 10 tests — hard exclusion absoluteness
  (including a "best possible" signal that's still excluded), factor
  breakdown correctness, ordering sanity (higher evidence grade / manual
  source score higher, all else equal), and the "never a fit score"
  structural gold-set guard.

## Evidence

`python -m unittest tests.test_signal_screening -v`: 10/10 pass.
