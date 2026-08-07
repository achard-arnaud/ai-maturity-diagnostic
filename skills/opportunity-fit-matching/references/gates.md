# Hard-gate policy

Apply product-specific gates from each snapshot and these generic gates:

1. Demonstrate the problem materially.
2. Establish actionable timing or explicitly select nurture.
3. Identify a sponsor path.
4. Identify a terrain owner.
5. Establish feasible technical and data access.
6. Establish compatible organization, security, and control models.
7. Establish a baseline or reconstruction method.
8. Establish a proof within an acceptable decision horizon.

Use:

- `PASS`: evidence is sufficient;
- `OPEN`: material uncertainty remains;
- `FAIL`: the condition is absent or incompatible.

Consequences:

- Any blocker or critical `FAIL` -> never `PURSUE` or `VALIDATE`; use `DISQUALIFY` or `NURTURE` according to the failure.
- Missing sponsor, timing, or owner -> usually `VALIDATE` or `NURTURE`.
- Any blocker or critical `OPEN` -> never `PURSUE`; `VALIDATE` remains possible to close the uncertainty.

Record claim IDs supporting every gate status. Do not infer `PASS` from a missing field.
