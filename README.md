# AI Maturity Diagnostic & Enterprise Intelligence v0.4

Ce dépôt fournit un système modulaire pour transformer des preuves publiques, des vérités produit et des données privées autorisées en diagnostics IA, décisions commerciales, notes exécutives et dossiers de candidature traçables.

Il ne confond jamais un signal avec une preuve, un score avec une décision, ni la mise en page avec l’analyse métier.

## Capacités principales

| Couche | Finalité | Point d’entrée |
|---|---|---|
| Diagnostic entreprise | Reconstituer stratégie IA, organisation, recrutement, sourcing et maturité | `ai-strategy-control-tower` |
| Qualification commerciale | Séparer demande du compte, vérité produit, hard gates, fit et pilote | `qualification-tunnel-router` |
| Intelligence réseau | Importer un réseau privé, prioriser les comptes et cibler les personnes après le fit | `network-contact-intake` |
| Business intelligence | Produire une analyse et une recommandation décisionnelle Sarah-Pro | `business-intelligence-nice` |
| Candidatures | Qualifier une opportunité et construire un dossier François-Pro ou Sarah-Pro | `application-nice` |
| Production Nice | Transformer un contenu gelé en HTML, PDF et PNG avec QA visuelle | `nice-output-engine` |

Le [catalogue complet des skills](skills/README.md) précise les responsabilités exclusives et les handoffs.

## Architecture

```text
RÉSEAU       contacts -> identité -> ICB -> screening -> file d'études
ENTREPRISE   stratégie -> organisation -> recrutement -> newsflow -> demande
PRODUIT      vérité produit -> ICP -> hard gates -> snapshot
MATCHING     demande + snapshot -> fit -> personnes -> pilote
INTELLIGENCE preuves -> analyse -> recommandation -> contenu gelé
OUTPUT       contrat de contenu -> template -> HTML/PDF/PNG -> QA visuelle
```

### Invariants

- La recherche entreprise reste product-blind jusqu’au matching.
- Les faits compte restent séparés des profils produit canoniques.
- Les hard gates précèdent le scoring ; un score élevé ne neutralise jamais un blocker.
- Le ciblage d’une personne commence après le fit et après validation de son rôle courant.
- `nice-output-engine` ne recherche, ne score et ne renforce aucun claim.
- `application-nice` confirme toujours `François-Pro` ou `Sarah-Pro` avant de lire une source candidat.
- Les données privées ne sont jamais requises pour exécuter les validations publiques.

## Choisir le bon parcours

### Diagnostic public d’une entreprise

1. Lire [`AGENTS.md`](AGENTS.md).
2. Démarrer avec [`ai-strategy-control-tower`](skills/ai-strategy-control-tower/SKILL.md).
3. Conserver preuves et sorties dans `studies/<entreprise>-<date>/`.
4. Consolider la demande avant tout matching avec une offre.

### Qualification d’une opportunité commerciale

1. Utiliser [`qualification-tunnel-router`](skills/qualification-tunnel-router/SKILL.md).
2. Produire séparément le profil de demande et le snapshot produit.
3. Exécuter le matching, puis seulement le ciblage personne et la conception du pilote.

### Note de business intelligence

1. Utiliser [`business-intelligence-nice`](skills/business-intelligence-nice/SKILL.md) pour la question de décision, la recherche, la preuve et la recommandation.
2. Geler le contenu fonctionnel.
3. Utiliser [`nice-output-engine`](skills/nice-output-engine/SKILL.md) pour un brief exécutif, un benchmark ou une business note de 5 à 7 pages.

### Candidature ou préparation d’entretien

1. Utiliser [`application-nice`](skills/application-nice/SKILL.md).
2. Confirmer la persona active avant toute lecture de CV ou d’exemple.
3. Maintenir séparées les vérités entreprise, rôle et candidat.
4. Utiliser `nice-output-engine` uniquement après validation du contenu et des preuves.

## Installation et validation

