# STOP — Epic 06 / Sprint S02

## Objective

Draft/review/publish/supersede workflow et RBAC. Stop condition:
"publication contrôlée" (controlled publication) -- transition/audit.

## Outputs

- `app/product_workflow.py`:
  - `create_draft_version`/`submit_for_review`: plain state-machine
    moves (`draft -> in_review`), gated by S01's `can_transition_version`.
  - `publish_version`: the one privileged, audited step.
    - RBAC: refuses (`ProductAuthorizationError`) unless
      `actor_role == "product_owner"` -- any other role, including
      `None` (unauthenticated), is rejected outright, per ADR-008's
      authorization model.
    - Requires `status == "in_review"`.
    - Produces exactly one `ProductSnapshot` (via S01's
      `compute_content_hash`) and flips the version to `published`.
    - If a `previous_published_version` is passed (the product's
      currently published version, if any), it is superseded in the
      *same* call -- there is never a window with two versions
      "published" for one product.
    - Appends a `ProductPublished` event to Epic 01's `EventJournal`
      (same audited-decision pattern as Epic 04's `research_review.py`).
- `tests/test_product_workflow.py`: 9 tests -- draft/submit transitions
  and the reject-on-already-in-review case; publish rejected for a
  non-owner role and for an unauthenticated (`None`) role; publish
  rejected from a non-`in_review` status; a successful publish (status,
  `published_snapshot_id`, snapshot content, no supersession on a first
  publish); the audit event carries the actor and snapshot id; and the
  Sprint's core property -- publishing v2 supersedes v1's version while
  v1's own already-published snapshot content is untouched.

## Evidence

`python -m unittest tests.test_product_workflow -v`: 9/9 pass.
Full `python scripts/check_release.py`: 0 errors.
