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

`check_release.py` contrôle notamment les packages, schémas, liens, tests, chemins non portables et fuites de clés privées. Depuis v0.7, il instrumente également l’application Python du control plane (`app/`) et échoue sous **80 % de couverture de lignes**. Les scripts CLI restent couverts par les tests d’intégration existants ; ils ne sont pas inclus artificiellement dans le pourcentage lorsque les tests les lancent en sous-processus.

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

## Control plane v0.6 — parcours demande, matching et nudging

La couche v0.6 conserve tous les invariants précédents et réorganise l’interface autour du parcours utilisateur. Elle est spécifiée dans le [PRD v0.6](docs/PRD_control_plane_v0_6.md), l’[ADR des frontières demande/use cases/nudging](docs/ADR-005-demand-use-case-nudging-boundaries.md) et les [user flows v0.6](docs/USER_FLOWS_v0_6.md).

Quatre surfaces opérationnelles restent séparées :

```text
DEMANDE        ICB -> secteurs -> entreprises -> études -> use cases
OFFRES         rayons -> preuves -> profils canoniques -> revue owner
QUALIFICATION  demande -> snapshots -> hard gates / fit -> personnes -> pilote
NUDGING        inventaire use cases -> productivisation / dépendance / package -> revue
```

### Catalogue de demande

ICB est utilisé comme nomenclature de navigation et de consolidation, jamais comme preuve de besoin. Un secteur passe progressivement de `0` étude éligible à `1`, puis `2/3` avec CTA **Ajouter une 3e entreprise**, puis `3+` avec CTA **Lancer le benchmark**. La règle existante de trois études courantes et suffisamment complètes reste inchangée.

Chaque étude peut produire `05b_use_case_inventory.yaml` via `enterprise-use-case-intelligence`. Les use cases conservent leur entreprise, étude, preuve, maturité, dépendances, réutilisabilité et feedback. Le rollup sectoriel peut les consolider comme evidence pool sans les transformer en vérité d’un autre compte.

### Qualification et matching

Le menu Qualification dérive son état des artefacts persistés et expose la prochaine action autorisée : demande, snapshot, matching, ciblage personne ou pilote. Le **Parcours complet** montre l’ensemble des gates mais ne les exécute pas silencieusement. `qualification-tunnel-router` et `opportunity-fit-matching` restent les frontières autorisées.

### Nudging

Le menu Nudging est volontairement isolé de la qualification initiale. Il ne charge ni ICB, ni benchmark sectoriel, ni profil de demande, ni catalogue produit, ni matrice de fit.

Il propose trois familles d’hypothèses à partir du seul inventaire de use cases de l’entreprise :

- **Productivisation** : mise en série, enrichissement, variantes, actifs réutilisables et réduction du coût marginal d’un use case existant ;
- **Upsell par dépendance** : proposition uniquement lorsqu’un edge `depends_on` ou `enables` relie explicitement les use cases ;
- **Cross-sell package** : assemblage de use cases déjà recensés partageant une famille d’outcome, uniquement lorsqu’un retour d’expérience de l’entreprise permet d’ancrer le storytelling.

Chaque nudge reste une `hypothesis` avec preuves/feedback, préconditions, inconnues et falsifier. L’absence de relation ou de feedback produit zéro suggestion plutôt qu’une inférence commerciale opportuniste.

Le menu **Suivi** remonte les prochaines actions métier calculées — 3e entreprise, benchmark, étape de qualification, inventaire éligible au nudging — avant le backlog de gouvernance et de release.

La posture de déploiement reste celle de v0.5 : local-first, non production-network-ready tant que les gates sécurité, executor, persistence et évaluations correspondantes restent ouverts.

## Control plane v0.7 — chaîne de valeur, patrimoine UC, reach itératif et blockers actionnables

