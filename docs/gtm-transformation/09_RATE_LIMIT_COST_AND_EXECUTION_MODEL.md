# Rate Limit, Cost and Execution Model

## Objectif

Rendre la consommation IA compatible avec des forfaits limités et un développement Stop & Go, sans dégrader la traçabilité.

## Budget envelope

Chaque run déclare : provider/model, plafond appels/tokens/coût/temps, priorité, cache policy, fallback autorisé, checkpoint frequency et condition d'arrêt. Les budgets existent aux niveaux workspace, workflow, Epic de test et run.

## Execution lanes

- Deterministic : parsing, validation, hash, migration, projection ; aucun LLM.
- Light : classification/résumé borné sur corpus déjà acquis.
- Heavy : recherche ou synthèse multi-source explicitement autorisée.
- Human : validation, décision sensible, saisie ou levée de blocker.

## Politique

1. Réutiliser artefacts/sources/cache avant acquisition.
2. Dédupliquer par input hash + version de prompt/modèle/policy.
3. Réserver le heavy aux gaps décisionnels susceptibles de changer le verdict.
4. Sauvegarder un checkpoint après chaque lot atomique.
5. Backoff/jitter et respect de `Retry-After`; aucun retry infini.
6. Fallback modèle/provider uniquement si le contrat de qualité l'autorise.
7. Exposer coût marginal attendu avant relance depuis un resolver.

## Degraded mode

Si quota épuisé : lecture, navigation, décisions déjà calculées et tâches humaines restent disponibles. Les runs en attente affichent `blocked_rate_limit`, prochaine fenêtre et option de reprise ; aucune sortie partielle n'est promue.
