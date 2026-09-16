# Domain and Truth Model

## Bounded contexts

| Contexte | Vérité possédée | N'en déduit jamais seul |
|---|---|---|
| Network | identité, relation, provenance, currentness | demande ou autorité |
| Market Signals | signal observé, source, date, watchlist | besoin confirmé |
| Account Intelligence | claims, dossier, maturité, initiatives | offre recommandée |
| Demand | problème, impact, timing, sponsor/budget connus ou inconnus | adéquation produit |
| Product Intelligence | produit, version, snapshot, preuves et exclusions | besoin d'un compte |
| Fit | gates, coverage, gaps, alternatives, verdict | cible personne |
| Targeting | rôles, influence, warm paths, currentness | engagement réel |
| Reach | plan, message, canal, tâche, touchpoint sortant | réaction du prospect |
| Engagement | réponse, meeting, objection, sentiment, consentement | vérité produit |
| Opportunity | qualification commerciale, proof, deal, expansion | réécriture des preuves amont |
| Learning | métriques, feedback, propositions | mutation automatique des contrats |

## Types de vérité

1. Observation : élément daté et sourcé.
2. Fait validé : observation acceptée selon politique.
3. Inférence : conclusion explicable à partir de claims.
4. Hypothèse : assertion à valider avec propriétaire et échéance.
5. Décision : verdict pris par un acteur/règle sur une version d'inputs.
6. Projection : vue recalculable, jamais source primaire.

## Règles anti-contamination

- Le screening priorise la recherche, pas le fit.
- Le catalogue produit ne suggère pas de « douleur » dans la recherche entreprise.
- La demande peut rester implicite/hypothétique mais son statut est visible.
- Un snapshot publié est immuable ; toute correction crée une version/supersession.
- Un fit est invalidé ou marqué stale quand un input référencé change.
- Un titre de poste ne prouve ni autorité ni rôle dans le buying committee.
- Un touchpoint envoyé n'est pas un engagement.
- Un learning item doit citer cohortes, limites et artefacts sources.

## Shared kernel minimal

`WorkspaceRef`, `EntityRef`, `ArtifactRef`, `EvidenceRef`, `ActorRef`, `SourceRef`, `VersionRef`, `DecisionRef`, `PolicyRef`, `EventRef`, avec IDs stables, timestamps, provenance et version de schéma.
