# STOP — Epic 04 / Sprint S03

## Objective

Orchestration passes avec budget/checkpoints. Stop condition: "heavy run
stoppable" -- mocked limits/cache tests.

## Outputs

- `app/research_orchestration.py`: `run_pass(steps, budget, context,
  checkpoint)`. A pass is an ordered list of named `PassStep`s; each
  step's `run` returns `(result, cost)`. Budget (`max_steps`/`max_cost`)
  is checked *after* a step runs (a step's real cost is only known once
  it has run), so a call may spend slightly over `max_cost` on the step
  that crosses it, but never starts a step once the prior one already
  spent the budget. The moment budget is spent with steps remaining, the
  call returns `status="checkpointed"` with a `checkpoint` carrying
  `results`, `cost_spent`, and `next_index` -- a later call passing that
  checkpoint back in resumes from exactly `next_index` and never re-invokes
  an earlier step (the "cache" is simply the checkpoint's own
  `results` dict, carried forward). This is deliberately independent of
  Epic 01's `RunManager` (which owns run *persistence* and resume-token
  security) -- a caller wires this module's checkpoint into a
  `RunManager.checkpoint()` call; this module only owns step sequencing
  and budget.
- `tests/test_research_orchestration.py`: 7 tests using injected mock
  steps that record call order and a fixed cost -- all-steps-within-budget
  completes; `max_steps` checkpoints a heavy run at the right step;
  `max_cost` checkpoints once spent; resuming from a checkpoint never
  re-runs a completed step and eventually reaches `completed`; completed
  results survive across checkpoints; an invalid (`<=0`) budget is
  rejected; the accumulated `results` a step sees in its context is
  a snapshot at call time (mutating it doesn't leak into stored results).

## Evidence

`python -m unittest tests.test_research_orchestration -v`: 7/7 pass.
Full `python scripts/check_release.py`: 0 errors.
