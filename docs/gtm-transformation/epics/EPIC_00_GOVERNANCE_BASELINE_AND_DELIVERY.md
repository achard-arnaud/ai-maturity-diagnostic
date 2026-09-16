# Epic 00 — Governance, Baseline and Delivery

## Purpose

Rendre toute transformation suivante vérifiable, stoppable et non ambiguë.

## Current state

CI centralisée dans `scripts/check_release.py`, nombreux tests et ADR, mais documents empilés, versions « current » périmées, CI push sans `dev`, Playwright hors release gate et branches documentaires non réconciliées.

## Target state

Une baseline signée, une autorité documentaire, une traceability matrix et une CI Sprint/Epic qui protègent `dev` et `main`.

## Gaps

PRODUCT vocabulaire ; DOMAIN frontières ; QA NRT/E2E ; DOCUMENTATION supersession ; CI triggers ; SECURITY checks explicites.

## Invariants

Evidence-first, product-blind, hard gates, workspace isolation, aucun changement métier silencieux.

## Dependencies

Aucune ; cet Epic établit la baseline des suivants.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Inventorier HEAD, branches, PRD/ADR/tests/routes ; produire baseline machine-readable | inventory completeness | baseline versionnée |
| S02 | Adopter glossaire, bounded contexts et registre supersession | doc/link validation | aucun terme critique ambigu |
| S03 | Étendre CI à `dev`, `sprint/**`, `epic/**`; jobs lisibles | workflow lint + dry PR | checks requis visibles |
| S04 | Intégrer Playwright par journey/tags et artefacts de panne | 3 journeys sur fixture | E2E reproductible |
| S05 | Traceability requirements→contracts→tests ; templates Sprint/Epic/handoff | linter de traçabilité | release candidate auditable |

## Epic acceptance

PR témoin vers `dev` et release témoin vers `main` passent les gates ; baseline/limitations publiées ; aucun code fonctionnel modifié sans requirement.

## Rollback / compatibility

Revert YAML CI et docs ; aucune migration de données.

## Deferred work

Refactor plateforme E01 ; objets métier E02+.
