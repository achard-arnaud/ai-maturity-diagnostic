# Migration, Compatibility and Rollback

## Stratégie

Strangler par contracts/read models : ajouter le canonique, adapter le legacy, mesurer la parité, basculer, puis retirer. Aucun big bang artefacts + API + frontend dans un même Sprint.

## Migrations

- Chaque migration possède `plan`, `dry-run`, inventory, mapping, hashes/counts, backup/rollback manifest et rapport.
- Les schémas sont versionnés ; lecteurs N et N-1 au minimum pendant l'Epic concerné.
- Les writers dual-write seulement si l'idempotence et la réconciliation sont testées ; sinon writer unique + projection.
- Product catalog ownership est tranché avant déplacement.
- Les événements historiques sont conservés ; pas de reconstruction fictive de dates ou d'actors.

## Feature flags

Flags par workspace pour nouveaux read models, routes et shell. Tout flag a owner, date d'expiration, métrique de bascule et chemin de retrait.

## Rollback

Rollback code et rollback data sont séparés. Un revert applicatif ne supprime jamais des événements/artefacts créés ; il remet l'ancien reader/route et marque les nouveaux outputs comme non consommés si nécessaire.

## Compatibility gates

- tests legacy + canonique ;
- parité de projections sur gold set ;
- deep links et refresh/back ;
- export/import ;
- cross-workspace isolation ;
- absence de mutation silencieuse des snapshots/decisions ;
- rollback rehearsal avant main pour Epic avec migration.
