# STOP — Epic 09 / Sprint S03

## Objective

Execution queue: priorities, SLA (overdue), pause/cancel. Stop
condition: "retry sans doublon" (retry without duplication) -- a retry
attempt must never create a second in-flight attempt for the same
step, and pausing/cancelling a sequence must cascade deterministically
to still-open work without rewriting anything already terminal.

## Outputs

- `app/reach_queue.py`:
  - `build_priority_queue(tasks, now)`: deterministic ordering
    (overdue first, then priority desc, then due_at asc, then task_id
    asc as a tiebreak) -- stable regardless of input order; terminal
    tasks (`done`/`skipped`) excluded.
  - `retry_step(step, attempts)`: the sole choke point for retries --
    refuses (`DuplicateRetryError`) when an attempt for the same
    `step_id` is already `prepared` or `sent`; refuses
    (`InvalidTransitionError`) on a step already in a terminal status;
    otherwise returns a new attempt with an incrementing
    `attempt_number`.
  - `pause_sequence`/`resume_sequence`: only active↔paused, refused
    otherwise.
  - `cancel_sequence(sequence, tasks, steps)`: cascades open tasks to
    `skipped` and open steps to `cancelled`; anything already terminal
    (done/skipped/sent/cancelled) is left untouched -- cancellation
    never rewrites history. Allowed from `draft` or an active status,
    refused if already cancelled.
  - `is_task_overdue(task, now)`: SLA helper, always false for
    terminal tasks.
- `tests/test_reach_queue.py`: 20 tests -- priority queue ordering
  (overdue-first, priority tiebreak, terminal exclusion, stable
  ordering across differently-ordered input), retry duplication gold
  cases (refused while prepared/sent in-flight, allowed after a failed
  attempt, refused on a terminal step, scoped correctly by step_id),
  pause/resume valid and invalid transitions, cancel cascade and
  untouched-terminal-records gold cases, overdue SLA checks.

## Evidence

`python -m unittest tests.test_reach_queue -v`: 20/20 pass.
Full `python scripts/check_release.py`: 0 errors.
