# Enterprise AI Qualification v0.3

Ce dépôt combine trois couches complémentaires :

1. une tour de contrôle qui reconstitue la stratégie IA réelle d’une entreprise à partir de preuves publiques;
2. un tunnel v0.2 qui sépare la demande d’un compte, la vérité des offres, le matching et la conception d’une preuve commerciale;
3. une couche réseau v0.3 qui ingère des contacts privés, priorise les comptes, orchestre les études, cible les personnes après le fit et consolide les diagnostics par secteur ICB.

Une intégration LinkedIn read-only est documentée comme option future, mais reste volontairement absente du runtime jusqu’au Gold Set et aux gates d’accès/privacy.

## Installation

Python 3.11 est la baseline testée. Les dépendances sont centralisées dans `pyproject.toml` :

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[docs,dev]'
python scripts/check_release.py
```

Le réseau privé n’est pas requis dans un clone public. `check_release.py` le valide lorsqu’il est présent et le saute explicitement sinon.

## Parcours de qualification

```text
enterprise-demand-intelligence      product-icp-intelligence
              \                       /
               -> opportunity-fit-matching
                           |
                  engagement-pilot-design
```

Utiliser `qualification-tunnel-router` uniquement pour choisir l’étape et contrôler les artefacts.

## Structure

```text
skills/             skills de recherche et de qualification
contracts/          handoffs structurés v0.2 et v0.3
data/taxonomies/    nomenclature ICB et règles candidates
data/private/       réseau et sorties privées, ignorés par Git
product_catalog/    un profil versionné par offre
evidence/product/   preuves produit séparées
templates/          gabarits d’étude v0.2
evals/              cas de triggering et de raisonnement
scripts/            initialisation et validations
docs/               architecture, pitch et migration
studies/            études créées localement
artifacts/          cadrage et artefacts de la tour de contrôle
```

## Commandes

```bash
python scripts/validate_package.py
python scripts/import_contacts.py <contacts.tsv> --batch-date 2026-07-23
python scripts/map_companies_icb.py
python scripts/screen_network_accounts.py
python scripts/sync_study_queue.py
python scripts/validate_network.py
python scripts/validate_linkedin_design.py
python scripts/init_study.py "Entreprise" --date 2026-07-23 --offers all
python scripts/validate_study.py studies/entreprise-20260723
python scripts/check_release.py
```

L’initialisation copie des snapshots produit avec leur SHA-256. Une modification du catalogue ne change donc pas rétroactivement le raisonnement d’une étude.

## Démarrage recherche entreprise

Lire `AGENTS.md`, puis `skills/ai-strategy-control-tower/SKILL.md`. Pour une étude réelle, conserver les preuves et sorties dans `studies/<entreprise>-<date>/`.

Voir [l’architecture réseau v0.3](docs/05_network_architecture_v0_3.md) pour le rôle et les interactions de chaque brique.

Voir [le PRD LinkedIn différé](docs/PRD_linkedin_qualification_plugin_v0_1.md) et sa [matrice de traçabilité](docs/linkedin_prd_traceability_matrix.md). Aucun plugin ni connecteur LinkedIn n’est installé par ces documents.

Voir [la revue de readiness v0.3](docs/06_release_readiness_v0_3.md) pour le périmètre du milestone, les validations et les limites connues.
