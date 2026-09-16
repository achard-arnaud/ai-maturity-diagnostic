# Epic 02 — Canonical Account and Network Graph

## Purpose

Créer la fondation identité/relations/temporalité de Discover, Research et Targets.

## Current state

Contrats Person/Company/Relationship, index réseau, create/reassign/dedup, Account 360 et données privées existent ; la route personne stable et l'historique de rôles/currentness sont faibles.

## Target state

Personnes, entreprises, identités externes et relations possèdent IDs stables, provenance, validité temporelle, résolution de doublons et projections workspace-scoped.

## Gaps

DOMAIN canonical identity ; DATA temporal relations ; API person/company deep links ; UX merge review ; SECURITY PII ; QA IDOR/dedup.

## Invariants

Un signal réseau ne prouve ni demande ni autorité ; données privées workspace-scoped ; merge d'identité explicite et réversible.

## Dependencies

E01.

## Sprint plan

| Sprint | Objective / implementation | Tests & CI gate | Stop condition |
|---|---|---|---|
| S01 | Schémas v1 Person/Company/Relationship/ExternalIdentity | schema/property/N-1 reader | contrats figés |
| S02 | Temporal Role/Employment et currentness policy | expiry/conflict tests | rôle courant explicable |
| S03 | Identity resolution/dedup proposals sans auto-merge | gold pairs + reversibility | merge humain audité |
| S04 | Read models + API v1 people/companies/relationships | auth/pagination/IDOR | deep links stables |
| S05 | Person 360 et Account 360 composés, provenance visible | UI contract/E2E refresh-back | pas de fusion de vérités |
| S06 | Migration/index/reconciliation du réseau legacy | counts/hashes/parity | legacy routes compatibles |

## Epic acceptance

Journey personne→entreprise→relation et entreprise→personnes fonctionne, cross-workspace protégé, rôle stale bloque les usages aval.

## Rollback / compatibility

Readers legacy via adaptateurs ; merge d'identité compensable.

## Deferred work

Signals E03 ; buying committee E08 ; graph database.
