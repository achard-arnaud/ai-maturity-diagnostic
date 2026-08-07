# Skill trigger matrix

| Skill | Trigger positif principal | Trigger négatif principal |
|---|---|---|
| `qualification-tunnel-router` | Où en sommes-nous, quelle skill ensuite, lance le tunnel | Analyse métier d’une étape précise |
| `enterprise-demand-intelligence` | Recherche d’un compte, gaps, pouvoirs, signaux et demande | Définition ou recommandation produit |
| `product-icp-intelligence` | Définir ou réviser une offre, son ICP, ses preuves et gates | Analyse d’un compte nommé |
| `opportunity-fit-matching` | Croiser deux profils déjà constitués | Recherche fraîche ou conception du pilote |
| `engagement-pilot-design` | Transformer un match en preuve, discovery ou pilote | Décider le fit ou refaire la recherche |
| `network-contact-intake` | Importer une liste privée et créer les objets réseau | Recherche entreprise ou product fit |
| `enterprise-icb-mapping` | Classer une entreprise selon son activité | Screening réseau ou matching produit |
| `network-account-screening` | Prioriser les comptes à rechercher | Conclure à un besoin ou à un fit |
| `network-study-orchestration` | Créer ou rafraîchir la file d’études | Produire l’analyse métier |
| `person-opportunity-targeting` | Sélectionner des personnes après un fit | Décider le fit depuis un titre |
| `sector-intelligence-consolidation` | Consolider trois études actuelles ou plus | Généraliser depuis le volume de contacts |

## Collision entreprise + produit

Pour « Analyse LDLC pour Astraforge », ne pas déclencher le matching tant que `05_enterprise_demand_profile.yaml` n’existe pas. Transmettre le produit uniquement comme contexte de destination.

## Collision ICP

- « Quel est l’ICP d’Astraforge ? » -> Product ICP.
- « Ce compte correspond-il à l’ICP Astraforge ? » -> Matching si les deux profils existent.
- « Trouve des comptes correspondant à l’ICP Astraforge » -> profil produit existant puis recherche et screening compte; ne pas faire réécrire la vérité produit par la skill entreprise.

## Discipline d’évaluation

Maintenir 20 requêtes par skill : 10 positives et 10 négatives. Rejouer les suites après toute modification significative des descriptions. Utiliser `evals/reasoning_cases.yaml` pour les gates et arbitrages métier.

## Collision contact × produit

Un titre comme « CTO » ou « Head of AI » ne déclenche jamais le product fit. L’ordre obligatoire reste : diagnostic entreprise -> fit entreprise–produit -> ciblage personne -> reach.

## Collision screening × demande

Un tier A indique une forte priorité de recherche depuis le réseau. Il ne prouve ni maturité, ni urgence, ni budget, ni demande.
