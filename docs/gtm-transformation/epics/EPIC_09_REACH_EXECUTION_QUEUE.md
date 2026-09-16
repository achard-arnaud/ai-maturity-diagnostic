# Epic 09 — Reach Execution Queue

## Purpose

Transformer Reach/Campaigns en file d'exécution sûre, idempotente et supervisée.

## Current state

Preview/prepare reach, strategy artifact, campaigns draft/sent, messages et kanban existent ; modèle Sequence/Touchpoint/canal/consentement reste incomplet.

## Target state

Séquences approuvées, tâches et touchpoints planifiés ; génération personnalisée fondée sur preuves ; envoi séparé, audité et canal-policy compliant.

## Gaps

DOMAIN sequence/touchpoint ; WORKFLOW approvals/cadence ; BACKEND scheduler/idempotence ; API commands ; UX daily queue ; SECURITY consent/channel ; QA duplicate sends.

## Invariants

Préparation et envoi sont séparés ; aucun envoi sans cible ready, consent/policy et approval ; idempotence obligatoire.

## Dependencies

E08.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Sequence/Step/Task/Touchpoint schemas et policies canal | schema/policy tests | aucun send implicite |
| S02 | Message evidence binding, templates et approval | citation/leakage evals | claims sourcés |
| S03 | Execution queue/priorities/SLA/pause/cancel | state/idempotence | retry sans doublon |
| S04 | Scheduler local + quotas + time windows | clock/429/recovery tests | degraded mode actif |
| S05 | API Reach/Sequences/Tasks/Touchpoints | auth/ETag/commands | stable v1 |
| S06 | UI My day/Reach queue/preview/approve | E2E prepare→approve | opérable sans fichiers |
| S07 | Adaptateur premier canal autorisé ou manual-send export | contract/compensation/audit | LinkedIn write toujours interdit sans ADR |

## Epic acceptance

Une séquence peut être préparée, approuvée, exécutée manuellement ou via canal autorisé, pausée et reprise sans double envoi.

## Rollback / compatibility

Kill switch global/par canal ; campagnes legacy importées comme drafts.

## Deferred work

Autonomous outreach, multichannel optimization.