La v0.7 prolonge le parcours sans créer de nouvelle source de vérité. Voir le [PRD v0.7](docs/PRD_control_plane_v0_7.md), l’[ADR-006](docs/ADR-006-uc-graph-reach-blocker-resolution.md), les [user flows v0.7](docs/USER_FLOWS_v0_7.md) et la [trousse de reprise](docs/POST_HOLIDAY_KIT_v0_7.md).

Le parcours fonctionnel devient :

```text
ICB / secteur
-> entreprise / étude
-> 05 demande
-> 05b use cases
-> 05c chaîne de valeur + causes
-> snapshots produit
-> 06 fit
-> 06b contacts
-> 06c reach first/second wave
-> 07 preuve / pilote
```

### Porter + Ishikawa depuis un use case

Le deep dive entreprise expose **Analyse chaîne de valeur** sur chaque UC canonique. `enterprise-value-chain-causal-analysis` cartographie de façon evidence-bounded :

- activités amont, activité focale, aval et support ;
- handoffs et points de contrôle ;
- effets valeur/coût/qualité/délai/risque ;
- causes `people`, `process`, `technology`, `data`, `governance/control`, `environment/external`.

Une activité adjacente issue de cette analyse reste une hypothèse. Seul `enterprise-use-case-intelligence` peut la transformer en UC après validation avec des preuves de l’entreprise.

### Patrimoine UC — principes Zettelkasten sans nouvelle infrastructure

La v0.7 retient seulement les principes utiles : UC atomiques avec IDs stables, liens typés et backlinks. Le graphe est recalculé depuis `05b`/`05c` et n’est **pas** une base canonique supplémentaire.

Relations possibles : `depends_on`, `enables`, `variant_of`, `shares_asset`, `same_outcome`, `value_chain_neighbor`, `causal_neighbor`, `similar_pattern`. Une relation cross-company/sectorielle reste une hypothèse comparative et porte `demand_proof: false`.

Aucun graph DB, vector store ou moteur Zettelkasten n’est ajouté avant qu’un usage réel démontre un problème de recherche, de volume ou de coût de maintenance.

### Matchmaker reach itératif

Après un fit valide, `iterative-reach-matchmaking` bridge les artefacts déjà collectés : produit/ICP, contacts privés, organigramme/système de décision, use cases et newsflow. Il classe des hypothèses de rôles :

- promoteur / sponsor ;
- prescripteur / influenceur ;
- terrain owner / utilisateur ;
- sponsor technique ;
- veto / contrôle.

Les personnes sont organisées en `first`, `second` et `validation_only`. Un rôle obsolète déclenche **Valider le rôle actuel** ; une lane manquante déclenche **Élargir le 2e tour**. Le newsflow explique le `why_now` ou l’ordre de validation, jamais le fit ni l’autorité.

### Blocker = action à résoudre

Un blocker exposé par un workflow comprend désormais son ID/type, pourquoi il bloque, l’état attendu, la skill ou action humaine propriétaire, un CTA, ses context paths et la postcondition. L’interface n’utilise plus un bouton désactivé comme seule réponse à un blocker actif : le resolver remonte vers le prérequis approprié.

### Navigation et suivi

Les menus principaux restent volontairement compacts : **Demande · Offres · Qualification · Nudging · Suivi · Skills**. Les vues Reach, Porter/Ishikawa et Patrimoine UC sont contextuelles afin d’éviter un CRM parallèle.

- Offre -> audit vérité produit -> opportunités utilisant cette offre -> qualification.
- Entreprise -> organisation -> UC -> chaîne de valeur -> patrimoine -> qualification.
- Qualification -> contacts -> reach -> pilote.
- Nudging -> même-company UC graph -> hypothèses -> revue/feedback.
- Suivi -> blockers métier et pending avant TODO techniques.

La v0.7 ne change pas la posture de sécurité : elle reste locale/interne. Elle ne constitue ni un CRM outbound, ni une autorisation d’exposition réseau, ni une automatisation décisionnelle sans Gold Set.
