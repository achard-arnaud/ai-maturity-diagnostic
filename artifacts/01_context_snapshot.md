# 01 — Instantané de contexte

## Cadre temporel

- Date de l’instantané : 2026-07-23.
- Baseline : dépôt contenant une tour de contrôle de stratégie IA et quatre skills de recherche spécialisées.
- Événement de rupture : passage d’un système recherche + matching à un tunnel symétrique de qualification à double ICP.

## Hypothèses de travail

| ID | Hypothèse | Impact si fausse | Statut |
|---|---|---|---|
| H1 | La demande vise l’implémentation du package v0.2 décrit dans les pièces jointes | Le livrable serait trop expansif | Retenue, car le contenu fournit fichiers, scripts et evals cibles |
| H2 | Les quatre offres sont des vérités produit indépendantes | Le matching resterait biaisé vers Astraforge | Direction owner `U1` |
| H3 | Les profils produit doivent être figés par étude | Une mise à jour du catalogue altérerait les décisions historiques | Direction owner `U1` |
| H4 | La clé fonctionnelle personne à court terme est nom normalisé + entreprise normalisée | Les homonymes inter-entreprises seraient fusionnés | Direction owner `U1`, implémentée et testée |
| H5 | Python 3.11 et les dépendances observées sont réplicables par CI | Le gate de release serait non portable | Testé localement; CI GitLab ajoutée |

## État initial

| Dimension | Observation | Statut | Confiance |
|---|---|---|---|
| Skills entreprise | Tour de contrôle + quatre skills spécialisées présentes | Fait local | Élevée |
| Skills tunnel v0.2 | Absentes au démarrage | Fait local | Élevée |
| Catalogue produit structuré | Absent au démarrage | Fait local | Élevée |
| Contrats et evals v0.2 | Absents au démarrage | Fait local | Élevée |
| Preuve Astraforge | Partielle, principalement transcript dérivé et direction owner | Inférence fournie | Moyenne |

## Inconnues susceptibles de changer le verdict

- Architecture et technologies Astraforge effectivement déployées.
- Preuves clients externes et résultats attribuables.
- Prix, modèle commercial, sécurité formelle et environnements supportés.

## Priorités

1. Verrouiller les frontières compte/produit/matching/pilote.
2. Rendre les handoffs et snapshots vérifiables par machine.
3. Tester les collisions de déclenchement et les gates sur des cas négatifs.
4. Rendre le dépôt reproductible, expurger les secrets historiques et centraliser la configuration.

## Journal de cadrage

| Date | Décision | Motif | Impact |
|---|---|---|---|
| 2026-07-23 | Traiter la demande comme une implémentation de package v0.2 | Les pièces jointes décrivent une architecture, des contenus et des scripts complets | Création de cinq skills et des ressources associées |
| 2026-07-23 | Ne pas faire de recherche compte | La mission porte sur le système de qualification | Les quatre passes corporate/org/hiring/newsflow ne sont pas exécutées |
| 2026-07-23 | Ingérer le réseau sans considérer les titres comme actuels | Le fichier n’a aucun champ de date | Toutes les relations restent `unverified` |
| 2026-07-23 | Utiliser l’ICB Equity v5.0 comme taxonomie | Source officielle LSEG de mars 2026 | 11 industries, 20 supersectors et 45 sectors embarqués |
| 2026-07-23 | Ne pas appliquer automatiquement la file de 136 études | La priorité de recherche ne prouve pas le besoin et une création massive serait prématurée | File générée, application bornée laissée explicite |
| 2026-07-23 | Conserver des IDs internes et utiliser nom + entreprise comme seed transitoire | Éviter la fusion d’homonymes avant une future résolution LinkedIn | Migration privée sauvegardée, tests adverses ajoutés |
| 2026-07-23 | Distinguer rollup exploratoire et décisionnel | Les candidats ICB `N0` ne sont pas des classifications validées | `candidate/mixed -> exploratory`; tous validés -> `decision_grade` |
| 2026-07-23 | Centraliser les règles fit et la release | Éviter les divergences entre validation, ciblage et reach | Module partagé, `pyproject.toml`, CI et `check_release.py` |

## État réseau après premier intake

| Dimension | État | Limite structurante |
|---|---|---|
| Personnes | 1 308 objets privés | Identité et fonction à rafraîchir |
| Entreprises | 662 identités conservatrices | Maisons-mères, filiales et marques non regroupées sans preuve |
| ICB | 272 candidats, 362 pending, 28 hors périmètre probables | Les candidats `N0` ne sont pas des classifications validées |
| Screening | 60 A, 76 B, 213 C, 313 D | Mesure l’accès de recherche, pas le fit |
| Études | 136 créations proposées | Aucune étude appliquée ni recherche publique exécutée |
| Secteurs | 0 rollup éligible | Il manque trois études complètes et actuelles par secteur |
