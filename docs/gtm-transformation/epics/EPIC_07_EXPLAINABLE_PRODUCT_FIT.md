# Epic 07 — Explainable Product Fit

## Purpose

Faire du FitAssessment une décision auditée, et non un simple score.

## Current state

Qualification cockpit, matrices, gates, blockers, resolvers et décisions pursue/validate existent ; read/write model et staleness inter-versions sont fragmentés.

## Target state

Un FitAssessment relie une DemandVersion à un ProductSnapshot, évalue gates avant score, expose couverture/gaps/risques/alternatives/contre-preuves et verdict humain.

## Gaps

DOMAIN decision object ; DATA refs exactes ; WORKFLOW draft→review→decision→stale ; API compare ; UX decision page ; QA calibration.

## Invariants

Hard gates avant score ; score sans gate critique résolue ne produit jamais `PURSUE` ; inputs versionnés.

## Dependencies

E05 et E06.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | FitAssessment schema + input version locking | reproducibility tests | mêmes inputs=même base |
| S02 | Hard gates/blockers/resolvers policy engine | exhaustive gate matrix | aucun score bypass |
| S03 | Explainable scoring/coverage/gaps/alternatives | gold cases/calibration | justification lisible |
| S04 | Review/decision/override/stale lifecycle | RBAC/audit/expiry | override borné |
| S05 | API queue/detail/compare/read models | contract/409/idempotence | stable v1 |
| S06 | UI Fit workbench + E2E Demand→Fit | visual/functional E2E | target creation gated |

## Epic acceptance

Décision reproductible, contradictoire visible, invalidation sur input superseded, TargetPlan impossible avant verdict autorisé.

## Rollback / compatibility

Projection vers `06_product_fit_matrix.yaml`; cockpit legacy en lecture.

## Deferred work

ML ranking, batch matching à grande échelle.
