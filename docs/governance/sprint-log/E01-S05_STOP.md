# STOP — Epic 01 / Sprint S05

## Objective

Add budget envelopes, quotas, cache keys, retry/backoff and degraded mode.

## State

Tag `epic-01-s05-budget-quota`; no external provider dependency.

## Outputs

- Atomic workspace usage ledger with 80% checkpoint and 100% stop signals.
- Cache key covers provider/model/prompt/policy/payload.
- Retry policy honors Retry-After, timeouts, jitter and attempt caps.

## Evidence

Budget stop, concurrency, 429, timeout, non-retryable and cache identity tests passed.

## Remaining

Provider billing reconciliation and organization-wide quotas are deferred.

## Commands to resume

```bash
python -m unittest tests.test_execution_policy -v
```

## Risks / notes

Units are provider-neutral by design; adapters must translate real billing into `cost_units`.
