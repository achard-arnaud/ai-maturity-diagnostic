# 00 — Cadrage de la mission

## Objet

| Champ | Valeur |
|---|---|
| Entité analysée | Astraforge et le système de qualification associé |
| Nature de la mission | Refonte d’architecture de skills, pas une étude de compte |
| Périmètre | Racine du dépôt, tunnel v0.2 et couche réseau/release v0.3 |
| Langues | Français pour la documentation métier, anglais pour les identifiants et contrats |

## Décision à éclairer

| Champ | Valeur |
|---|---|
| Audience | Propriétaire produit et mainteneurs du système de qualification |
| Décision | Mettre en œuvre un tunnel à double ICP séparant demande entreprise, vérité produit, matching et pilote |
| Horizon | Milestone v0.3 daté du 23 juillet 2026 |
| Confidentialité | Matériaux fournis par l’utilisateur et sources publiques citées par celui-ci |
| Format | Package de dépôt validé par scripts et evals |

## Questions spécifiques

1. Les cinq skills ont-elles une responsabilité exclusive et un déclenchement testable ?
2. Les données compte et produit ne se croisent-elles que dans le matcher ?
3. Les handoffs, snapshots et décisions sont-ils structurés, versionnés et validables ?

## Inclus

- Skills du tunnel v0.2 et du réseau v0.3, contrats, catalogue des quatre offres, preuve produit Astraforge, templates, scripts, docs et evals.
- Compatibilité avec les quatre lentilles de recherche entreprise existantes.

## Exclu

- Recherche fraîche sur un compte nommé.
- Validation commerciale ou technique des capacités Astraforge non étayées.
- Installation globale des skills hors du dépôt.

## Paramètres de preuve

| Paramètre | Choix |
|---|---|
| Date de coupure | 2026-07-23 |
| Statuts | `fact`, `inference`, `hypothesis`, `unknown` |
| Grades | `P1`, `P2`, `U1`, `W1`, `N0` |
| Sources de conception | Quatre pièces jointes et cahier des charges utilisateur |
| Recherche web | Non relancée; les conclusions GitHub restent attribuées au matériau fourni |

## Critères de succès

- [x] Frontières des cinq skills explicites.
- [x] Contrats de handoff définis.
- [x] Catalogue et snapshots validés automatiquement.
- [x] 220 cas structurés de déclenchement présents et vérifiés en forme (11 skills × 20).
- [ ] Evals de déclenchement et de raisonnement rejoués par un modèle sur un Gold Set métier.
- [x] Initialisation et validation d’une étude de démonstration réussies.
- [x] Tests adverses identité, scores, gates, coordination aval et dates sectorielles ajoutés.
- [x] Gate de release reproductible et CI GitLab ajoutés.

## Extension réseau v0.3 — 2026-07-23

| Champ | Valeur |
|---|---|
| Entrée | Fichier privé de 1 308 contacts, colonnes `Name`, `Job title`, `Company`, `Country` |
| Décision | Construire une première couche personne–entreprise–secteur–étude–produit–reach |
| Données personnelles | Confidentielles, conservées sous `data/private/` et ignorées par Git |
| Granularité ICB | Candidat sectoriel lorsque le nom le permet; sinon `pending`; aucune attribution subsector |
| Application des études | File seulement, aucune création en masse sans `--apply --limit` |

### Critères de succès réseau

- [x] Intake, checksum, IDs et relations canoniques.
- [x] Mapping ICB candidat avec confiance et limites.
- [x] Screening réseau distinct du product fit.
- [x] File de création et rafraîchissement d’études.
- [x] Ciblage personne après match uniquement.
- [x] Reach bloqué quand les preuves ou le rôle actuel manquent.
- [x] Consolidation sectorielle soumise à un seuil de trois études.
