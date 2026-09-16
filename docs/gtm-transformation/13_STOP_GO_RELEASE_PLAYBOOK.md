# Stop & Go Release Playbook

## Branching cible

```text
main ← epic/E##_name ← dev ← sprint/E##-S##_name
```

La branche d'Epic sert de candidate de release si plusieurs Sprints doivent être stabilisés ensemble. Un Sprint passe par PR vers `dev`; la release Epic passe par PR `dev` ou branche Epic synchronisée vers `main`. Les écarts entre `dev` et `main` sont visibles et bornés à un Epic actif.

## Gate de Sprint vers dev

1. Objective et scope inchangés ou décision de changement enregistrée.
2. Tests unitaires/contractuels/intégration pertinents verts.
3. Release gate commune verte ; E2E impactés verts.
4. Migration dry-run/rollback si données touchées.
5. Documentation et traceability matrix mises à jour.
6. Aucun secret/donnée privée ; audit sécurité/workspace si route ou write.
7. Démo fonctionnelle ou preuve machine de l'hypothèse.
8. `STOP.md`/handoff : état, commit, outputs, reste, commandes de reprise, risques.

## Gate d'Epic vers main

- Tous les Sprints obligatoires acceptés ; deferred explicite.
- Full NRT + parcours E2E Epic + isolation workspace.
- Audit invariants evidence/product-blind/gates/currentness/lineage.
- QA fonctionnelle sur gold set ; budget/coût mesuré.
- Migration et rollback rehearsed.
- ADR/README/AGENTS/version/supersession synchronisés.
- Release notes, known limitations et décision Go/No-Go.

## CI à corriger en E00

La workflow GitHub actuelle vérifie les PR, `main` et `agent/**`, mais pas les pushes `dev` ou `sprint/**`/`epic/**`. La cible doit au minimum couvrir PR + pushes `dev`, branches Sprint/Epic actives et `main`. Playwright doit être un job distinct ou une gate explicitement déclarée, pas une spécification dormante.

## Stop condition

On peut arrêter après un Sprint si : `dev` démarre, migrations sont cohérentes, flags protègent l'incomplet, aucune route canonique ne promet une capacité partielle, handoff/reprise existe et les gaps suivants restent documentés.

## Rate-limit stop

Un test lourd est lancé avec budget. À 80 % du budget, checkpoint ; à 100 %, arrêt propre. Le Sprint peut être accepté sans rerun lourd uniquement si sorties cache/gold set prouvent l'acceptance et qu'une dette de validation datée est explicitement classée non bloquante. Les gates sécurité, migration et invariants ne sont jamais contournées pour économiser des tokens.

## Rollback

Le rollback privilégie flags et readers legacy, puis revert code. Les données append-only restent ; les projections se reconstruisent. Toute action externe non réversible est hors périmètre tant que compensation/idempotence/audit ne sont pas conçus.
