# Epic 07 — Explainable Product Fit — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/fit_assessment_v1.schema.yaml` + `app/fit_policy.py`: input version locking (demand_id+demand_version+product_snapshot_id), deterministic hash proving reproducibility. |
| S02 | `app/fit_gates.py`: `can_compute_score` is the sole choke point deciding scorability, proven with an exhaustive gate/blocker matrix. |
| S03 | `app/fit_scoring.py`: explainable coverage/score/gaps/alternatives, every number carries a readable factor breakdown. |
| S04 | `app/fit_lifecycle.py`: RBAC-gated decisions; PURSUE absolutely refused while gates/blockers unresolved; bounded (reason+expiry) overrides only. |
| S05 | `app/fit_store.py`/`app/fit_routes.py`: optimistic-concurrency API with 409/idempotence. |
| S06 | `app/fit_targeting_gate.py`: the gate Epic 08 must call, proven via full E2E chain. |

All 6 shipped in one PR to `dev`: [#53](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/53).

## Gate checklist

- [x] All 6 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00-06 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #53's CI (release-check + e2e-gate both green
      across both duplicate CI runs, one re-run each for the known
      Découvrir-form flake, confirmed identical failure on both runs
      before re-running).
- [x] Audit invariants this Epic owns re-checked: **hard gates avant
      score**: `app.fit_gates.can_compute_score` is exhaustively proven
      (all 24 combinations of 3 gates x 3 blocker counts) to allow
      scoring in exactly the case where every gate passed and zero
      blockers are open. **Score sans gate critique résolue ne produit
      jamais PURSUE**: `app.fit_lifecycle.decide_fit` refuses a PURSUE
      verdict outright when gates/blockers are unresolved, with no
      override parameter able to bypass that specific check (verified by
      two dedicated tests supplying an override reason+expiry anyway and
      confirming rejection). **Inputs versionnés**: every FitAssessment
      locks an exact demand_version + product_snapshot_id pair at
      creation, hashed deterministically, and detectably stale the
      moment either moves.
- [x] Migration/rollback: not applicable -- this Epic introduces a new,
      additive object (FitAssessment) with no legacy artifact to migrate
      from.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 6 sprints, still
      35/35, unchanged.
- [x] Release notes and known limitations published below.

## Known limitations

- `app.fit_gates.evaluate_hard_gates` and `app.fit_scoring`'s
  `dimension_checks` are both caller-supplied -- this Epic builds the
  policy engine and audit trail around gate/coverage evaluation, not the
  evaluation itself (e.g. an automated compliance-questionnaire skill
  that produces those checks). Wiring a real evaluation skill is
  deferred, narrow follow-on work; the contract (`{gate_id, passed,
  reason}` / `{dimension, covered, rationale}`) is stable and ready for
  one.
- No dedicated `product_owner`-vs-`fit_reviewer` role separation is
  enforced beyond the single `fit_reviewer` role check in
  `decide_fit` -- a richer reviewer-assignment/escalation model (e.g.
  requiring a *different* reviewer than the assessment's creator, as
  Epic 04's `research_review` does for `accept_case`) is deferred.
- `app.fit_targeting_gate.can_create_target_plan` is a pure function
  ready for Epic 08 to call; no HTTP route in this Epic exposes it
  directly (S05 only shipped the FitAssessment CRUD/compare routes).
  Epic 08 is expected to call it from its own TargetPlan creation
  code path.
- Carried over from Epic 00-06 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner; `app.product_workflow`'s
  publish route (Epic 06's own known limitation) is still unbuilt, so
  there is no HTTP path yet from a draft ProductVersion to a
  ProductSnapshot a FitAssessment could reference in a live system --
  only direct Python calls or migration currently produce snapshots.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 07. Decision made
autonomously per the operator's instruction to continue the same
iterative sprint-by-sprint procedure through Epics 06-10.
