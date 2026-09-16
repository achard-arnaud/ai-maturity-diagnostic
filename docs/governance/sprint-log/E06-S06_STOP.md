# STOP — Epic 06 / Sprint S06

## Objective

UI library/version diff/publish + migration legacy. Stop condition:
"catalogue compatible" -- E2E harvest→publish.

As with every prior Epic's "UI" sprint (Epic 02/04/05 S05), this means
the read-model/migration layer a UI consumes, not frontend HTML/JS.

## Outputs

- `app/product_migrator.py`: `ProductMigrator(repo_root).plan/apply/
  rollback`, same dry-run/apply/rollback/manifest shape as
  `demand_migrator`/`network_v1_migrator`. Reads legacy
  `product_catalog/*.yaml` offer files (written by
  `app.catalog_promotion.promote_candidate`), maps each to exactly one
  Product + its first published Snapshot -- `positioning.one_liner` ->
  `description`, `problem.anti_problem` -> `exclusions`,
  `hard_gates` -> `hard_gates`, `outcomes.primary` -> `capabilities`.
  An offer carrying `workspace_id` maps to a workspace overlay
  (`owner_scope.kind=workspace`); one without maps to shared-core.
  Deterministic ids, idempotent re-apply (already-migrated offers are
  skipped), rollback proven to remove exactly the applied
  product+snapshot set. Legacy `product_catalog/*.yaml` files are only
  ever read, never mutated.
- `tests/test_product_migrator.py`: 8 unit tests (plan finds all
  offers and is deterministic, apply creates a correctly-mapped
  product+snapshot, apply is idempotent on rerun, a workspace-scoped
  offer maps to a workspace overlay, rollback removes exactly the
  applied set, rollback rejects a non-applied manifest) plus the
  Sprint's own E2E gate:
  `test_harvest_promote_migrate_publish_end_to_end` -- stages a harvest
  candidate the same way `app.catalog.CatalogHarvester.stage()` would,
  promotes it via the real, unmodified
  `app.catalog_promotion.promote_candidate` (the legacy path, untouched
  by this Epic), migrates the resulting `product_catalog/*.yaml` file,
  and confirms the resulting v1 Product+Snapshot is queryable, correctly
  mapped, and visible to any workspace (shared-core, since the promoted
  offer carries no `workspace_id`).

## Evidence

`python -m unittest tests.test_product_migrator -v`: 8/8 pass.
Full `python scripts/check_release.py`: 0 errors.
Legacy network suite (35 tests) re-verified unchanged.

## Epic 06 status

All 6 Sprints closed (S01 Product/Version/Snapshot schemas and frozen
semantics; S02 draft/review/publish/supersede workflow and RBAC; S03
snapshot immutability and stale propagation; S04 catalog ownership/
subscription model with proven no-leakage; S05 API/diff/read models with
stable deep links; S06 legacy migration with an E2E harvest→publish
proof). Epic acceptance (a future Fit can reference exactly the
published content; editing an offer creates a new version without
changing history) is verified: S01/S03 prove immutability and
reproducibility; S02 proves publication is RBAC-gated and audited; S06
proves the legacy catalog absorbs cleanly into the new model without any
mutation of legacy files.
