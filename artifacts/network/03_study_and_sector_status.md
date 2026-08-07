# File d’études et consolidation sectorielle

## File initiale

- `create` : 136 entreprises de tiers A ou B sans étude;
- `hold` : 526 entreprises;
- études appliquées automatiquement : 0.

L’application est volontairement bornée : `python scripts/sync_study_queue.py --apply --limit 5`.

## Consolidation sectorielle

Aucun secteur n’est actuellement éligible. Il faut au moins trois études du même secteur ICB, datant de moins de six mois, avec claims, capability gaps et confiance moyenne ou élevée.
