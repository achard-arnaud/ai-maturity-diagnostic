# STOP — Epic 08 / Sprint S03

## Objective

Plan builder et validation workflow. Stop condition: "blockers
actionnables" (actionable blockers) -- transition/resolver tests.

## Outputs

- `app/target_plan_workflow.py`:
  - `create_target_plan`: the only TargetPlan constructor -- refuses
    (`TargetPlanWorkflowError`) unless Epic 07's
    `can_create_target_plan` authorizes it ("fit avant ciblage").
  - `build_stakeholder_blockers`: one actionable `StakeholderBlocker`
    (`why_blocked` + concrete `cta`) per not-ready active stakeholder --
    never a bare failure with no next step.
  - `can_activate_plan`: a plan may activate only once at least one
    active, *ready* authority-role (sponsor/champion) stakeholder
    exists; if none, an explicit actionable blocker names exactly that
    ("no ready sponsor or champion... assign and validate one"). Every
    other not-ready active stakeholder still surfaces its own blocker
    regardless of whether it's what's stopping activation -- blockers
    are always complete, never just "the one that matters".
  - `activate_plan`/`mark_plan_stale`: plain transition guards (status
    must be draft to activate, `allowed` must be true; staling requires
    a reason).
- `tests/test_target_plan_workflow.py`: 15 tests -- create rejected for
  an unauthorized/draft/rejected fit, succeeds for an authorized one;
  blockers empty when all ready, one actionable blocker per not-ready
  stakeholder; activation allowed with a ready sponsor or champion
  alone, blocked with an actionable reason when no authority stakeholder
  exists, blocked when the only sponsor isn't ready (both the
  authority-specific and the stakeholder-specific blockers reported),
  and the case where a non-authority stakeholder's own blocker is still
  reported even though activation is otherwise allowed; activate/
  mark_stale transition guards.

## Evidence

`python -m unittest tests.test_target_plan_workflow -v`: 15/15 pass.
Full `python scripts/check_release.py`: 0 errors.
