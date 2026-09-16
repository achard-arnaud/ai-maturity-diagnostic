# STOP — Epic 05 / Sprint S02

## Objective

Lifecycle et qualification checklist/gates. Stop condition: "transitions
explicables" (explicable transitions) -- state/property tests.

## Outputs

- `app/demand_lifecycle.py`:
  - Transition table: `observed -> {qualifying, rejected}`,
    `qualifying -> {qualified, rejected}`, `qualified -> stale`,
    `rejected/stale -> reopened`, `reopened -> {qualifying, rejected}`.
  - `run_qualification_checklist(demand)`: `problem` must be known
    (load-bearing dimension), and at least one buying-signal dimension
    (`sponsor`/`budget`/`timing`/`urgency`/`initiative`) must be known --
    otherwise there is nothing to qualify against. Returns a
    `QualificationChecklist` naming every missing condition, never a bare
    pass/fail.
  - `qualify_demand`: the *only* function in this module that can produce
    `status="qualified"` -- always runs the checklist first;
    `transition_to_qualifying` only ever reaches `"qualifying"`, so there
    is no path to bypass a failing checklist.
  - `reject_demand`/`mark_stale`/`reopen_demand`: each requires a
    non-empty reason.
  - Every `DemandLifecycleError` this module raises carries a specific,
    non-empty `.reason` -- an invalid transition names the exact
    from/to/demand_id, a failed checklist names every missing dimension,
    a missing reason names which action needed one. No bare/opaque
    failure exists in this module.
- `tests/test_demand_lifecycle.py`: 19 tests -- transition table
  (allowed and disallowed pairs), qualification checklist (passes with
  problem+signal known, fails and names the reason for unknown problem
  or no buying signal), qualify_demand (requires `qualifying` status,
  succeeds when checklist passes, fails and names the missing dimension,
  and a property test proving the failing-checklist case can never be
  bypassed by any other call in the module), reject/mark_stale/reopen
  (each requires a reason), and a property test asserting every raised
  `DemandLifecycleError` carries a specific (non-trivial-length) reason.

## Evidence

`python -m unittest tests.test_demand_lifecycle -v`: 19/19 pass.
Full `python scripts/check_release.py`: 0 errors.
