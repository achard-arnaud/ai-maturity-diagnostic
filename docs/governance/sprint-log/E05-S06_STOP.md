# STOP — Epic 05 / Sprint S06

## Objective

Migration/reconciliation des artefacts legacy. Stop condition: "rollback
validé" (rollback validated) -- hashes/counts/N-1.

## Outputs

- `app/demand_migrator.py`: `DemandMigrator(repo_root,
  workspace_id).plan/apply/rollback`, same dry-run/apply/rollback/
  manifest shape as `network_v1_migrator`/`workspace_migrator`. A 1:1
  backfill: each legacy `studies/*/05_enterprise_demand_profile.yaml`
  (found via its `00_manifest.yaml`) maps to exactly one
  `CanonicalDemandV1` via S01's `map_from_enterprise_profile` -- never a
  merge across studies.
  - `plan()`: deterministic `demand_id` derived from `study_id`'s hash
    (re-running produces the same ids); each item carries a
    `content_hash` (sha256 of the source profile's bytes) for drift
    detection. Legacy files are only ever read.
  - `apply(plan)`: creates each demand via S04's `create_demand`;
    re-applying an already-migrated study is a no-op (skipped, not
    duplicated or raised) -- migration is idempotent on rerun. Writes a
    manifest recording `applied_demand_ids`, counts, and
    `rollback_status: "available"`.
  - `rollback(manifest_path)`: removes *exactly* the `demand_id`s this
    manifest applied, from the raw JSONL store -- nothing else. Validated
    by count: N (post-apply) minus the applied set equals N-1 (whatever
    existed before this migration, including demands from other
    sources), never more, never less.
- `tests/test_demand_migrator.py`: 10 tests -- plan finds all studies and
  is deterministic across calls; every item carries a well-formed content
  hash; apply creates demands + a manifest; the mapped problem statement
  round-trips faithfully; apply is idempotent on rerun (no duplicates);
  a plan from a different workspace is rejected; rollback removes exactly
  the applied count (the core "rollback validé" property) and rejects a
  manifest from a different workspace; the N-1 gold case: a
  manually-created demand outside the migration survives rollback
  untouched while the migration's own 2 are removed.

## Evidence

`python -m unittest tests.test_demand_migrator -v`: 10/10 pass.
Full `python scripts/check_release.py`: 0 errors.

## Epic 05 status

All 6 Sprints closed (S01 Demand v1 schema + legacy mapping; S02
lifecycle + qualification checklist/gates; S03 Claim/Evidence links,
confidence and contradiction; S04 queue/API/optimistic edit; S05 dossier,
resolver, detect->qualify E2E; S06 migration/reconciliation with
validated rollback). Epic acceptance (a Demand can be detected,
qualified, rejected, reopened or marked stale independently of the
product, with no automated match) is verified across S01-S06's tests:
S01's schema structurally excludes every product/fit field; S02's
qualify_demand is the sole path to "qualified" and always gated;
S06's migrator never touches legacy files beyond a read pass and its
rollback is proven exact.
