# STOP — Epic 10 / Sprint S04

## Objective

Inbox / follow-up / stop-sequence / next action. Stop condition:
"réponse agit sur reach" (a reply acts on reach) -- an inbound
EngagementEvent must actually pause or cancel the Reach sequence it
correlates to, not just get logged as a passive record.

## Outputs

- `app/engagement_inbox.py`:
  - `next_action_for_kind(kind)`: the vocabulary mapping --
    `replied`/`meeting_booked`/`bounced` -> `pause_sequence`,
    `opted_out` -> `cancel_sequence`; refuses an unmapped kind.
  - `apply_engagement_to_sequence(event, sequence, tasks, steps)`: the
    sole function letting an inbound event act on Reach (Epic 09's
    `pause_sequence`/`cancel_sequence`). Idempotent -- re-applying
    against an already-paused/cancelled sequence is a no-op
    (`"no_op"`/`"already_cancelled"`), never an error.
  - `build_engagement_inbox(conversations, events, objections)`:
    deterministic follow-up queue -- open conversations with at least
    one low-confidence (still-`draft`) objection on one of their
    events, oldest conversation first.
- `tests/test_engagement_inbox.py`: 14 tests -- the kind->action
  vocabulary, the gold case (a reply actually pauses an active
  sequence), opt-out cancels and cascades to open tasks/steps,
  idempotent re-application against already-stopped sequences,
  meeting_booked also pauses, inbox inclusion/exclusion by pending
  objection, high-confidence exclusion, closed-conversation exclusion,
  and oldest-first ordering.

## Evidence

`python -m unittest tests.test_engagement_inbox -v`: 14/14 pass.
Full `python scripts/check_release.py`: 0 errors.
