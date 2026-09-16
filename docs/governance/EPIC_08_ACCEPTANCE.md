# Epic 08 — Buying Committee and Target Plans — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/target_plan_v1.schema.yaml`/`stakeholder_role_v1.schema.yaml`/`influence_v1.schema.yaml` + `app/target_plan_policy.py`: role independent of title, singular sponsor/champion cardinality. |
| S02 | `app/target_currentness.py`: strict readiness (stale/conflict blocks; authority roles need more than a title). |
| S03 | `app/target_plan_workflow.py`: creation gated on Fit; activation requires a ready authority stakeholder, actionable blockers otherwise. |
| S04 | `app/buying_committee_view.py`: deterministic, pure graph projection. |
| S05 | `app/target_plan_store.py`/`app/target_plan_routes.py`: bounded-access API. |
| S06 | `app/reach_gate.py`: the gate Epic 09 must call, proven via full E2E with refresh-back re-block. |

All 6 shipped in one PR to `dev`: [#56](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/56).

## Gate checklist

- [x] All 6 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00-07 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #56's CI (release-check + e2e-gate both green
      across both duplicate CI runs, one re-run for the known
      Découvrir-form flake, confirmed identical failure before
      re-running).
- [x] Audit invariants this Epic owns re-checked: **fit avant ciblage**:
      `app.target_plan_workflow.create_target_plan` is the sole
      constructor and refuses outright unless Epic 07's
      `can_create_target_plan` authorizes it. **Un titre de poste ne
      prouve ni autorité ni rôle**: `app.target_plan_policy.
      assign_stakeholder_role` accepts role and title as fully
      independent inputs (proven by tests assigning a CEO title to a
      non-authority role and a junior title to an authority role, both
      accepted without contradiction); `app.target_currentness.
      evaluate_readiness` additionally requires non-weak influence
      confidence for authority roles, never accepting a title alone as
      proof. **Currentness insuffisante bloque Reach**: proven at every
      layer -- readiness itself blocks on stale/conflicted currentness
      regardless of role, plan activation requires a ready authority
      stakeholder, and `app.reach_gate.can_initiate_reach`
      re-evaluates readiness fresh at reach time (the refresh-back E2E
      test proves a stakeholder ready at activation can still be
      re-blocked later).
- [x] Migration/rollback: not applicable -- this Epic introduces new,
      additive objects (TargetPlan/StakeholderRole/Influence) with no
      legacy artifact to migrate from.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 6 sprints, still
      35/35, unchanged.
- [x] Release notes and known limitations published below.

## Known limitations

- `app.buying_committee_view.build_committee_graph`'s edges are
  currently limited to warm-path connections; a richer graph model
  (e.g. reporting-line edges between stakeholders, if that data becomes
  available from Epic 02's network graph) is deferred, narrow follow-on
  work -- the projection contract (`{"nodes": [...], "edges": [...]}`)
  is stable and can grow additional edge types without breaking
  existing consumers.
- `app.target_plan_store`/`app.target_plan_routes` do not yet expose a
  write path (create/patch) over HTTP -- S05 shipped read routes only
  (list/get/stakeholders/committee-graph). Writing plans and assigning
  stakeholders is currently Python-API-only (via
  `app.target_plan_workflow`/`app.target_plan_policy` directly); an HTTP
  write route is deferred, narrow follow-on work, same pattern as Epic
  06's still-unbuilt product-publish route.
- No dedicated privacy/PII redaction is applied to stakeholder records
  beyond workspace-scoped access control -- `person_entity_id` and
  `title` are returned as stored to any authenticated member of the
  owning workspace. A finer-grained per-role visibility model (e.g.
  redacting `title` for some viewer roles) is deferred if a future
  Sprint's requirements call for it.
- Carried over from Epic 00-07 (not created by this Epic):
  `feat/prospection-principes-todo` still unmerged; GitLab's `e2e-gate`
  mirror unverified against a live runner; Epic 06's product-publish
  route and Epic 07's `dimension_checks`/`gate_checks` evaluation-skill
  wiring both remain unbuilt, as documented in their own acceptance
  records.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 08. Decision made
autonomously per the operator's instruction to continue the same
iterative sprint-by-sprint procedure through Epics 06-10.
