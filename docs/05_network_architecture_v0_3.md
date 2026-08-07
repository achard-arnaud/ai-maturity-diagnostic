# Architecture du projet — Réseau, qualification et matching v0.3

## Finalité

Transformer un réseau privé de personnes en un système traçable de qualification commerciale : identifier les entreprises, prioriser la recherche, établir leur demande réelle, la comparer aux offres, sélectionner les contacts pertinents, préparer une approche vérifiable et consolider les apprentissages par secteur.

## Flux de bout en bout

```text
Fichier privé de contacts
        |
        v
intake batch + people + companies + relationships
        |
        +--> candidat ICB ----------------------------+
        |                                             |
        +--> screening réseau                         |
                  |                                   |
                  v                                   |
           file CREATE / REFRESH                      |
                  |                                   |
                  v                                   |
        recherche entreprise publique                 |
                  |                                   |
                  v                                   |
       enterprise demand profile                      |
                  |                                   |
      product snapshots + hard gates                  |
                  |                                   |
                  v                                   |
         company × product fit                        |
                  |                                   |
                  v                                   |
       person opportunity targeting                   |
                  |                                   |
                  v                                   |
      reach hypothesis + preuve/pilote                |
                                                      |
        études complètes et actuelles ----------------+
                  |
                  v
          consolidation sectorielle ICB
```

## Briques techniques et interactions

| Brique | Emplacement | Responsabilité | Entrées | Sorties et interaction suivante |
|---|---|---|---|---|
| Contrat agent | `AGENTS.md` | Fixer les frontières, la preuve et l’ordre des skills | Demande utilisateur | Route vers le réseau, la recherche entreprise ou le tunnel produit |
| Intake privé | `network-contact-intake`, `import_contacts.py` | Valider le TSV, préserver le brut, normaliser et attribuer des IDs | Fichier `Name / Job title / Company / Country` | Batch, personnes, entreprises et relations |
| Registre personnes | `data/private/network/people.jsonl` | Identité privée, relations et hypothèses de rôle | Intake | Alimente le ciblage post-fit uniquement |
| Registre entreprises | `data/private/network/companies.jsonl` | Identité stable, alias, pays observés, contacts, ICB, screening et étude | Intake, ICB, screening, orchestration | Pivot entre réseau et études |
| Registre relations | `data/private/network/relationships.jsonl` | Conserver titre, entreprise, pays, provenance et statut de validation | Intake | Alimente screening et ciblage sans prouver l’autorité |
| Taxonomie ICB | `data/taxonomies/icb_v5_2026.yaml` | Référentiel officiel 11 industries, 20 supersectors, 45 sectors | ICB Equity v5.0 LSEG, mars 2026 | Contraint et valide les codes de mapping |
| Mapping ICB | `enterprise-icb-mapping`, `map_companies_icb.py` | Produire un candidat de classification avec niveau et confiance | Entreprises + taxonomie + règles | Mapping candidat, pending ou hors périmètre; alimente rollups et screening |
| Screening réseau | `network-account-screening`, `screen_network_accounts.py` | Prioriser les entreprises à rechercher à partir de l’accès réseau | Entreprises, relations, ICB candidat | Tiers A–D; alimente la file d’études, jamais le product fit |
| Orchestration études | `network-study-orchestration`, `sync_study_queue.py` | Décider `create / refresh / ready / hold` et initialiser un volume borné | Registre entreprises, screening, études existantes | `study_queue.yaml`, puis dossiers sous `studies/` |
| Initialisation étude | `init_study.py` | Créer manifest, artefacts et snapshots produit immuables | Entreprise, `company_id`, catalogue | Étude au stade `enterprise_research` |
| Intelligence entreprise | Control tower + quatre skills spécialisées + `enterprise-demand-intelligence` | Établir stratégie, organisation, capacités, newsflow, maturité et gaps | Sources publiques datées | `05_enterprise_demand_profile.yaml`, sans produit |
| Catalogue produit | `product_catalog/`, `product-icp-intelligence` | Versionner problème, ICP, anti-ICP, preuves et hard gates d’une offre | Preuves produit | Profils canoniques et snapshots d’étude |
| Matching | `opportunity-fit-matching` | Croiser demande réelle et vérité produit; appliquer gates avant score | Profil entreprise + snapshots | `06_product_fit_matrix.yaml` |
| Ciblage personne | `person-opportunity-targeting`, `target_study_contacts.py` | Classer les contacts après le fit, sans le modifier | Match, personas produit, relations privées | `06b_contact_targets.yaml` avec IDs opaques |
| Reach et engagement | `engagement-pilot-design`, `build_reach_hypotheses.py` | Relier priorité, gap, preuve produit et question de validation | Fit, cibles, claims compte, preuves produit | `07_engagement_hypothesis.md` et `07b_reach_hypotheses.yaml` |
| Organisation et livrables | `tech-leadership-org-intelligence` | Produire organigramme analytique, influence map et DOCX | Preuves publiques de l’étude | Note qualifiée et système de décision |
| Consolidation sectorielle | `sector-intelligence-consolidation`, `build_sector_rollups.py` | Regrouper au moins trois études actuelles et complètes du même secteur | Profils compte + mapping ICB | Evidence pool `exploratory` avec candidats; `decision_grade` seulement si tous les mappings sont validés |
| Contrats | `contracts/` | Stabiliser les handoffs entre briques | Schémas 0.2 et 0.3 | Validations reproductibles |
| Validateurs | `validate_package.py`, `validate_study.py`, `validate_network.py`, `check_release.py` | Vérifier structure, versions, frontières, scores, gates, références, portabilité et confidentialité | Package, études, données privées, dépôt | Erreurs bloquantes avant milestone |
| Evals | `evals/` | Tester déclenchements, collisions et cas métier | Requêtes positives/négatives | Réduction des appels de mauvaise skill |
| Adaptateur LinkedIn futur | PRD, ADR et contrats différés | Valider la fraîcheur d’un contact déjà connu | Requête issue du ciblage post-fit | Preuve externe -> policy/merge gate; validation manuelle si indisponible |

