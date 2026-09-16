# Epic 06 — Product Intelligence and Immutable Snapshots

## Purpose

Rendre la vérité produit publiable, historisée et utilisable de façon reproductible par le fit.

## Current state

Catalogue, harvest, staging, promotion, offer update, search et preuves produit existent ; ownership workspace/global et sémantique version/snapshot restent incomplètes.

## Target state

Product → ProductVersion → ProductSnapshot publié, immuable et hashé ; corrections par supersession ; exclusions/hard gates et preuves datées.

## Gaps

DOMAIN version vs snapshot ; DATA immutability ; WORKFLOW draft/review/publish ; API promotion ; UX diff ; SECURITY ownership ; QA mutation attempts.

## Invariants

Aucune preuve compte dans la vérité produit ; snapshot publié immuable ; correction par supersession.

## Dependencies

E01.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Product/Version/Snapshot/Evidence schemas | schema/N-1 | semantics figées |
| S02 | Draft/review/publish/supersede workflow et RBAC | transition/audit | publication contrôlée |
| S03 | Snapshot hash, immutability et stale propagation | mutation/repro tests | fit reproductible |
| S04 | Catalog ownership/subscription model selon ADR E01 | isolation/visibility | pas de fuite cross-workspace |
| S05 | API/search/diff/read models | contract/performance fixtures | deep links stables |
| S06 | UI library/version diff/publish + migration legacy | E2E harvest→publish | catalogue compatible |

## Epic acceptance

Un fit futur peut référencer exactement le contenu publié ; modifier l'offre crée une nouvelle version sans changer l'historique.

## Rollback / compatibility

Ancien catalogue exposé comme version importée ; publication flaggable.

## Deferred work

Pricing engine, CPQ, syndication externe.
