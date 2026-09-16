# Epic 01 — Acceptance Record

## Sprints closed

- S01 — `epic-01-s01-catalog-ownership`: ADR-008 and executable ownership contract.
- S02 — `epic-01-s02-artifact-store`: atomic/version-aware ArtifactStore and legacy writer façade.
- S03 — `epic-01-s03-event-journal`: correlated, idempotent and hash-chained platform journal.
- S04 — `epic-01-s04-run-checkpoints`: durable run state, checkpoints, cancellation and resume tokens.
- S05 — `epic-01-s05-budget-quota`: budget envelopes, cache keys and bounded retry/degraded modes.
- S06 — `epic-01-s06-migrator`: dry-run, hash manifest, progress record and safe rollback.

The branch remains an isolated release candidate until Epic 00 is present in both `dev` and `main` and CI runs on the remote branch.

## Gate checklist

- [x] All six mandatory Sprints implemented and tagged; deferred items explicit.
- [ ] Full release gate green in GitHub CI on the Epic branch.
- [ ] E2E gate green or only documented expected GAP skips.
- [x] Invariants re-checked: file artifacts remain canonical; runtime/event stores do not recompute business truth; workspace roots remain explicit; hard gates untouched.
- [x] Migration and rollback rehearsed in `tests/test_workspace_migrator.py` including modified-destination refusal.
- [x] Traceability matrix updated.
- [x] Known limitations published below.

## Local verification

- 305 tests passed under `unittest discover`.
- 3 collection errors are environment-only missing dependencies: `starlette` for auth/server suites and `jsonschema` for LinkedIn design validation.
- 22 focused E01 tests passed after the final red-team corrections.
- `compileall` and `git diff --check` passed.

## Known limitations

- `ArtifactStore` is process/file-lock based and targets the current single-instance runtime; distributed locking is deferred.
- The catalog projection/overlay read model belongs to Epic 06; Epic 01 fixes ownership and persistence policy only.
- EventJournal is a technical history, not an event-sourced replacement for canonical business artifacts.
- Budgets are local workspace ledgers; provider reconciliation and shared distributed quotas are deferred.
- Migration copies `studies`, `data/private` and `artifacts`; `product_catalog` is explicitly excluded by ADR-008.
- Full release/E2E results depend on remote CI because package installation is blocked in this execution environment.

## Go/No-Go

`NO-GO` for `dev`/`main` integration until both conditions are met: Epic 00 is fully contained in `dev` and `main`; remote release/E2E gates are reviewed. Code candidate itself is complete.
