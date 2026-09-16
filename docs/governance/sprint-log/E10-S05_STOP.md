# STOP — Epic 10 / Sprint S05

## Objective

UI Engagement + E2E reply->follow-up/opportunity proposal. Stop
condition: "boucle fermée" (closed loop).

As with every prior Epic's "UI" sprint, this means the gate/read-model
layer a UI consumes, not frontend HTML/JS: a reply must flow all the
way from ingestion through classification, follow-up and back onto the
Reach sequence it came from -- proven end to end.

## Outputs

- `app/engagement_opportunity.py`: `propose_opportunity(event)` --
  returns a proposal record only for `meeting_booked`, `None`
  otherwise; never auto-creates or mutates a TargetPlan/FitAssessment,
  only ever proposes.
- `app/engagement_store.py`: workspace-scoped JSONL storage for
  `CanonicalConversationV1`/`CanonicalEngagementEventV1`/
  `CanonicalObjectionV1` -- put/get/list with the same conventions as
  every prior Epic's store (bounded pagination, status filter,
  workspace isolation, deterministic ordering).
- `app/engagement_routes.py`: `GET .../conversations`,
  `GET .../conversations/{id}`, `GET .../conversations/{id}/events`,
  `GET .../conversations/{id}/events/{engagement_event_id}/objections`
  -- workspace-gated, IDOR-safe, bounded pagination (1-100). Wired
  `create_v1_engagement_router(ROOT)` into `app/server.py`.
- `tests/test_engagement_opportunity.py`: 4 tests -- meeting_booked
  proposes, every other kind proposes nothing.
- `tests/test_engagement_store.py`: 6 tests -- put/get, not-found,
  status filter, workspace isolation, event ordering, objection
  scoping.
- `tests/test_engagement_routes.py`: 8 tests -- unauthenticated 401,
  pagination bound, own-workspace success for every route,
  cross-workspace 404 for conversation/events.
- `tests/test_engagement_e2e.py`: the Sprint's own closed-loop E2E, 3
  tests -- a low-confidence reply is ingested (idempotently),
  correlated to its outbound touchpoint, classified as not yet
  actionable, pauses the Reach sequence, appears in the follow-up
  inbox, and becomes actionable only once reviewed;
  a meeting_booked event pauses reach and proposes an opportunity;
  an opt-out cancels reach (cascading to open tasks/steps) and
  re-ingesting/re-applying the same event is fully idempotent.

## Evidence

`python -m unittest tests.test_engagement_opportunity
tests.test_engagement_store tests.test_engagement_routes
tests.test_engagement_e2e -v`: 20/20 pass.
Full `python scripts/check_release.py`: 0 errors.

## Epic 10 status

All 5 sprints closed: S01 Conversation/EngagementEvent/Objection
schemas (outbound never counts as engagement); S02 idempotent
ingestion and touchpoint correlation; S03 classification with
confidence-gated human review (a low-confidence draft can never act);
S04 the inbox and the reply-acts-on-reach next-action loop
(pause/cancel, always idempotent); S05 the API read model and the full
closed-loop E2E from ingestion through to Reach and an opportunity
proposal.
