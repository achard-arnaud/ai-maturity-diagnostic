# Epic 10 — Engagement and Conversation Loop — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/conversation_v1.schema.yaml`/`engagement_event_v1.schema.yaml`/`objection_v1.schema.yaml` + `app/engagement_policy.py`: an EngagementEvent can only ever be constructed from an inbound-originated kind -- a Touchpoint's send is never itself engagement. |
| S02 | `app/engagement_ingestion.py`: idempotent ingestion keyed on `source_ref`, best-effort touchpoint correlation. |
| S03 | `app/engagement_classification.py`: an Objection always starts `draft`; `can_act_on_objection` blocks a low-confidence draft outright until human review. |
| S04 | `app/engagement_inbox.py`: `apply_engagement_to_sequence` -- a reply/meeting_booked/bounce pauses, an opt-out cancels the Reach sequence (Epic 09), always idempotently; deterministic follow-up inbox. |
| S05 | `app/engagement_opportunity.py`/`app/engagement_store.py`/`app/engagement_routes.py`: opportunity proposal from meeting_booked, bounded-access API, and the closed-loop E2E. |

All 5 shipped in one PR to `dev`: [#62](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/62).

## Gate checklist

- [x] All 5 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00-09 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #62's CI (release-check + e2e-gate both
      green across both duplicate CI runs, no re-run needed).
- [x] Audit invariants this Epic owns re-checked: **outbound ≠
      engagement**: `app.engagement_policy.create_engagement_event` is
      the sole constructor and refuses any `kind` outside the
      inbound-originated vocabulary (replied/meeting_booked/opted_out/
      bounced) -- a Touchpoint's own `sent` status (Epic 09) can never
      be wrapped into this model, proven by a dedicated gold-case test.
      **events idempotents**: `app.engagement_ingestion.ingest_engagement_event`/
      `ingest_batch` dedup on `source_ref`, proven by a full-file
      re-import gold case creating nothing new. **faible confiance
      routée**: `app.engagement_classification.can_act_on_objection`
      is the sole choke point downstream code must call, and a
      low-confidence draft is always blocked, proven by a dedicated
      gold-case test; it only becomes actionable once
      `review_objection` marks it reviewed. **réponse agit sur
      reach**: `app.engagement_inbox.apply_engagement_to_sequence` is
      the sole function letting an inbound event act on Reach, proven
      end to end (a reply pauses an active sequence; an opt-out
      cancels one, cascading to its open tasks/steps) and proven
      idempotent under re-application against an already-stopped
      sequence.
- [x] Migration/rollback: not applicable -- this Epic introduces new,
      additive objects (Conversation/EngagementEvent/Objection) with
      no legacy artifact to migrate from.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 5 sprints, still
      35/35, unchanged.
- [x] Release notes and known limitations published below.

## Known limitations

- `app.engagement_store`/`app.engagement_routes` do not yet expose a
  write path (create/patch) over HTTP -- S05 shipped read routes only
  (list/get/events/objections). Ingesting events, classifying
  objections and applying them to a Reach sequence is currently
  Python-API-only (via `app.engagement_ingestion`/
  `app.engagement_classification`/`app.engagement_inbox` directly); an
  HTTP write route is deferred, narrow follow-on work, same pattern as
  every prior Epic's still-unbuilt write routes (Epic 06's
  product-publish, Epic 08's target-plan write, Epic 09's reach write).
- `app.engagement_classification`'s confidence score is a caller-
  supplied input, not itself computed by a classifier model in this
  Epic -- the actual NLP/heuristic classification step that produces a
  `(category, confidence)` pair from raw reply text is deferred, narrow
  follow-on work; this Epic's own scope is the policy gate around that
  score (routing, review, actionability), not the classifier itself.
- `app.engagement_opportunity.propose_opportunity` only ever returns a
  proposal record -- there is no TargetPlan/FitAssessment mutation, nor
  a store for the proposal itself, wired up yet; accepting a proposal
  into an actual next stage is deferred, narrow follow-on work.
- Carried over from Epic 00-09 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner; Epic 06's product-publish
  route, Epic 07's `dimension_checks`/`gate_checks` evaluation-skill
  wiring, Epic 08's target-plan write route, and Epic 09's reach write
  route all remain unbuilt, as documented in their own acceptance
  records.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 10. Decision made
autonomously per the operator's instruction to continue the same
iterative sprint-by-sprint procedure through Epics 06-10. This closes
the last of the five originally-supplied Epic specifications
(06-10).
