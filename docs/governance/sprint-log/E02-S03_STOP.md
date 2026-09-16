# STOP — Epic 02 / Sprint S03

## Objective

Identity resolution/dedup proposals sans auto-merge. Stop condition:
"merge humain audité" (human-audited merge), reversible.

## Outputs

- `app/identity_resolution.py`: pure functions, no disk I/O.
  - `propose_merge(survivor, candidate, evidence, confidence)` — creates a
    `pending_review` `MergeProposal`. Rejects self-merge, out-of-range
    confidence, and empty evidence.
  - `decide_merge(proposal, decision, reviewed_by, rationale)` — the only
    way to move a proposal to `accepted`/`rejected`; requires a named
    reviewer (no anonymous merges).
  - `apply_accepted_merge(survivor, candidate, decision)` — only accepts
    an `accepted` decision; marks the candidate `status: merged` +
    `merged_into_entity_id`, absorbs its `legacy_ids` into the survivor.
    Never deletes, never mutates inputs in place.
  - `reverse_merge(survivor, merged_candidate, original_candidate_legacy_ids)`
    — undoes a merge completely: candidate back to `active`, survivor's
    `legacy_ids` shrink back.
- `tests/test_identity_resolution.py`: 11 tests, including two explicit
  "gold pairs" from the corpus's own example scenario — a true duplicate
  (same person, different employer) that should merge, and a known
  non-duplicate (same name, unrelated people) that must be rejected, not
  merged, even though a proposal can legitimately be raised for it.

## Evidence

`python -m unittest tests.test_identity_resolution -v`: 11/11 pass. First
run caught a real bug: `apply_accepted_merge` checked
`decision.candidate_entity_id`/`decision.survivor_entity_id`, fields
`MergeDecision` didn't carry yet — fixed by deriving them from the
proposal at `decide_merge` time, re-ran, green.

## Remaining

This module is not wired to `app/network_index.find_potential_duplicates`
(detection) or to any storage yet — S04's read models and S06's
migration/backfill are where entity_id assignment and real merge proposals
over actual data happen. This Sprint only proves the merge/reverse
mechanics are sound and human-gated.