Python 3.11 est la baseline testée. Les dépendances sont centralisées dans `pyproject.toml`.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[docs,dev]'
python scripts/check_release.py
```

Commandes spécialisées :

```bash
python scripts/validate_package.py
python scripts/import_contacts.py <contacts.tsv> --batch-date YYYY-MM-DD
python scripts/map_companies_icb.py
python scripts/screen_network_accounts.py
python scripts/sync_study_queue.py
python scripts/validate_network.py
python scripts/validate_linkedin_design.py
python scripts/init_study.py "Entreprise" --date YYYY-MM-DD --offers all
python scripts/validate_study.py studies/entreprise-YYYYMMDD
```

`check_release.py` contrôle notamment les packages, schémas, liens, tests, chemins non portables et fuites de clés privées. Le réseau privé est validé lorsqu’il est présent et explicitement ignoré dans un clone public.

## Structure du dépôt

```text
skills/             processeurs spécialisés et contrats d'utilisation
contracts/          handoffs structurés de qualification et de réseau
data/taxonomies/    nomenclature ICB et règles candidates
data/private/       identités et relations privées, ignorées par Git
product_catalog/    profils produit versionnés
evidence/product/   preuves produit séparées des preuves compte
templates/          gabarits d'étude partagés
evals/              cas de triggering et de raisonnement
scripts/            initialisation, génération et validations
docs/               architecture, politiques et décisions différées
studies/            études locales et leurs evidence ledgers
artifacts/          cadrage et artefacts de la tour de contrôle
```

Chaque étude reçoit des snapshots produit avec leur SHA-256 : une modification ultérieure du catalogue ne réécrit pas rétroactivement le raisonnement historique.

## Confidentialité et connecteurs

Le dépôt public contient les méthodes, contrats, schémas et politiques de templates. Il exclut les CV, coordonnées, transcriptions, identités réseau et dossiers de candidature privés.

L’intégration LinkedIn reste documentée comme un capteur read-only optionnel. Elle n’est pas installée dans le runtime tant que les gates d’accès, de privacy et le Gold Set ne sont pas validés. Voir le [PRD LinkedIn](docs/PRD_linkedin_qualification_plugin_v0_1.md) et sa [matrice de traçabilité](docs/linkedin_prd_traceability_matrix.md).

## Documentation de référence

- [Architecture réseau v0.3](docs/05_network_architecture_v0_3.md)
- [Revue de readiness v0.3](docs/06_release_readiness_v0_3.md)
- [Catalogue des skills](skills/README.md)
- [Contrat global d’agent](AGENTS.md)

## Control plane v0.5 — exploitation locale

La couche v0.5 ajoute une interface locale d’orchestration sans modifier les responsabilités, handoffs ou invariants ci-dessus. Elle est documentée dans le [PRD v0.5](docs/PRD_productized_diagnostic_v0_5.md), l’[ADR de frontière web](docs/ADR-004-web-control-plane-boundary.md) et la [boucle SDLC](docs/SDLC_superpowers_loop.md).

Démarrage local :

```bash
python -m app.server
# http://127.0.0.1:8080
```

L’interface permet de :

- découvrir les packages `skills/*/SKILL.md` et préparer un appel unitaire explicitement versionné ;
- consulter les offres canoniques par rayonnage sans dupliquer leur vérité produit ;
- découvrir des sources publiques de catalogues d’entreprise ou importer un catalogue déjà récolté ;
- conserver tout résultat de harvesting comme claim non revu sous `data/private/catalog_harvest/` ;
- consulter les TODO historiques et les gates de productisation v0.5.

Sans variable `AI_DIAGNOSTIC_SKILL_EXECUTOR`, un CTA de skill retourne une enveloppe `prepared` et ne prétend pas qu’un agent a exécuté la demande. La sélection d’un runtime de production reste un gate explicite.

Le harvesting ne promeut jamais automatiquement un claim vers `product_catalog/` : toute canonicalisation passe par `product-icp-intelligence` puis une revue humaine.

Le serveur écoute uniquement `127.0.0.1` par défaut. Aucune exposition réseau ou production n’est considérée prête tant que l’authentification, l’autorisation, l’audit et le hardening documentés dans `artifacts/TODO_productization_v0_5.yaml` ne sont pas fermés et vérifiés.
