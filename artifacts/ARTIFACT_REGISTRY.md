# Registre canonique des artefacts

| ID | Artefact | Owner principal | Entrées | Sortie / porte de qualité |
|---|---|---|---|---|
| 00 | `00_intake.md` | Tour de contrôle | Demande, contraintes | Décision, périmètre et date de coupure fixés |
| 01 | `01_context_snapshot.md` | Tour de contrôle | Cadrage initial | Hypothèses falsifiables et priorités de recherche |
| 01b | `01b_evidence_ledger.md` | Toutes les skills | Toute source ou proposition | Source IDs et claim IDs uniques, conflits conservés |
| 02 | `02_corporate_strategy.md` | Corporate | Sources stratégiques | Priorités financées et rôle IA segmenté |
| 03 | `03_leadership_signals.md` | Leadership | Gouvernance, profils, nominations | Personnes, mandats et modèle organisationnel |
| 03b | `03b_org_graphs.md` | Leadership | Relations tracées | Graphes avec liens confirmés/inférés et traçabilité |
| 03c | `03c_decision_system.md` | Leadership | Pouvoirs, décisions, objectif | RACI, influence map, ordre de contact, inconnues |
| 04 | `04_hiring_workspace_intelligence.md` | Hiring | Corpus dédupliqué | Modèle opératoire, capacité et biais |
| 05 | `05_newsflow_make_or_buy.md` | Newsflow | Chronologie dédupliquée | Momentum et sourcing par couche |
| 06 | `06_governance_maturity_assessment.md` | Tour de contrôle | `02` à `05` | Verdict de gouvernance et maturité étayé |
| 07 | `07_contradictions_and_gaps.md` | Tour de contrôle | Registre complet | Contradictions, scénarios et preuves discriminantes |
| 08 | `08_final_synthesis.md` | Tour de contrôle | `06`, `07`, ledger | Réponse décisionnelle traçable |

## Règles de dépendance

- `01b` est la source de vérité des références ; les autres artefacts citent ses IDs.
- `06` ne crée pas de faits nouveaux : il consolide `02` à `05`.
- `08` ne supprime aucune incertitude encore ouverte dans `07`.
- Un graphe sans table de traçabilité n’est pas livrable.
- Un niveau de maturité ne peut dépasser les preuves de production, réplication et adoption consignées.

## Artefacts du tunnel de qualification v0.2

Ces fichiers vivent dans `studies/<entreprise>-<YYYYMMDD>/` et ne remplacent pas les artefacts narratifs ci-dessus.

| ID | Artefact | Owner | Porte de qualité |
|---|---|---|---|
| 00 | `00_manifest.yaml` | Init / routeur | Versions, candidats et snapshots tracés |
| 01–04 | Fichiers d’évidence YAML | Enterprise demand | Sources et claims product-agnostic |
| 05 | `05_enterprise_demand_profile.yaml` | Enterprise demand | Aucun champ de recommandation produit |
| 06 | `06_product_fit_matrix.yaml` | Opportunity matching | Gates avant score, snapshots immuables |
| 07 | `07_engagement_hypothesis.md` | Engagement design | Baseline, KPI, guardrails et falsificateur |
| 08 | `08_validation_log.yaml` | Toutes les étapes | Événements et mises à jour versionnés |
| 06b | `06b_contact_targets.yaml` | Person targeting | Personnes classées seulement après product fit |
| 07b | `07b_reach_hypotheses.yaml` | Engagement design | Priorité + gap + preuve + question, ou statut bloqué |

## Artefacts réseau privés

| Artefact | Owner | Fonction |
|---|---|---|
| `intake_batches/<id>/manifest.yaml` | Contact intake | Provenance, checksum, schéma et limites |
| `network/people.jsonl` | Contact intake | Identités privées et hypothèses de rôle |
| `network/companies.jsonl` | Contact intake / orchestration | Pivot entreprise entre réseau et études |
| `network/relationships.jsonl` | Contact intake | Liens personne–entreprise non datés à valider |
| `network/company_icb_mappings.jsonl` | ICB mapping | Branche candidate, niveau, confiance et statut |
| `network/account_screening.jsonl` | Account screening | Priorité de recherche sans produit |
| `network/study_queue.yaml` | Study orchestration | Actions `create/refresh/ready/hold` |
| `sector_rollups/ICB-*.yaml` | Sector consolidation | Evidence pool puis synthèse inter-comptes |

## Artefacts LinkedIn différés

Ces artefacts décrivent une option future et ne rendent aucun connecteur opérationnel.

| Artefact | Owner futur | Fonction / gate |
|---|---|---|
| `linkedin_prd_traceability.yaml` | Mainteneur architecture | Relier LI-FR-001..015 à leurs contrats et vérifications |
| `TODO_linkedin_plugin.yaml` | Product owner / privacy / admin | Conserver LI-G0..LI-G6 et empêcher un démarrage prématuré |
| `role_validation_request` | Person targeting | Formuler une question ciblée sur un contact canonique |
| `linkedin_connector_evidence` | Adaptateur futur | Normaliser une preuve read-only sans modifier le canon |
| `external_identity_mapping` | Identity merge gate | Conserver un alias fournisseur privé |
| `relationship_observation` | Identity merge gate | Produire une observation post-merge traçable |
| `private_integration_audit` | Adaptateur futur | Auditer capacité, résultat et policy sans payload sensible |
