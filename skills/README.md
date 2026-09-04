# Catalogue des skills

## Intelligence de stratégie IA

| Skill | Rôle | Artefact principal |
|---|---|---|
| `ai-strategy-control-tower` | Cadrage, orchestration, preuve et synthèse | `00`, `01`, `01b`, `06`–`08` |
| `corporate-ai-strategy-intelligence` | Priorités corporate et rôle réel de l’IA | `02` |
| `tech-leadership-org-intelligence` | Organisation, pouvoirs, RACI et influence | `03`, `03b`, `03c` |
| `ai-hiring-workspace-intelligence` | Modèle opératoire visible par le recrutement | `04` |
| `ai-newsflow-sourcing-intelligence` | Momentum et faire/acheter/s’allier | `05` |

## Tunnel de qualification

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `qualification-tunnel-router` | Router, vérifier les handoffs et résoudre les blockers vers leur prérequis | Prochaine skill / resolver |
| `enterprise-demand-intelligence` | Qualifier le compte sans connaître les offres | `05_enterprise_demand_profile.yaml` |
| `product-icp-intelligence` | Versionner la vérité d’une offre sans compte | `product_catalog/OFFER-*.yaml` |
| `opportunity-fit-matching` | Croiser demande et profils produit sans recherche fraîche | `06_product_fit_matrix.yaml` |
| `person-opportunity-targeting` | Sélectionner les premiers contacts après fit valide | `06b_contact_targets.yaml` |
| `iterative-reach-matchmaking` | Organiser promoteurs, prescripteurs, terrain, sponsors techniques et veto en première/seconde vague | `06c_reach_strategy.yaml` |
| `engagement-pilot-design` | Transformer fit + reach en preuve ou discovery falsifiable | `07_engagement_hypothesis.md` |

Les faits produit restent dans `product_catalog/`; les faits compte et personnes restent dans leurs artefacts propriétaires. Le newsflow peut modifier le `why_now` du reach, jamais le fit.

## Couche réseau

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `network-contact-intake` | Import privé, IDs et relations | Registres `people`, `companies`, `relationships` |
| `enterprise-icb-mapping` | Candidat ICB fondé sur l’activité | `company_icb_mappings.jsonl` |
| `network-account-screening` | Priorité de recherche product-agnostic | `account_screening.jsonl` |
| `network-study-orchestration` | Cycle `create/refresh/ready/hold` | `study_queue.yaml` |
| `sector-intelligence-consolidation` | Synthèse de trois études comparables ou plus | `sector_rollups/ICB-*.yaml` |

## Catalogue de demande, chaînes de valeur et patrimoine UC

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `enterprise-use-case-intelligence` | Recenser et maintenir les use cases d’une entreprise à partir de ses preuves, sans offre | `05b_use_case_inventory.yaml` |
| `enterprise-value-chain-causal-analysis` | Décomposer un UC canonique dans sa chaîne opérationnelle avec Porter et ses causes avec Ishikawa | `05c_value_chain_causal_map.yaml` |
| `sector-intelligence-consolidation` | Consolider preuves et use cases de >=3 études d’un même secteur ICB | `data/private/sector_rollups/ICB-*.yaml` |
| `use-case-nudging` | Productivisation, upsell par dépendance et cross-sell feedback-backed depuis le seul inventaire entreprise | `09_use_case_nudges.yaml` |

Le patrimoine UC utilise une vue graphe **dérivée**, pas une nouvelle skill ni une nouvelle vérité. Les liens `depends_on`, `enables`, `variant_of`, `shares_asset`, `same_outcome`, `value_chain_neighbor`, `causal_neighbor` et `similar_pattern` conservent scope, basis, confiance et provenance. Une similarité sectorielle ne prouve jamais qu’un compte possède le use case.

La hiérarchie de navigation reste `ICB -> secteur -> entreprises -> études -> use cases`. ICB sert à naviguer et benchmarker ; il ne prouve jamais un besoin. Porter/Ishikawa peuvent faire émerger un workflow adjacent au statut d’hypothèse, mais seul `enterprise-use-case-intelligence` peut le canonicaliser avec une preuve entreprise.

## Handoff reach v0.7

```text
05 demand
-> 05b use cases
-> 05c value-chain / causal map (optionnel pour expliquer le workflow)
-> immutable product snapshots
-> 06 product fit
-> 06b contact targets
-> 06c iterative reach
-> 07 engagement / pilot
```

`iterative-reach-matchmaking` ne remplace ni le matching ni l’organigramme. Il orchestre les preuves déjà acquises et peut router en arrière vers `tech-leadership-org-intelligence` ou la validation de rôle lorsqu’une seconde vague de personnes est nécessaire.

## Intelligence exécutive et candidatures v0.4

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `business-intelligence-nice` | Recherche, preuve, analyse et recommandation Sarah-Pro | Contenu décisionnel structuré et gelé |
| `application-nice` | Qualification d’opportunité et candidature, après confirmation François-Pro ou Sarah-Pro | Verdict, narratif et dossier persona-spécifique |
| `nice-output-engine` | Mise en page, rendu HTML/PDF/PNG et QA visuelle, sans analyse métier | Brief, benchmark, business note ou application pack |

Le flux impose une séparation nette entre le fond et la forme : les skills fonctionnelles établissent les vérités, les preuves et la recommandation, puis `nice-output-engine` rend le contenu gelé. `application-nice` partage uniquement un système opératoire ; ses sources, exemples, règles de narration et thèmes restent séparés par persona.

Le dépôt public contient le code, les contrats, les méthodes et les politiques de templates. Les CV, coordonnées, transcriptions et dossiers de candidature privés sont volontairement exclus et doivent être fournis dans l’environnement d’exécution selon `assets/private-assets.manifest.example.json`.


## Executive entity briefing v0.9

`executive-entity-briefing` owns compact meeting/networking briefs that combine a named external company, its material products/frameworks/methodologies and a named person.

It writes three audience-neutral canonical atom families — company, external product and person — then a derived `executive_entity_brief`. A `core|material` external product is protected by a retention gate and must appear in page 2 `product_spotlights`.

This external-product intelligence contract is intentionally separate from `product_catalog/`: target-company offerings never become our own canonical offer truth. Persona-specific relevance for François-Pro or Sarah-Pro exists only in the assembly layer.
