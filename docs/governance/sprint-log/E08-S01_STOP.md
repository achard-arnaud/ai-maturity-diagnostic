# STOP — Epic 08 / Sprint S01

## Objective

TargetPlan/StakeholderRole/Influence schemas. Stop condition: "rôles ≠
titres" (roles ≠ titles) -- schema/cardinality.

## Outputs

- `contracts/target_plan_v1.schema.yaml`: `CanonicalTargetPlanV1`.
  Locks a `fit_assessment_id` (per this Epic's "fit avant ciblage"
  invariant, a plan can only exist for a fit that already authorized
  targeting -- enforced at creation time, S03). Carries no stakeholder
  data inline; each stakeholder is a separate record.
- `contracts/stakeholder_role_v1.schema.yaml`: `CanonicalStakeholderRoleV1`.
  `role` (sponsor/champion/user/prescripteur/technique/procurement/
  blocker) and `title` (the person's real job title, purely
  informational) are two independent fields -- the schema's own
  `x-rules` and `app.target_plan_policy`'s docstring both state that no
  function in this Epic reads `title` to infer or validate `role`.
- `contracts/influence_v1.schema.yaml`: `CanonicalInfluenceV1`. `warm_path`
  (nullable, explicit unknown when absent), `confidence`, `evidence_ids`.
- `app/target_plan_policy.py`:
  - `assign_stakeholder_role`: builds a StakeholderRole record from
    `role` and `title` as fully independent parameters -- no combination
    is rejected as "inconsistent" (that's the "rôles ≠ titres" invariant
    made concrete: a CEO can be assigned `role="user"`, a junior analyst
    can be `role="sponsor"`, without either being blocked).
  - `validate_role_cardinality`: `sponsor`/`champion` are singular per
    plan among *active* stakeholders (a second active one is rejected);
    every other role is unbounded; a superseded stakeholder never counts
    against cardinality.
  - `supersede_stakeholder_role`: flips status only.
- `tests/test_target_plan_policy.py`: 13 tests -- unknown role rejected,
  valid assignment; the Sprint's own "roles ≠ titles" cases (CEO title
  with a non-sponsor role accepted, junior title with sponsor role
  accepted, two stakeholders sharing the same title assigned different
  roles); cardinality (first sponsor/champion allowed, a second active
  one of either rejected, a superseded one doesn't block a new one,
  multiple active technique/blocker stakeholders allowed, sponsor
  cardinality doesn't block champion); supersede flips status.

## Evidence

`python -m unittest tests.test_target_plan_policy -v`: 13/13 pass.
Full `python scripts/check_release.py`: 0 errors.
