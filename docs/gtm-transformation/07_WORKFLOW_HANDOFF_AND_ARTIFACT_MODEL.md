# Workflow, Handoff and Artifact Model

## Handoff envelope

Chaque handoff persistant contient : `handoff_id`, owner source/destination, object refs et versions, input hashes, preuves, gates, blockers, budget consommé/restant, run status, outputs, timestamps, actor et resume token.

## Workflow states

`prepared → started → checkpointed → completed | blocked | failed | cancelled`.

Un retry réutilise la même idempotency key ou crée une nouvelle tentative rattachée. Un arrêt rate-limit devient `checkpointed` ou `blocked`, jamais un artefact partiellement déclaré complet.

## Convention d'artefacts

```text
workspaces/<ws>/
  entities/
  studies/<research_case_id>/
  products/<product_id>/versions/<version_id>/
  fits/<fit_id>/
  targets/<target_plan_id>/
  reach/<sequence_id>/
  engagement/<conversation_id>/
  opportunities/<opportunity_id>/
  events/YYYY/MM/*.jsonl
  runtime/checkpoints/
```

La migration part des chemins historiques et produit un mapping/manifest ; elle n'impose pas immédiatement ce layout physique si les adaptateurs peuvent fournir les mêmes contrats.

## Propriétaires

Une seule capability écrit chaque vérité. Les orchestrateurs routent et vérifient ; ils ne recalculent pas silencieusement les sorties d'une skill propriétaire. Les side stories sont des branches d'enquête liées au tronc, avec budget et décision `merge/retain/defer/reject`.
