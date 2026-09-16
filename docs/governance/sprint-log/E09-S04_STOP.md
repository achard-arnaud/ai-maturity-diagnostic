# STOP — Epic 09 / Sprint S04

## Objective

Scheduler local, quotas, time windows. Stop condition: "degraded mode
actif" (degraded mode active) -- a send that would fall outside its
channel's time window or exceed its daily quota must never be
silently dropped or force-sent anyway; the scheduler enters an
explicit degraded mode and defers the attempt.

## Outputs

- `app/reach_scheduler.py`:
  - `DEFAULT_TIME_WINDOWS`: per-channel allowed hour ranges
    (email 7-19, phone 9-18, manual 0-24).
  - `is_within_time_window(channel, hour, windows)`: rejects an
    unconfigured channel rather than defaulting it open.
  - `count_sent_today(channel, sent_events, today)`: quota-counting
    helper, scoped to channel and day.
  - `evaluate_schedule(...)`: the sole choke point -- returns a
    `ScheduleDecision(allowed, degraded, reason)`; `allowed=False`
    always pairs with `degraded=True` and a concrete `reason`
    (`outside_time_window` or `quota_exhausted`) -- never a bare
    failure, and quota room never overrides a closed window.
  - `is_degraded_mode_active(decisions)`: true if any decision in a
    batch is degraded.
- `tests/test_reach_scheduler.py`: 11 tests -- time-window boundaries
  (within/before/after, unknown channel rejected), quota counting
  scoped correctly, schedule allowed within window and under quota,
  degraded on closed window, degraded on exhausted quota, the gold
  case that quota room never forces a send through a closed window,
  and degraded-mode aggregation across a batch of decisions.

## Evidence

`python -m unittest tests.test_reach_scheduler -v`: 11/11 pass.
Full `python scripts/check_release.py`: 0 errors.
