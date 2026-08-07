# Qualification Tunnel v0.2 — Architecture et audit de la v0

## Décision d’architecture

Concevoir le projet comme un tunnel de qualification à double ICP :

```text
Réalité du compte                         Réalité de l’offre
-----------------                         -------------------
stratégie                                 problème canonique
organisation                              résultats vendables
capabilités                               ICP et anti-ICP
momentum                                  prérequis et hard gates
contraintes                               preuves et limites
        \                                  /
         \                                /
          -> Opportunity Product Fit -> preuve -> décision
```

Maintenir la symétrie : la recherche entreprise ne charge aucune offre; la définition produit ne connaît aucun compte. Autoriser leur croisement uniquement dans le matcher.

## Audit de la v0

### Skill entreprise trop proche du matching

`company-demand-lead-intelligence` préparait déjà le handoff produit, ce qui pouvait orienter l’interprétation des signaux publics.

Correction : remplacer ce rôle par `enterprise-demand-intelligence`, responsable uniquement des priorités, pouvoirs, capacités, contraintes et gaps du compte.

### Skill produit trop large

`product-offer-matching-intelligence` mélangeait catalogue, ICP, scoring, gates, sélection, pilote, angle de contact et boucle post-entretien.

Correction : séparer `product-icp-intelligence`, `opportunity-fit-matching` et `engagement-pilot-design`.

### Catalogue monolithique

Un catalogue unique chargeait des offres non pertinentes et favorisait la contamination entre produits.

Correction : utiliser un index léger et un fichier versionné par offre. Charger uniquement les offres candidates.

### Fiche Astraforge monolithique

La v0 mélangeait positionnement, architecture, ICP, use cases, sécurité, pilote, pricing et inconnues.

Correction : séparer profil canonique, registre de sources, positionnement, méthode de pilote et inconnues.

### Taxonomie de preuve incohérente

Correction : séparer deux axes :

- `epistemic_status`: `fact | inference | hypothesis | unknown`;
- `evidence_grade`: `P1 | P2 | U1 | W1 | N0`.

### Initialisation cassée

La v0 attendait `templates/study_manifest.yaml`, absent.

Correction : fournir le template et créer des snapshots produit versionnés à l’initialisation.

## Propriété des ressources

| Zone | Contenu | Propriétaire | Interdit |
|---|---|---|---|
| `evidence/product/` | Sources produit | Humain / ingestion | Décision commerciale |
| `product_catalog/` | Vérité produit versionnée | Product ICP / owner | Données compte |
| `studies/<account>/sources/` | Preuves compte | Enterprise research | Vérité produit |
| `05_enterprise_demand_profile.yaml` | Demande qualifiée | Enterprise demand | Recommandation d’offre |
| `inputs/product_snapshots/` | Copie immuable d’une offre | Init script | Mise à jour après création |
| `06_product_fit_matrix.yaml` | Croisement compte × produit | Matcher | Recherche web brute |
| `skills/*/references/` | Méthodes et policies | Mainteneur de skill | Faits volatils |
| `contracts/` | Interfaces | Mainteneur système | Logique métier détaillée |
| `evals/` | Tests de déclenchement et raisonnement | Mainteneur | Données de production |

## Pipeline

```text
qualification-tunnel-router
        |
        +--> enterprise-demand-intelligence
        |       -> 05_enterprise_demand_profile.yaml
        |
        +--> product-icp-intelligence
        |       -> product_catalog/OFFER-*.yaml
        |
        +--> opportunity-fit-matching
        |       -> 06_product_fit_matrix.yaml
        |
        +--> engagement-pilot-design
                -> 07_engagement_hypothesis.md
```

Règle d’or : une skill connaît la méthode de sa responsabilité, jamais la vérité métier d’une autre responsabilité. Passer d’une étape à l’autre par artefact contractuel, jamais par mémoire implicite.
