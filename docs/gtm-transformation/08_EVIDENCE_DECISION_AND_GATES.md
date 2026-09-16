# Evidence, Decision and Gates

## Evidence record

Une preuve porte source, locator, type, date du fait/publication/observation/consultation, excerpt borné, hash, licence/usage, entity refs, claims supportés/contestés, freshness et niveau de confiance.

## Decision record

Une décision référence les versions exactes d'inputs, règles et gates évalués, résultat, alternatives, contre-preuves, inconnues, actor et expiration/review date.

## Ordre des gates

1. Complétude minimale et provenance.
2. Freshness/currentness.
3. Hard gates produit et conformité.
4. Blockers critiques.
5. Scoring explicable.
6. Validation humaine selon seuil de risque.

Un score ne transforme jamais `FAIL` ou blocker critique ouvert en `PURSUE`.

## Resolver contract

`why_blocked`, `required_state_or_evidence`, `owner_capability`, `cta`, `postcondition`, `cost_estimate`, `expiry`.

## Red-team fonctionnel

À chaque décision majeure : chercher une explication alternative, un falsifier, une preuve contradictoire et une dépendance non résolue. Le red-team n'est pas le terme générique pour QA ou rétrospective ; il vise une conclusion contestable.
