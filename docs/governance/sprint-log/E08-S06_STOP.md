# STOP — Epic 08 / Sprint S06

## Objective

UI Targets/map/order + E2E Fit→Targets. Stop condition: "reach gated" --
functional/refresh-back E2E.

As with every prior Epic's "UI" sprint, this means the gate/read-model
layer a UI (and Epic 09) consumes, not frontend HTML/JS.

## Outputs

- `app/reach_gate.py`: `can_initiate_reach(plan, stakeholder,
  readiness)` -- the one function Epic 09 (Reach Execution Queue) must
  call before initiating outreach. Blocks unless the plan is `active`,
  the stakeholder is `active`, and `readiness.ready` is true.
  Deliberately takes `readiness` as a parameter re-evaluated by the
  caller each time, never cached -- this is what makes the "refresh-back"
  property hold: a stakeholder ready at plan-activation time can still
  be re-blocked later if their currentness lapses.
- `tests/test_reach_gate.py`: 4 unit tests on the gate itself (inactive
  plan blocks, inactive stakeholder blocks, not-ready stakeholder
  blocks, active+active+ready allows) plus the Sprint's own E2E gate: 3
  full chains --
  `test_e2e_authorized_fit_to_ready_reach` (an authorized Fit ->
  `create_target_plan` -> `assign_stakeholder_role` -> `can_activate_plan`
  -> `activate_plan` -> `can_initiate_reach`, ending allowed);
  `test_e2e_refresh_back_readiness_lapse_reblocks_reach` (identical setup,
  but readiness is re-evaluated as lapsed by the time reach is attempted
  -- reach correctly re-blocks even though the plan is still active,
  proving readiness isn't a one-time check baked in at activation);
  `test_e2e_unauthorized_fit_never_reaches_targeting` (an unauthorized
  fit never even produces a TargetPlan to reach from).

## Evidence

`python -m unittest tests.test_reach_gate -v`: 7/7 pass.
Full `python scripts/check_release.py`: 0 errors.
Legacy network suite (35 tests) re-verified unchanged.

## Epic 08 status

All 6 Sprints closed (S01 TargetPlan/StakeholderRole/Influence schemas
with roles independent of titles; S02 currentness/authority/warm-path
readiness, strict; S03 plan builder/activation with actionable blockers;
S04 deterministic buying-committee graph projection; S05 API with
bounded access; S06 the reach gate and full E2E). Epic acceptance
(1-5 priority contacts can be justified; any insufficient currentness
blocks or routes to validation) is verified: S02's gold cases prove
strict readiness; S03 proves activation requires a ready authority
stakeholder with actionable blockers otherwise; S06 proves reach itself
re-checks readiness fresh, never trusting a stale snapshot.
