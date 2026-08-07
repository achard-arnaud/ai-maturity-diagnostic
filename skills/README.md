# Catalogue des skills

## Intelligence de stratégie IA

| Skill | Rôle | Artefact principal |
|---|---|---|
| `ai-strategy-control-tower` | Cadrage, orchestration, preuve et synthèse | `00`, `01`, `01b`, `06`–`08` |
| `corporate-ai-strategy-intelligence` | Priorités corporate et rôle réel de l’IA | `02` |
| `tech-leadership-org-intelligence` | Organisation, pouvoirs, RACI et influence | `03`, `03b`, `03c` |
| `ai-hiring-workspace-intelligence` | Modèle opératoire visible par le recrutement | `04` |
| `ai-newsflow-sourcing-intelligence` | Momentum et faire/acheter/s’allier | `05` |

## Tunnel de qualification v0.2

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `qualification-tunnel-router` | Router et vérifier les handoffs | Prochaine skill |
| `enterprise-demand-intelligence` | Qualifier le compte sans connaître les offres | `05_enterprise_demand_profile.yaml` |
| `product-icp-intelligence` | Versionner la vérité d’une offre sans compte | `product_catalog/OFFER-*.yaml` |
| `opportunity-fit-matching` | Croiser les deux profils sans recherche fraîche | `06_product_fit_matrix.yaml` |
| `engagement-pilot-design` | Transformer un match en preuve falsifiable | `07_engagement_hypothesis.md` |

Chaque package contient un `SKILL.md`, des métadonnées `agents/openai.yaml` et seulement les références méthodologiques nécessaires. Les faits produit restent dans `product_catalog/`; les faits compte restent dans `studies/`.

## Couche réseau v0.3

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `network-contact-intake` | Import privé, IDs et relations | Registres `people`, `companies`, `relationships` |
| `enterprise-icb-mapping` | Candidat ICB fondé sur l’activité | `company_icb_mappings.jsonl` |
| `network-account-screening` | Priorité de recherche product-agnostic | `account_screening.jsonl` |
| `network-study-orchestration` | Cycle `create/refresh/ready/hold` | `study_queue.yaml` |
| `person-opportunity-targeting` | Sélection de contacts après fit | `06b_contact_targets.yaml` |
| `sector-intelligence-consolidation` | Synthèse de trois études comparables ou plus | `sector_rollups/ICB-*.yaml` |

`engagement-pilot-design` transforme ensuite les cibles et le fit en hypothèses de reach ou de preuve, sans inventer d’autorité ni de besoin.

## Intelligence exécutive et candidatures v0.4

| Skill | Responsabilité exclusive | Sortie |
|---|---|---|
| `business-intelligence-nice` | Recherche, preuve, analyse et recommandation Sarah-Pro | Contenu décisionnel structuré et gelé |
| `application-nice` | Qualification d’opportunité et candidature, après confirmation François-Pro ou Sarah-Pro | Verdict, narratif et dossier persona-spécifique |
| `nice-output-engine` | Mise en page, rendu HTML/PDF/PNG et QA visuelle, sans analyse métier | Brief, benchmark, business note ou application pack |

Le flux impose une séparation nette entre le fond et la forme : les skills fonctionnelles établissent les vérités, les preuves et la recommandation, puis `nice-output-engine` rend le contenu gelé. `application-nice` partage uniquement un système opératoire ; ses sources, exemples, règles de narration et thèmes restent séparés par persona.

Le dépôt public contient le code, les contrats, les méthodes et les politiques de templates. Les CV, coordonnées, transcriptions et dossiers de candidature privés sont volontairement exclus et doivent être fournis dans l’environnement d’exécution selon `assets/private-assets.manifest.example.json`.
