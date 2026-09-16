# Epic 01 — Platform Transaction and Execution Foundations

## Purpose

Fiabiliser écritures, événements, jobs, quotas et migrations avant d'élargir le domaine.

## Current state

FastAPI/auth/workspaces/RBAC/audit sont présents. Les modules métier restent file-based ; ownership produit, writes atomiques, journal d'événements, idempotence et rate-limit execution ne sont pas uniformes.

## Target state

Toute mutation passe par une couche transactionnelle workspace-scoped ; tout run est borné, checkpointable, observable et reprenable.

## Gaps

DATA atomicity/versioning ; BACKEND unit of work/jobs ; API idempotency/ETag ; SECURITY scopes ; QA concurrency ; DOCUMENTATION catalog ownership.

## Invariants

Artefacts canoniques conservés ; runtime store non promu en vérité métier ; local-first encore possible.

## Dependencies

E00. Aucun Sprint E01 ne peut être intégré dans `dev` ou `main` tant qu'E00 n'est pas entièrement présent dans les deux branches.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition | Tag |
|---|---|---|---|---|
| S01 | Décider ownership catalogue global/workspace/hybride via ADR | architecture test fixtures | ADR accepté | `epic-01-s01-catalog-ownership` |
| S02 | Introduire ArtifactStore + atomic write + locks + version checks | race/crash/property tests | anciens writers adaptés par façade | `epic-01-s02-artifact-store` |
| S03 | Ajouter EventJournal append-only et correlation IDs | append/idempotence/replay tests | aucun dual truth | `epic-01-s03-event-journal` |
| S04 | Job/run/checkpoint model et resume token | failure/resume/cancel tests | runs déterministes reprenables | `epic-01-s04-run-checkpoints` |
| S05 | Budget envelope, quota, cache key, retry/backoff et degraded mode | simulated 429/timeouts | quota ne corrompt rien | `epic-01-s05-budget-quota` |
| S06 | Migrator framework dry-run/hash/report/rollback | migration rehearsal default workspace | restauration prouvée | `epic-01-s06-migrator` |

## Epic acceptance

Une mutation et un run lourd simulé survivent crash/retry ; audit/event/cost sont corrélés ; migration legacy répétable.

## Rollback / compatibility

Feature flags par writer ; readers legacy N-1 ; EventJournal append-only ignoré par ancien runtime.

## Deferred work

Store SQL métier, queue distribuée, multi-instance.
