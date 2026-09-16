# STOP — Epic 10 / Sprint S03

## Objective

Classification, confidence, human review. Stop condition: "faible
confiance routée" (low confidence routed) -- a classification below
the confidence threshold can never drive a downstream action until a
human reviews it.

## Outputs

- `app/engagement_classification.py`:
  - `CONFIDENCE_THRESHOLD = 0.7`.
  - `classify_objection(...)`: the sole constructor -- always created
    `status="draft"`; refuses an out-of-range confidence.
  - `needs_human_review(objection)`: true only for a low-confidence
    draft.
  - `can_act_on_objection(objection)`: the sole choke point S04 must
    call before acting -- true if `status="reviewed"` or confidence is
    already at/above threshold; a low-confidence draft is always
    blocked (the gold case).
  - `review_objection(objection, reviewed_by, reviewed_at)`: refuses a
    non-draft objection; sets `status="reviewed"`.
  - `build_review_queue(objections)`: deterministic, oldest-first,
    low-confidence-drafts-only queue.
- `tests/test_engagement_classification.py`: 14 tests -- construction
  always draft, out-of-range confidence refused, review-need at/above/
  below threshold and after review, the gold case (low-confidence
  draft blocked from acting), high-confidence draft already actionable,
  low-confidence becomes actionable only after review, review sets
  reviewer/status, double-review refused, queue contents/ordering and
  reviewed objections never reappearing.

## Evidence

`python -m unittest tests.test_engagement_classification -v`: 14/14
pass.
Full `python scripts/check_release.py`: 0 errors.
