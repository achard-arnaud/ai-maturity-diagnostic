# STOP — Epic 09 / Sprint S01

## Objective

Sequence/Step/Task/Touchpoint schemas et policies canal. Stop condition:
"aucun send implicite" (no implicit send) -- schema/policy tests.

## Outputs

- `contracts/sequence_v1.schema.yaml`: `CanonicalSequenceV1`. Orders
  Steps only, never sends anything itself. Per this Epic's own invariant
  ("préparation et envoi sont séparés"), preparation (`draft`/`approved`)
  and execution (`active`/`paused`/`completed`) statuses are distinct.
- `contracts/step_v1.schema.yaml`: `CanonicalStepV1`. `channel`
  (email/linkedin/phone/manual), `status`
  (pending/scheduled/sent/skipped/cancelled) -- schema notes a step is
  always created `pending`.
- `contracts/task_v1.schema.yaml`: `CanonicalTaskV1`. The human-facing
  unit of work; never itself a send.
- `contracts/touchpoint_v1.schema.yaml`: `CanonicalTouchpointV1`. Always
  created `status=prepared`, `sent_at=null`; moving to `sent` always
  requires a later, separately-audited action with a real `sent_by`.
- `app/reach_channel_policy.py`:
  - `assert_no_implicit_creation_as_sent(record, record_kind)`: rejects
    creating a step/touchpoint already marked `sent` -- creation must
    always start unsent.
  - `can_send_via_channel`/`assert_channel_authorized_to_send`:
    email/phone/manual are send-allowed; `linkedin` is categorically
    not -- LinkedIn write access always requires a dedicated ADR (this
    Epic's own deferred-work line), enforced here, not just documented.
- `tests/test_reach_channel_policy.py`: 11 tests -- step/touchpoint
  creation allowed at every legitimate non-sent status, rejected when
  created already `sent`; unknown record_kind rejected; every
  send-allowed channel confirmed, LinkedIn confirmed forbidden (both the
  boolean check and the raising assertion), unknown channel rejected.

## Evidence

`python -m unittest tests.test_reach_channel_policy -v`: 11/11 pass.
Full `python scripts/check_release.py`: 0 errors.
