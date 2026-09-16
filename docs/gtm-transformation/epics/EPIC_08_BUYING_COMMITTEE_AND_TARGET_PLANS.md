# Epic 08 — Buying Committee and Target Plans

## Purpose

Passer de contacts agrégés à un plan de ciblage explicite, actuel et relié au fit.

## Current state

`contact_targets`, reach strategies et lanes first/second/validation existent ; pas de vraie route profil personne et currentness/authority restent des blockers fréquents.

## Target state

TargetPlan versionné : sponsor, champion, user, prescripteur, technique, procurement et blocker ; warm paths, confiance, preuves, ordre de contact et besoins de validation.

## Gaps

DOMAIN roles/influence ; DATA currentness ; WORKFLOW validate roles ; API person-target links ; UX map ; QA title≠authority.

## Invariants

Fit avant ciblage ; titre ne prouve pas autorité ; currentness insuffisante bloque Reach.

## Dependencies

E02 et E07.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | TargetPlan/StakeholderRole/Influence schemas | schema/cardinality | rôles ≠ titres |
| S02 | Currentness/authority/warm-path evidence policies | stale/conflict gold cases | ready strict |
| S03 | Plan builder et validation workflow | transition/resolver tests | blockers actionnables |
| S04 | Graph/read model buying committee | graph determinism | projection sans new truth |
| S05 | API people↔target plan + privacy controls | IDOR/PII/pagination | accès borné |
| S06 | UI Targets/map/order + E2E Fit→Targets | functional/refresh-back | reach gated |

## Epic acceptance

1–5 contacts prioritaires peuvent être justifiés ; toute currentness insuffisante bloque ou route vers validation.

## Rollback / compatibility

Projection legacy `06b_contact_targets.yaml`; lanes existantes conservées.

## Deferred work

Enrichissement payant, social graph exhaustif.
