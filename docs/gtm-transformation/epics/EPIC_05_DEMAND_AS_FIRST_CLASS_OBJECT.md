# Epic 05 — Demand as a First-Class Object

## Purpose

Transformer la demande d'un artefact agrégé en objet CRM qualifiable et révisable.

## Current state

`enterprise_demand_profile`, formulaire d'intake, use-case inventory, value-chain et catalog views existent ; observation, hypothèse et demande confirmée sont encore trop agrégées.

## Target state

Chaque Demand possède problème, population, impact, urgence, initiative, sponsor/budget/timing connus ou inconnus, preuves, statut et historique.

## Gaps

DOMAIN Demand/Need/Initiative boundaries ; DATA versioning ; WORKFLOW qualify/reject/stale ; API CRUD commands ; UX queue ; QA no-fit leakage.

## Invariants

Demand indépendante du catalogue ; inconnues visibles ; fit et ciblage interdits dans ce contexte.

## Dependencies

E04.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Demand schema v1 + mapping depuis profils/use cases | migration parity | objet non contaminé |
| S02 | Lifecycle et qualification checklist/gates | state/property tests | transitions explicables |
| S03 | Claim/Evidence links, confidence et contradiction | lineage/stale tests | provenance complète |
| S04 | Demand queue/API/read model et édition optimiste | auth/409/idempotence | mutation sûre |
| S05 | UI Demands + dossier compte + resolvers | E2E detect→qualify | unknowns visibles |
| S06 | Migration/reconciliation des artefacts legacy | hashes/counts/N-1 | rollback validé |

## Epic acceptance

Demand peut être détectée, qualifiée, rejetée, réouverte ou stale indépendamment du produit ; aucun match automatique.

## Rollback / compatibility

Projection `05_enterprise_demand_profile.yaml` maintenue pendant transition.

## Deferred work

Fit E07 ; voice-to-text d'entretien dans un Epic ultérieur si priorisé.
