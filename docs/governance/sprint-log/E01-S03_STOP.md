# STOP — Epic 01 / Sprint S03

## Objective

Add an append-only EventJournal and propagate correlation IDs.

## State

Tag `epic-01-s03-event-journal`; no merge to protected branches yet.

## Outputs

- Technical journal with hash chain, idempotency key and replay verification.
- Framework-neutral correlation context wired into HTTP middleware.

## Evidence

Concurrent 20-thread append, tamper detection, idempotency and correlation tests passed.

## Remaining

Domain-specific event emission is owned by later Epics; no dual business truth is introduced here.

## Commands to resume

```bash
python -m unittest tests.test_event_journal tests.test_artifact_store -v
```

## Risks / notes

Red-team changed the initial append design to one locked read-verify-append transaction.
