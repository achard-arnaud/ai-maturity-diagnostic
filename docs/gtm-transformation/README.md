# Programme de transformation GTM evidence-first

Ce corpus documente la cible d'une petite application GTM evidence-first : les
artefacts versionnés restent la mémoire métier, l'application apporte
navigation, files de travail, décisions, orchestration et audit. Il est fondé
sur `main@5468e57` du présent dépôt et sur un benchmark CRM/Sales Tech externe
(non reproduit ici).

Le programme comporte 14 Epics et 83 Sprints. Chaque Sprint est un incrément
stoppable mergé vers `dev` après CI. Chaque Epic devient une release cohérente
vers `main` après NRT, QA fonctionnelle et audit des invariants.

## Ordre de lecture

1. [`00_GTM_PRODUCT_NORTH_STAR.md`](00_GTM_PRODUCT_NORTH_STAR.md)
2. [`01_AS_IS_AUDIT_AND_GAP_MAP.md`](01_AS_IS_AUDIT_AND_GAP_MAP.md)
3. [`02_DOMAIN_AND_TRUTH_MODEL.md`](02_DOMAIN_AND_TRUTH_MODEL.md)
4. [`03_GTM_LIFECYCLE_AND_STATE_MACHINES.md`](03_GTM_LIFECYCLE_AND_STATE_MACHINES.md)
5. [`04_INFORMATION_ARCHITECTURE.md`](04_INFORMATION_ARCHITECTURE.md)
6. [`05_CANONICAL_OBJECT_AND_EVENT_MODEL.md`](05_CANONICAL_OBJECT_AND_EVENT_MODEL.md)
7. [`06_ROUTE_CONTEXT_AND_API_MODEL.md`](06_ROUTE_CONTEXT_AND_API_MODEL.md)
8. [`07_WORKFLOW_HANDOFF_AND_ARTIFACT_MODEL.md`](07_WORKFLOW_HANDOFF_AND_ARTIFACT_MODEL.md)
9. [`08_EVIDENCE_DECISION_AND_GATES.md`](08_EVIDENCE_DECISION_AND_GATES.md)
10. [`09_RATE_LIMIT_COST_AND_EXECUTION_MODEL.md`](09_RATE_LIMIT_COST_AND_EXECUTION_MODEL.md)
11. [`10_LEARNING_LOOP_OBSERVABILITY_AND_QA.md`](10_LEARNING_LOOP_OBSERVABILITY_AND_QA.md)
12. [`11_MIGRATION_COMPATIBILITY_AND_ROLLBACK.md`](11_MIGRATION_COMPATIBILITY_AND_ROLLBACK.md)
13. [`12_PROGRAM_ROADMAP.md`](12_PROGRAM_ROADMAP.md)
14. [`13_STOP_GO_RELEASE_PLAYBOOK.md`](13_STOP_GO_RELEASE_PLAYBOOK.md)
15. Les documents sous [`epics/`](epics/)

## Autorité documentaire

En cas de conflit : contrats exécutables et tests de `HEAD` > ADR acceptés >
modèles cibles de ce corpus > anciens PRD > maquettes. La North Star arbitre
le produit ; les ADR arbitrent l'architecture ; les schémas et tests
contractuels arbitrent l'exécution.

Les anciens PRD (`docs/PRD_*.md`) et ADR (`docs/ADR-*.md`) restent en place
et ne sont pas marqués supersédés par ce commit : le registre de supersession
et le glossaire commun sont le livrable du Sprint E00-S02, pas de E00-S01. La
baseline machine-readable de E00-S01 (`docs/governance/baseline/`) référence
ce corpus comme cible sans trancher les conflits terminologiques.

## Non-action

Ce corpus ne modifie pas le code applicatif et n'autorise aucun merge de
capacité métier. Il constitue le programme de transformation à valider avant
implémentation, et sert de boussole d'ancrage pour les Sprints de l'Epic 00
et suivants.
