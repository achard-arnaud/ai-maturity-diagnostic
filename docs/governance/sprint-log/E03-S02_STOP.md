# STOP — Epic 03 / Sprint S02

## Objective

Ingestion adapters public/manual/import avec provenance. Stop condition:
"core sans intégration" (the core path works without any live external
integration).

## Outputs

- `app/signal_ingestion.py`: `ingest_public`, `ingest_manual`,
  `ingest_import`. Every adapter consumes already-obtained content
  (a URL + already-fetched text, an operator's note, pre-parsed rows) —
  none of them performs a live network call. Wiring an actual public
  fetch/premium connector behind `ingest_public` is deferred work per the
  Epic's own "sources premium/connecteurs" line, not this Sprint's job.
  Each adapter builds on S01's `signal_policy` (dedup key, demand-field
  guard) so ingestion and lifecycle never diverge on shape.
  - `ingest_public`: evidence_grade U1 / epistemic_status inference.
  - `ingest_manual`: evidence_grade U1 / epistemic_status hypothesis;
    source ref includes the operator so two operators noting the same
    event don't collide on dedup.
  - `ingest_import`: batch of rows, each needing `content` +
    `observed_at`; **a malformed row fails the whole batch** rather than
    silently skipping it — a partial import is never promoted as
    complete.
- `tests/test_signal_ingestion.py`: 13 tests — schema-valid output for
  each adapter, required-field failures, an explicit
  "unreachable/fake URL does not raise a network error" test (proving
  "core sans integration" directly), operator-scoped dedup, and
  whole-batch failure on one bad row.

## Evidence

`python -m unittest tests.test_signal_ingestion -v`: 13/13 pass.
