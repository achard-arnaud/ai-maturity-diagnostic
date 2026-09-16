# STOP — Epic 10 / Sprint S01

## Objective

Conversation/EngagementEvent/Objection schemas. Stop condition:
"outbound ≠ engagement" -- sending a Touchpoint (Epic 09) proves
outreach happened, never that the recipient responded.

## Outputs

- `contracts/conversation_v1.schema.yaml`: `CanonicalConversationV1`.
  Groups EngagementEvents for one stakeholder on one TargetPlan;
  `sequence_id` nullable (a conversation may originate outside any
  Reach sequence).
- `contracts/engagement_event_v1.schema.yaml`: `CanonicalEngagementEventV1`.
  `kind` is restricted to inbound-originated signals
  (replied/meeting_booked/opted_out/bounced) -- there is no `sent`
  kind representable here at all; `source_ref` is the dedup key S02's
  idempotent ingestion must key off of.
- `contracts/objection_v1.schema.yaml`: `CanonicalObjectionV1`.
  `status` defaults to `draft`; a low-confidence classification is
  always created draft and routed to human review (S03's own stop
  condition, "faible confiance routée").
- `app/engagement_policy.py`:
  - `ENGAGEMENT_KINDS`/`is_engagement_kind`: the sole vocabulary of
    what counts as engagement.
  - `create_engagement_event(...)`: the sole constructor -- refuses
    (`NotEngagementError`) any `kind` outside `ENGAGEMENT_KINDS`,
    including `sent` itself, so a Touchpoint's send status can never
    be wrapped into this model.
  - `open_conversation`/`close_conversation`: simple lifecycle, refuses
    closing an already-closed conversation.
- `tests/test_engagement_policy.py`: 14 tests -- every engagement kind
  confirmed, `sent` and an unknown kind confirmed not engagement,
  event creation with/without a correlated touchpoint, the gold case
  refusing a `sent`-kind event outright, conversation open/close
  lifecycle including the double-close refusal.

## Evidence

`python -m unittest tests.test_engagement_policy -v`: 14/14 pass.
Full `python scripts/check_release.py`: 0 errors.
