# GTM Product North Star

## Problème

Le système sait déjà produire des recherches, preuves, demandes, snapshots, fits, cibles et hypothèses de reach, mais l'utilisateur doit comprendre l'architecture des artefacts pour progresser. Les capacités existent comme modules juxtaposés ; elles ne forment pas encore une boucle GTM lisible, pilotable et économiquement bornée.

## Utilisateurs et jobs

- Fondateur/lead GTM : détecter les comptes où une offre a une chance démontrable de créer de la valeur.
- Analyste : constituer un dossier entreprise product-blind, sourcé et révisable.
- Product marketer : maintenir la vérité de l'offre et savoir quelle version a servi au fit.
- Sales/operator : choisir les bons rôles, exécuter la prochaine action et traiter les réponses.
- Reviewer : accepter, réfuter ou renvoyer une décision sans contourner les hard gates.
- Administrateur : gérer workspace, droits, quotas, politiques et audit sans devenir propriétaire de la vérité métier.

## Chaîne gouvernante

`signals/network → accounts → enterprise research → demand → immutable product snapshot → fit → target plan → reach → engagement → opportunity → proof/deal → land & scale → learning`

## Wedge produit

Une coordination layer GTM pour offres complexes : elle relie preuve, demande, version d'offre, fit explicable, buying committee et actions commerciales dans un graphe typé et auditable partagé entre humains et agents.

## Principes

1. Evidence before inference ; gate before score ; fit before person.
2. Recherche entreprise product-blind jusqu'au matching.
3. Demande et fit sont des objets de premier rang.
4. Un fit référence un snapshot produit immuable, jamais « le produit courant ».
5. Reach est une work queue ; engagement décrit la réaction externe, pas l'activité sortante.
6. Les artefacts restent la mémoire canonique ; le runtime indexe, projette et orchestre.
7. Toute dépense IA est budgétée, cacheable, observable et reprenable.
8. Chaque état bloqué expose raison, preuve manquante, propriétaire, CTA et postcondition.
9. Les intégrations externes sont des capteurs remplaçables.
10. L'apprentissage propose ; il ne réécrit jamais silencieusement les vérités.

## Espaces produits

`Home / Discover / Research / Fit / Targets / Reach / Engagement / Pipeline / Insights / Admin`

Les espaces ne sont pas les états du workflow : ils sont des projections orientées job. `Demand`, `ProductSnapshot`, `FitAssessment` et `EngagementEvent` restent des objets indépendants.

## Non-objectifs initiaux

- CRM généraliste, marketing automation complet ou data warehouse.
- Envoi LinkedIn automatisé, scraping authentifié ou séquence autonome non supervisée.
- Graph database, vector store, microservices ou Kubernetes sans besoin mesuré.
- Réécriture big-bang du cœur Python ou migration immédiate de tous les artefacts vers SQL.
- Optimisation de modèle fondée sur moins de trois études comparables et actuelles.

## Critères de convergence

- Un utilisateur peut aller d'un signal à une prochaine action sans connaître les chemins de fichiers.
- Chaque recommandation forte remonte à une preuve, une règle/gate et une version d'offre.
- Une réponse prospect modifie l'état d'engagement et peut ouvrir une opportunité sans effacer l'historique.
- Une interruption après n'importe quel Sprint accepté laisse `dev` exploitable et reprenable.
- Une release d'Epic vers `main` est migrable, réversible et couverte par NRT.
