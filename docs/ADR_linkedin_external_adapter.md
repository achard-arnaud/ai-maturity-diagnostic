# ADR — LinkedIn as an optional external adapter

**Status:** Accepted as design constraint; implementation deferred
**Date:** 2026-07-23

## Contexte

Le système v0.3 fonctionne sans LinkedIn. Son usage potentiel est la validation de fraîcheur d’une relation connue, non la découverte de prospects ni le calcul du fit.

## Décision

LinkedIn sera, si les gates sont franchis, un capteur de preuve optionnel avec les invariants suivants :

1. `person_id`, `company_id` et `relationship_id` internes restent canoniques;
2. une sortie connecteur est une preuve, non une vérité canonique;
3. chaque appel passe capability discovery, auth et policy checks;
4. la première phase est read-only;
5. aucun scraping ni browser automation non autorisée;
6. aucun outreach automatique;
7. aucune modification directe de la demande entreprise ou du product fit;
8. l’absence ou la panne du plugin ne bloque pas le cœur;
9. la persistance suit les contraintes du programme LinkedIn réellement utilisé;
10. toute future écriture requiert une décision d’architecture séparée.

## Conséquences

Avantages : indépendance fournisseur, contrats stables, frontière privacy explicite, rollback simple et matching reproductible.

Coûts : enrichissement moins automatique, validation manuelle persistante, accès Sales Navigator non garanti et gestion éventuelle de données transitoires.

## Options rejetées

- **Scraping/browser automation** : conformité et fragilité.
- **LinkedIn ID canonique** : dépendance fournisseur et contexte d’accès variable.
- **Appel LinkedIn par le matcher** : contamination du raisonnement déterministe.
- **Outreach v0.1** : domaine d’autorisation et de risque distinct.

## Test de réversibilité

Retirer LinkedIn doit laisser fonctionnels intake, ICB, screening, recherche, demand profile, product fit, person targeting, validation manuelle, reach hypothesis et sector rollup.
