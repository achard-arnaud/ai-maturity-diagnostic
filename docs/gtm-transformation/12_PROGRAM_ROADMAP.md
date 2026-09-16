# Program Roadmap

## Programme retenu

| Epic | Capacité livrée vers `main` | Sprints | Dépendances |
|---|---|---:|---|
| E00 | gouvernance, baseline et CI Stop & Go fiables | 5 | — |
| E01 | plateforme transactionnelle réversible et runtime borné | 6 | E00 |
| E02 | graphe canonique personnes/entreprises/relations | 6 | E01 |
| E03 | Discover signal-based : signaux, listes, watchlists | 6 | E02 |
| E04 | Research product-blind et Company 360 gouverné | 7 | E02–E03 |
| E05 | Demand de premier rang et qualifiable | 6 | E04 |
| E06 | Product intelligence et snapshots immuables | 6 | E01 |
| E07 | Fit décisionnel explicable et reproductible | 6 | E05–E06 |
| E08 | Target plans, buying committees et currentness | 6 | E02, E07 |
| E09 | Reach work queue, séquences et touchpoints sûrs | 7 | E08 |
| E10 | Engagement entrant et boucle conversationnelle | 5 | E09 |
| E11 | Opportunity, proof, deal et land & scale | 6 | E10 |
| E12 | Replatform UX/navigation et retrait du legacy | 6 | E03–E11 |
| E13 | Insights, coûts, learning et amélioration gouvernée | 5 | E04–E12 |

Total : 83 Sprints. Ce nombre exprime des points d'arrêt, pas 83 cycles calendaires identiques. Plusieurs Sprints purement documentaires ou contractuels peuvent être courts ; aucun n'est mergé s'il ne laisse pas `dev` cohérent.

## Vagues

### Vague A — Make change safe

E00–E01. Aucun nouveau menu majeur. Résultat : CI sur dev, contrats, journal, writes atomiques, quotas/checkpoints et migrations réversibles.

### Vague B — Rebuild the intelligence spine

E02–E08. Résultat : de Signal à TargetPlan, objets stables, evidence-first et reproductibles.

### Vague C — Close the commercial loop

E09–E11. Résultat : touchpoints, réponses, opportunities, proof/deal/expansion.

### Vague D — Productize and learn

E12–E13. Résultat : UX cible, instrumentation, coûts et loopback gouverné.

## Chemin critique

`E00 → E01 → E02 → E04 → E05 → E07 → E08 → E09 → E10 → E11 → E12 → E13`, avec `E06` en parallèle de E02–E05 après E01, puis jonction en E07. E03 peut avancer après E02 mais doit précéder la finalisation E04.

## Releases utiles intermédiaires

- R1 après E01 : prototype exploitable et stoppable, architecture sûre.
- R2 après E07 : moteur d'intelligence account-demand-product-fit complet.
- R3 après E10 : boucle prospection/engagement opérationnelle.
- R4 après E13 : petite application GTM cohérente et apprenante.

## Registre des décisions à obtenir

1. Product catalog global, workspace-scoped ou modèle hybride publication/abonnement.
2. Premier canal d'engagement réellement intégré ; LinkedIn écriture reste interdite sans ADR/PRD.
3. Niveau d'autonomie des agents pour préparer, jamais envoyer, les actions.
4. Conditions de création d'Opportunity depuis l'engagement.
5. Rétention des preuves, conversations et données personnelles.
