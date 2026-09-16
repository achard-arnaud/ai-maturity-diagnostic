# Epic 10 — Engagement and Conversation Loop

## Purpose

Séparer réaction externe et activité sortante, puis transformer les réponses en travail qualifié.

## Current state

Follow-up, campaigns et hypothèses d'engagement existent, mais pas d'Inbox/Conversation/EngagementEvent canonique.

## Target state

Réponses, meetings, objections, consentements et non-réponses sont classifiés, reliés aux touchpoints et routés vers next action/opportunity proposal.

## Gaps

DOMAIN conversation/event ; DATA threading ; WORKFLOW classify/resolve ; API ingest ; UX inbox ; SECURITY retention/PII ; QA misclassification.

## Invariants

Activité sortante ≠ engagement ; événement entrant append-only ; faible confiance requiert revue humaine.

## Dependencies

E09.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Conversation/EngagementEvent/Objection schemas | schema/threading | outbound ≠ engagement |
| S02 | Manual/import ingestion et dedup/correlation | duplicate/out-of-order tests | events idempotents |
| S03 | Classification + confidence + human review | gold set/fallback | faible confiance routée |
| S04 | Inbox/follow-up/stop-sequence/next action | workflow/consent tests | réponse agit sur reach |
| S05 | UI Engagement + E2E reply→follow-up/opportunity proposal | end-to-end/audit | boucle fermée |

## Epic acceptance

Une réponse peut arrêter une séquence, créer objection/tâche/meeting ou proposer une opportunité avec provenance.

## Rollback / compatibility

Ingestion désactivable ; événements conservés ; follow-up legacy lisible.

## Deferred work

Sentiment avancé, transcription multi-voix, email sync bidirectionnelle.
