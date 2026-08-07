# Migration v0 -> v0.2

| Artefact v0 | Diagnostic | Cible v0.2 |
|---|---|---|
| `01_Astraforge_fiche_produit_complete.md` | Mélange vérité produit, pitch, ICP, pilote et inconnues | Profil offre + pitch + registre de preuves |
| `09_product_offer_catalog.md` | Quatre offres monolithiques | `product_catalog/index.yaml` + un YAML par offre |
| `10_opportunity_matching.md` | Catalogue copié dans l’étude | `06_product_fit_matrix.yaml` + snapshots immuables |
| `11_engagement_hypothesis.md` | Trop proche du matcher | `engagement-pilot-design` |
| `05_claim_registry_and_artifact_contract.md` | Taxonomie incohérente | `contracts/claim.schema.yaml` + contrats de handoff |
| `06_v0_acceptance_tests.md` | Tests de raisonnement sans triggering | `evals/trigger_*` + `reasoning_cases.yaml` |
| `company-demand-lead-intelligence` | Orientée lead et matching | `enterprise-demand-intelligence` product-agnostic |
| `product-offer-matching-intelligence` | Responsabilité trop large | Product ICP + matching + pilote |
| `init_study.py` | Template manifest absent | Script v0.2 + snapshots |
| `validate_study.py` | Validation Markdown superficielle | Validation YAML, versions et frontières |

## Compatibilité conceptuelle

Conserver les lentilles stratégie corporate, organisation et pouvoir, recrutement et capacités, newsflow et momentum. Les utiliser pour établir la demande, jamais le fit produit.

## Numérotation des études

```text
00_manifest.yaml
01_strategy_evidence.yaml
02_organization_evidence.yaml
03_capability_signals.yaml
04_newsflow_evidence.yaml
05_enterprise_demand_profile.yaml
06_product_fit_matrix.yaml
07_engagement_hypothesis.md
08_validation_log.yaml
inputs/product_snapshots/
sources/
```
