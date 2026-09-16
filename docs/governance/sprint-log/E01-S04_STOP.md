# STOP — Epic 01 / Sprint S04

## Objective

Add durable run/checkpoint state and resume tokens.

## State

Tag `epic-01-s04-run-checkpoints`; later hardening is included in the Epic head.

## Outputs

- Prepared/started/checkpointed/completed/blocked/failed/cancelled state machine.
- Hashed resume tokens, optimistic updates and event correlation.

## Evidence

Checkpoint/resume, retryable failure, non-retryable refusal, cancellation and idempotent prepare tests passed.

## Remaining

Distributed workers and queues are deferred.

## Commands to resume

```bash
python -m unittest tests.test_run_manager -v
```

## Risks / notes

A repeated idempotent prepare retrieves the same run but does not re-disclose its raw resume token.
