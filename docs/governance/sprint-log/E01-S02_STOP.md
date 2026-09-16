# STOP — Epic 01 / Sprint S02

## Objective

Introduce ArtifactStore with atomic writes, locks and version checks; route existing application writers through it.

## State

Tag `epic-01-s02-artifact-store`; integration remains blocked by the Epic 00 branch gate.

## Outputs

- `app/artifact_store.py` centralizes scoped atomic YAML/text/JSONL writes.
- Demand, catalog, promotion, reach and blocker-action writers use the façade.

## Evidence

64 focused and legacy writer tests passed; crash, stale-version and 20-thread append cases passed.

## Remaining

Distributed/multi-instance locking is deferred.

## Commands to resume

```bash
python -m unittest tests.test_artifact_store tests.test_demand_catalog tests.test_catalog_harvest tests.test_catalog_promotion tests.test_reach_matchmaking tests.test_blocker_actions -v
```

## Risks / notes

Lock files are intentionally local and short-lived; stale locks are reclaimable after 120 seconds.
