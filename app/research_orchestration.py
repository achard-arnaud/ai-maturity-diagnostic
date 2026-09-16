"""Epic 04 S03: orchestration passes with budget/checkpoints.

A "pass" is an ordered sequence of named steps run against a
ResearchCase. Each step returns a (result, cost) pair. run_pass enforces a
budget (max steps, max cost) and, the moment the budget would be exceeded,
stops and returns a checkpoint that a later call can resume from -- no
step already run is re-run, and no completed step's result is lost. This
is deliberately independent of app.run_manager.RunManager (which owns
run *persistence*/resume-token security); this module owns the
step-sequencing and budget logic that a caller wires into a RunManager
checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

StepFn = Callable[[Mapping[str, Any]], tuple[Any, float]]


class BudgetError(Exception):
    pass


@dataclass(frozen=True)
class PassBudget:
    max_steps: int
    max_cost: float


@dataclass(frozen=True)
class PassStep:
    name: str
    run: StepFn


@dataclass(frozen=True)
class PassResult:
    status: str  # "completed" or "checkpointed"
    results: dict[str, Any]
    cost_spent: float
    checkpoint: dict[str, Any] | None


def run_pass(
    steps: Sequence[PassStep],
    budget: PassBudget,
    *,
    context: Mapping[str, Any] | None = None,
    checkpoint: Mapping[str, Any] | None = None,
) -> PassResult:
    """Run steps until the budget (max_steps or max_cost) is spent, or all
    steps are done, whichever comes first; resumes from checkpoint.

    Budget is checked *after* each step runs (a step's cost is only known
    once it has run), so a call can slightly overspend max_cost on its
    last step, but never runs a step beyond that. checkpoint (as
    previously returned in a PassResult.checkpoint) carries
    {"results": {...}, "cost_spent": float, "next_index": int} -- steps
    before next_index are never re-invoked, even if this function is
    called again with the same steps list (the "cache", here, is simply
    the checkpoint's own results dict).
    """
    if budget.max_steps <= 0:
        raise BudgetError("max_steps must be positive")

    context = context or {}
    if checkpoint:
        results = dict(checkpoint.get("results", {}))
        cost_spent = float(checkpoint.get("cost_spent", 0.0))
        start_index = int(checkpoint.get("next_index", 0))
    else:
        results = {}
        cost_spent = 0.0
        start_index = 0

    steps_run_this_call = 0

    for index in range(start_index, len(steps)):
        step = steps[index]

        result, cost = step.run({**context, "results": dict(results)})
        results[step.name] = result
        cost_spent += cost
        steps_run_this_call += 1

        budget_exhausted = steps_run_this_call >= budget.max_steps or cost_spent >= budget.max_cost
        if budget_exhausted and index + 1 < len(steps):
            return PassResult(
                status="checkpointed",
                results=results,
                cost_spent=cost_spent,
                checkpoint={"results": results, "cost_spent": cost_spent, "next_index": index + 1},
            )

    return PassResult(status="completed", results=results, cost_spent=cost_spent, checkpoint=None)
