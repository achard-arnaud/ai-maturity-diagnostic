# Epic 04 — Product-Blind Research and Company 360

## Purpose

Industrialiser la recherche compte sans contamination par l'offre.

## Current state

Skills corporate/org/hiring/newsflow, evidence ledger, études et Account 360 existent mais orchestration, queue, claims et complétude sont dispersés.

## Target state

ResearchCase est pilotable ; Company 360 sépare sources, claims, faits/inférences/hypothèses, contradictions, inconnues et Demands candidates.

## Gaps

DOMAIN ResearchCase/Claim ; DATA evidence ledger canonique ; WORKFLOW passes/checkpoints ; BACKEND budgeted orchestration ; UX research queue ; QA contamination/evals.

## Invariants

Recherche product-blind ; claims typés et sourcés ; aucune inférence promue en fait ; runs lourds checkpointables.

## Dependencies

E02 et E03.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | ResearchCase/Claim/Evidence contracts et completeness policy | schema/claim lineage | vérité typée |
| S02 | Queue, ownership, SLA, blockers et resume | transition/idempotence | dossier reprenable |
| S03 | Orchestration passes avec budget/checkpoints | mocked limits/cache tests | heavy run stoppable |
| S04 | Contradiction/falsifier/side-story bounded workflows | red-team gold cases | branches reliées au tronc |
| S05 | Company 360 read model et provenance UI | API/UI contracts | product data absente |
| S06 | Research review/accept/reopen/stale lifecycle | role/audit tests | review explicite |
| S07 | Evals de contamination, coverage et factuality | gold set thresholds | seuils de release atteints |

## Epic acceptance

Dossier complet/rejouable sur comptes tests ; aucune mention d'offre injectée avant handoff ; coût et preuves traçables.

## Rollback / compatibility

Artefacts historiques adaptés en lecture ; nouveaux claims non consommés si flag off.

## Deferred work

Demand lifecycle E05 ; recherche automatisée premium.
