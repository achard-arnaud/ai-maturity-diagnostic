# Audit AS-IS et Gap Map

## Base auditée

- Dépôt : `achard-arnaud/ai-maturity-diagnostic`
- Révision : `main@5468e57`, 16 septembre 2026
- Runtime : Python/FastAPI, frontend HTML/CSS/JS, artefacts YAML/Markdown, SQLite pour le contrôle auth/runtime.
- CI : `.github/workflows/qa.yml` appelle `scripts/check_release.py` sur PR et push `main`/`agent/**`; GitLab appelle la même logique.

La release gate n'a pas pu être rejouée dans l'environnement d'analyse faute de dépendance `jsonschema`; ce n'est pas un échec produit observé. L'état « CI verte » doit être récupéré depuis GitHub ou reproduit dans un environnement installé avant Epic 00.

## Actifs réels à préserver

| Axe | Actifs présents dans HEAD |
|---|---|
| Domaine | séparation network/enterprise/product/commercial/learning ; hard gates ; blockers/resolvers |
| Runtime | FastAPI, sessions, workspace, memberships/RBAC, audit, OIDC/local dev |
| Métier | réseau, Account 360, demande, catalogue, promotion, qualification, UC graph, reach, campagnes, kanban, nudging |
| Mémoire | artefacts versionnés, contrats YAML, skills spécialisées, manifests et études |
| QA | tests unitaires/intégration, 3 parcours Playwright, couverture annoncée ≥80 %, lint/validation/package/privacy |
| Sécurité | workspace path resolver, contrôle de rôles, sessions serveur, refus auth-disabled hors loopback |

## Gaps structurants

| ID | Gap | Impact | Epic propriétaire |
|---|---|---|---|
| G01 | North Star, vocabulaire et autorité documentaire non alignés | décisions contradictoires | E00 |
| G02 | CI push n'inclut pas `dev`; E2E hors release gate Python | Stop & Go non garanti | E00 |
| G03 | Persistance fichiers distribuée, ownership produit/workspace incomplètement tranché | concurrence/migration | E01 |
| G04 | Person/Company/Relationship/Signal sans graphe canonique complet ni temporalité uniforme | Discover fragile | E02 |
| G05 | Signals/watchlists/saved searches insuffisants comme objets | screening encore « liste » | E03 |
| G06 | Research queue, dossier Company 360 et claims product-blind non unifiés | contamination/duplication | E04 |
| G07 | Demand existe surtout comme artefact agrégé, pas comme lifecycle CRM robuste | qualification opaque | E05 |
| G08 | Version/snapshot produit, promotion et ownership à consolider | fit non reproductible | E06 |
| G09 | FitAssessment n'est pas encore un read/write model décisionnel complet | score trop central | E07 |
| G10 | Cible personne agrégée par study, sans person route/profil stable | buying committee faible | E08 |
| G11 | Reach et Campaign existent mais queue/touchpoints/cadence/idempotence restent fragmentés | exécution peu sûre | E09 |
| G12 | Engagement entrant n'est pas séparé de l'activité sortante | absence de vraie boucle commerciale | E10 |
| G13 | Lead/Opportunity/Deal/proof/land-scale ne forment pas un lifecycle canonique | pipeline incomplet | E11 |
| G14 | Navigation legacy par modules techniques | coût cognitif élevé | E12 |
| G15 | Learning loop, métriques, coûts IA, evals et propositions d'amélioration dispersés | amélioration non pilotée | E13 |

## Dette documentaire détectée

- `AGENTS.md` v0.3 contient des extensions v0.7 et des frontières de navigation devenues historiques.
- `TECHNICAL_BASELINE_v0_8.md` décrit comme « current » plusieurs gaps désormais partiellement implémentés.
- PRD v0.5/v0.6/v0.7/v0.8 s'empilent sans registre de supersession.
- Les branches documentaires `red-team-side-story` et `prospection-principes` portent des concepts utiles mais non mergés ; elles sont inputs, pas vérité de `main`.
- Deux pièces jointes de benchmark sont identiques : elles constituent une seule source logique.

## Conclusion

Le repo ne nécessite pas une réécriture. Il nécessite une strangler transformation : figer les contrats, enrichir le modèle dans l'ordre causal, exposer des projections API stables, puis remplacer progressivement la navigation legacy.
