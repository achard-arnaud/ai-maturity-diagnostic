# STOP — Epic 09 / Sprint S06

## Objective

UI My day / Reach queue / preview / approve + E2E prepare->approve.
Stop condition: "opérable sans fichiers" (operable without files).

As with every prior Epic's "UI" sprint, this means the gate/read-model
layer a UI consumes, not frontend HTML/JS: the whole prepare -> approve
-> send loop, and the queue a user works their day from, must be
drivable entirely through function calls, never by hand-editing JSONL
files.

## Outputs

- `app/reach_execution.py`:
  - `prepare_touchpoint(step, message, touchpoint_id)`: refuses to
    prepare from anything but an `approved` message; the resulting
    touchpoint is always `status="prepared"`, never pre-sent (reuses
    Epic 09 S01's `assert_no_implicit_creation_as_sent`).
  - `send_touchpoint(touchpoint, sent_by, sent_at)`: the distinct,
    later, explicitly-audited send action -- refuses a non-`prepared`
    touchpoint, and refuses (via S01's channel policy) any channel not
    authorized to send, LinkedIn included.
  - `build_my_day(assignee, tasks, sequences_by_id, now)`: the single
    queue a user works from -- their own open tasks, only from
    sequences still `active`/`paused` (never `cancelled`/`completed`),
    ordered through S03's `build_priority_queue`.
- `tests/test_reach_execution.py`: 9 tests -- prepare from an approved
  message never pre-sent, prepare refuses a draft message, send
  succeeds on email, send refuses LinkedIn
  (`ChannelNotAuthorizedError`), send refuses an already-sent
  touchpoint, my-day scoping (own tasks only, active sequences only,
  paused sequences still included, cancelled sequences excluded), and
  the Sprint's own E2E: `test_e2e_gated_reach_through_prepare_approve_send`
  chains Fit -> TargetPlan -> reach gate -> draft (sourced citation) ->
  approve -> prepare -> send end to end;
  `test_e2e_reach_not_gated_blocks_before_any_message_is_drafted` proves
  a lapsed-readiness reach never even reaches drafting.

## Evidence

`python -m unittest tests.test_reach_execution -v`: 9/9 pass.
Full `python scripts/check_release.py`: 0 errors.
