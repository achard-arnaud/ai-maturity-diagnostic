# STOP — Epic 01 / Sprint S06

## Objective

Add dry-run/hash/report/rollback workspace migration.

## State

Tag `epic-01-s06-migrator`; release candidate only.

## Outputs

- Planner inventories studies/private data/artifacts and excludes product catalog.
- Apply verifies all sources first, persists progress after each copy and writes a rollback manifest.
- Rollback refuses to remove modified destinations.

## Evidence

Copy/rollback, changed-source, partial-copy prevention and changed-destination refusal tests passed.

## Remaining

Production migration execution requires an explicit operator decision and backup policy.

## Commands to resume

```bash
python scripts/migrate_workspace.py <workspace-id>
python -m unittest tests.test_workspace_migrator -v
```

## Risks / notes

Apply is copy-first and preserves legacy sources; rollback removes only byte-identical destinations created by the migration.
