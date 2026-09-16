# Information Architecture

## Navigation cible

| Espace | Job | Objets dominants |
|---|---|---|
| Home | voir priorités et next best actions | queues, blockers, SLAs |
| Discover | trouver signaux, personnes et entreprises | Signal, Person, Company, List |
| Research | comprendre le compte sans biais produit | ResearchCase, Claim, Demand |
| Fit | décider de l'adéquation d'une version d'offre | Snapshot, FitAssessment |
| Targets | construire le buying committee et le chemin relationnel | TargetPlan, Role, Relationship |
| Reach | exécuter une cadence approuvée | Sequence, Task, Touchpoint |
| Engagement | traiter réponses, meetings et objections | EngagementEvent, Conversation |
| Pipeline | piloter leads, opportunities, proofs et deals | Opportunity, Proof, Deal |
| Insights | comprendre funnel, coûts, qualité et apprentissages | Metrics, Cohorts, Learning |
| Admin | administrer workspace, politiques, intégrations, quotas | Membership, Policy, Connector |

## Règles UX

- Les files de travail sont les homepages d'espace ; les objets restent accessibles par deep link.
- Une vue Account 360 compose les contextes mais ne fusionne pas leurs vérités.
- Les badges indiquent `fact/inference/hypothesis/unknown`, freshness, blockers et version.
- Une action bloquée montre le resolver au même endroit.
- `Products`, `Snapshots`, `Sequences`, `Tasks`, `Lists` et `Sources` sont sous-navigation ou vues contextuelles.
- Mobile/tablette : consultation, capture de note et résolution simple ; écrans d'administration lourds restent desktop-first.

## Migration de navigation

La coque cible cohabite d'abord avec les panneaux legacy derrière des routes stables. Les anciens boutons deviennent des redirects/toggles instrumentés ; ils ne sont supprimés qu'après parité E2E et absence d'usage sur une fenêtre décidée.
