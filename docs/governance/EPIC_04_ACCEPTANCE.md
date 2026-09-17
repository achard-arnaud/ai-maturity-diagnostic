# Epic 04 — Product-Blind Research and Company 360 — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/research_case_v1.schema.yaml`/`claim_v1.schema.yaml`/`evidence_v1.schema.yaml` + `app/research_policy.py`: case transition state machine, claim lineage validation per claim_type, gate-1 completeness. |
| S02 | `app/research_queue.py` + `app/research_case_store.py`: idempotent ownership, SLA, blockers, resume gated on zero open blockers. |
| S03 | `app/research_orchestration.py`: budgeted, checkpointable orchestration passes. |
| S04 | `app/research_redteam.py`: bounded side-story workflows reconnecting to the trunk claim; contradiction detection; red-team checklist. |
| S05 | `app/company360_view.py` + `app/claim_store.py`/`app/evidence_store.py` + `app/research_routes.py`: Company 360 read model, structurally product-blind. |
| S06 | `app/research_review.py`: explicit, audited accept/reopen/mark-stale lifecycle with separation of duties. |
| S07 | `app/research_evals.py`: contamination/coverage/factuality gold-set eval suite. |

All 7 shipped in one PR to `dev`: [#44](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/44).

## Gate checklist

- [x] All 7 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00/02/03 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #44's CI (release-check + e2e-gate both green
      across both duplicate CI runs, first attempt, no flake this time).
- [x] Audit invariants this Epic owns re-checked: **product-blind
      research** enforced at two independent layers -- structurally (the
      Company 360 view's own field/key shape, `app/company360_view.py`'s
      `_FORBIDDEN_FIELD_TOKENS` guard) and at the content level (S07's
      `check_contamination` scan over claim statement text, with
      zero-tolerance threshold in the release eval). **Claims typed and
      sourced**: every claim's `claim_type` (fact/inference/hypothesis)
      has its own lineage requirement enforced by
      `validate_claim_lineage`, never bypassable. **No inference promoted
      to fact automatically**: `is_claim_type_promotion` is a pure
      predicate for tests/callers to assert against; no code path in this
      Epic performs an automatic type upgrade. **Heavy runs
      checkpointable**: `run_pass` proven under mocked budget limits to
      checkpoint and resume without re-running or losing completed steps.
- [x] Migration/rollback: not applicable -- this Epic introduces new,
      additive objects (ResearchCase/Claim/Evidence) with no legacy
      artifact to migrate from; all three stores are append/upsert-only
      via `ArtifactStore`, same as Epic 02/03's read models.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 7 sprints, still
      35/35, unchanged -- no file under `app/network_writer.py`/
      `network_index.py`/`account_view.py`/`duplicate_dismissals.py` or
      `skills/network-account-screening/` was touched.
  - [x] Release notes and known limitations published below.

## Known limitations

- No premium/automated research connector exists behind
  `app/signal_ingestion.ingest_public`-equivalent for research passes --
  `run_pass`'s `PassStep`s are caller-supplied; wiring a real
  corporate/org/hiring/newsflow skill into a step is deliberately deferred
  (this Epic's own "recherche automatisée premium" deferred-work line).
- `app/research_orchestration.run_pass` is independent of Epic 01's
  `RunManager` by design (this Sprint owns step sequencing/budget, not
  persistence/resume-token security) -- wiring the two together into a
  durable, resumable HTTP-triggerable run is follow-on work for whichever
  Epic/Sprint needs research passes exposed over the API.
  `SignalList`/`SavedSearch`/`Watchlist` from Epic 03 similarly have no
  storage layer yet; both remain pure/tested logic layers awaiting their
  UI-facing Sprint.
- `app/research_review.accept_case`'s separation-of-duties check
  (reviewer != owner) is a simple identity comparison, not yet backed by
  a role/permission system -- Epic 00's RBAC primitives exist
  (`require_workspace_access`) but no `reviewer` role is modeled yet; any
  authenticated workspace member can currently act as reviewer as long as
  they are not the case's own owner.
- Carried over from Epic 00/02/03 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner; Epic 03's `ResearchQueued`
  event now has its intended consumer (this Epic's `ResearchCase`), but no
  automated process yet turns a `ResearchQueued` event into an actual
  `ResearchCase` record -- that wiring (event -> case creation) is
  follow-on work, not yet built.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 04. Decision made
autonomously per the operator's instruction to process Epics 03, 04, 05
iteratively with the same procedure, merging progressively to `dev` and
releasing to `main` at each Epic's acceptance.
