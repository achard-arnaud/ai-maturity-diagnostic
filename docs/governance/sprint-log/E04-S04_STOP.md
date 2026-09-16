# STOP — Epic 04 / Sprint S04

## Objective

Contradiction/falsifier/side-story bounded workflows. Stop condition:
"branches reliées au tronc" (branches connected to the trunk) -- red-team
gold cases.

## Outputs

- `app/research_redteam.py`: per
  `08_EVIDENCE_DECISION_AND_GATES.md`'s "Red-team fonctionnel" (chercher
  une explication alternative, un falsifier, une preuve contradictoire,
  une dépendance non résolue).
  - `open_side_story(parent_claim_id, question, owner, ...)`: a bounded
    investigation branch -- always carries an owner (rejects an
    ownerless open call), always references the trunk claim it branched
    from.
  - `resolve_side_story(side_story, resolution_claim, ...)`: the trunk
    check. A resolution is only accepted if the resolution claim
    reconnects to `parent_claim_id`, either via `supersedes_claim_id` or
    `derived_from_claim_ids`. Resolving with a claim that doesn't
    reference the trunk raises `SideStoryError` -- a side story can never
    close by drifting away from the claim it was opened to investigate.
  - `dismiss_side_story(...)`: the other legal close path, requires a
    non-empty reason (never a silent vanish).
  - `find_contradictions(claims)`: pairs of currently-*active* claims
    that contradict each other via `contradicted_by_claim_ids`;
    superseded/retracted claims' contradictions don't surface.
  - `run_redteam_checklist(claim, evidence_by_id, side_stories)`: per-claim
    checklist -- contradictory evidence (an Evidence record with this
    claim in `contests_claim_ids`), an open side story (unresolved
    alternative-explanation/falsifier chase), unresolved dependency
    (mirrors the open-side-story flag).
- `tests/test_research_redteam.py`: 16 tests, including the gold cases:
  a claim with contesting evidence is flagged; one without is clean; an
  open side story marks an unresolved dependency, a resolved one doesn't;
  a side story on a *different* claim isn't miscounted; resolution
  rejected when the resolution claim doesn't reconnect to the trunk (both
  "no link at all" and "linked to the wrong trunk claim" gold cases);
  dismiss requires a reason; can't resolve/dismiss an already-closed side
  story.

## Evidence

`python -m unittest tests.test_research_redteam -v`: 16/16 pass.
Full `python scripts/check_release.py`: 0 errors.