## Frontières décisionnelles

1. Le screening réseau mesure une priorité de recherche, pas un besoin.
2. Le diagnostic entreprise établit une demande observable, sans connaître les offres.
3. Le matcher décide du fit entreprise–produit, sans choisir de personne.
4. Le ciblage personne intervient seulement après le fit.
5. Le reach reste bloqué si le rôle actuel, la priorité, le gap ou la preuve produit ne sont pas validés.
6. Le rollup sectoriel ne démarre pas avant trois études actuelles, complètes et comparables; un mapping candidat limite la sortie à `exploratory`.
7. LinkedIn reste optionnel, read-only et hors runtime avant les gates LI-G0 à LI-G3.

## État des sept priorités

| Priorité | Première version livrée | État actuel |
|---|---|---|
| 1. Intake du fichier de contacts | Skill, import déterministe, batch immuable et registres privés | Exécutée sur 1 308 lignes |
| 2. Liaison entreprises–secteurs ICB | Taxonomie v5.0, règles candidates, mapping et contrat | 272 candidats `N0`, 362 en attente, 28 hors périmètre probable |
| 3. ICP théorique du réseau | Screening product-agnostic A–D | 662 entreprises scorées; ne constitue pas une preuve de demande |
| 4. Orchestration des diagnostics | File `create / refresh / ready / hold` et application bornée | 136 créations proposées, aucune lancée automatiquement |
| 5. Ciblage des contacts après fit | Personas, ranking par rôle et validation de l'emploi courant | Implémentée et testée; requiert un match existant |
| 6. Reach et preuve commerciale | Hypothèses structurées et gates priorité/gap/preuve/rôle | Implémentée et testée; reste bloquée tant qu'un gate manque |
| 7. Consolidation sectorielle | Éligibilité, evidence pool et contrat de synthèse ICB | Implémentée et testée; aucun rollup réel éligible à ce stade |

## Architecture de fichiers

```text
project/
├── AGENTS.md
├── pyproject.toml                    configuration Python et dépendances
├── .gitlab-ci.yml                    gate de release en CI
├── contracts/                       interfaces v0.2 et v0.3
├── data/
│   ├── taxonomies/                  ICB officiel + règles candidates
│   └── private/                     données réseau ignorées par Git
│       ├── intake_batches/
│       ├── network/
│       └── sector_rollups/
├── evidence/product/                preuves produit
├── product_catalog/                 un YAML versionné par offre
├── studies/                         études entreprise datées
├── skills/                          responsabilités spécialisées
├── scripts/                         opérations déterministes
├── templates/                       gabarits d’étude
├── artifacts/                       modèles et états de cadrage
├── docs/                            architecture et positionnement
├── evals/                           tests de triggering/raisonnement
└── tests/                           tests d’intégration
```

## Résultat du premier intake

- 1 308 lignes valides, aucune rejetée;
- 1 308 personnes et relations;
- 662 identités d’entreprise conservatrices après normalisation minimale;
- 272 candidats ICB à valider, 28 entités probablement hors périmètre ICB, 362 mappings en attente;
- screening : 60 comptes A, 76 B, 213 C et 313 D;
- 136 études proposées en `create`, aucune lancée automatiquement;
- aucun rollup sectoriel éligible avant production d’au moins trois études complètes par secteur.

Les libellés d’entreprise restent au niveau fourni par le fichier. Le regroupement maison-mère, filiale, marque ou business unit nécessite une résolution d’entités supplémentaire et ne doit pas être forcé.

Les personnes sont désormais seedées par `nom normalisé + entreprise normalisée`. Cette clé est transitoire : une future identité externe vérifiée pourra relier plusieurs seeds via la couche de résolution, sans remplacer les `person_id` internes.
