# Epic 03 — Signal-Based Discover

## Purpose

Faire du network screening une capacité signal-based et non une liste de contacts.

## Current state

Screening/ICB/study queue existent côté artefacts/skills ; peu d'objets applicatifs Signal, Watchlist, SavedSearch ou List avec lifecycle.

## Target state

Discover permet d'ingérer, normaliser, relier, revoir, expirer et convertir des signaux en priorité de recherche — jamais en preuve de demande.

## Gaps

PRODUCT workspace Discover ; DOMAIN signal semantics ; DATA dedup/freshness ; WORKFLOW review→queue ; API filters ; UX lists/watchlists ; QA false positives.

## Invariants

Le signal ne devient jamais une preuve de demande ; le screening priorise uniquement la recherche.

## Dependencies

E02.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Signal schema/source/freshness/dedup et policies | schema + expiry cases | signal ≠ demand garanti |
| S02 | Ingestion adapters public/manual/import avec provenance | contract/failure tests | core sans intégration |
| S03 | SavedSearch, List, SmartList et Watchlist | deterministic membership | listes versionnées |
| S04 | Screening score explicable + hard exclusions | gold set/no direct fit | score borné à recherche |
| S05 | Discover queue/API/read models | pagination/authorization | tri et filtres stables |
| S06 | UI Discover et handoff explicite ResearchQueued | E2E signal→queue | ancien screening accessible |

## Epic acceptance

Un signal sourcé peut être revu, relié à un compte, rejeté/expiré ou convertir en ResearchCase sans créer Demand/Fit.

## Rollback / compatibility

Signal store append-only et projections désactivables ; files historiques préservées.

## Deferred work

Research substantielle E04, sources premium/connecteurs.
