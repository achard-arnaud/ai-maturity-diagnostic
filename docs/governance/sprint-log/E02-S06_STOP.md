# STOP — Epic 02 / Sprint S06

## Objective

Migration/index/reconciliation du réseau legacy. Stop condition: "legacy
routes compatibles" (legacy routes stay compatible), tests: counts/hashes/
parity.

## Outputs

- `app/network_v1_migrator.py`: `NetworkV1Migrator(repo_root,
  workspace_id)` follows the same dry-run/apply/rollback/manifest shape
  as Epic 01's `app.workspace_migrator` (`plan()` -> `apply(plan)` ->
  `rollback(manifest_path)`, manifests under `runtime/migrations/`).
  Scope, per ADR-009: a **1:1 backfill** only. Each currently-scoped
  legacy person/company/relationship record gets exactly one new
  `entity_id`, deterministically derived from the immutable legacy id
  string (`sha256(legacy_id)[:16]`) — not from mutable identity-key
  fields, so re-running the dry-run is reproducible (required for
  migration rehearsal to mean anything), and re-applying after a rollback
  produces the same `entity_id`s again. Discovering that two different
  legacy ids are the same real entity is explicitly **not** this Sprint's
  job — that is S03's `identity_resolution` module, run afterward against
  the now-populated v1 store.
- `apply()` scopes strictly to the target `workspace_id` (via legacy
  `company.workspace_id`, coalesced the same way the legacy reader already
  does) and writes into `app.network_v1_store`, never into the legacy
  JSONL files.
- `rollback()` removes only the entity_ids this specific migration's
  manifest recorded, not the whole v1 store.

## Evidence

- `python -m unittest tests.test_network_v1_migrator -v`: 7/7 pass —
  workspace scoping, dry-run writes nothing, apply rejects a plan from
  the wrong workspace, apply backfills with correct `legacy_ids` linkage,
  **counts** are asserted (parity: 1 person / 1 company / 1 relationship
  in-scope out of 2/2/1 total legacy records across two workspaces),
  dry-run is **deterministic** across repeated runs (same entity_ids), the
  **legacy JSONL files are byte-for-byte untouched** after apply
  (hash-equivalent: read-before/read-after string equality), and
  rollback removes exactly the entities this migration created.
- **Legacy routes compatible**: re-ran the full pre-existing legacy
  network test suite (`tests/test_network_layer.py`,
  `test_network_writer.py`, `test_network_index.py`,
  `test_account_view.py`, `test_duplicate_dismissals.py`) after all of
  Epic 02's S01-S06 changes: 35/35 still pass, unchanged. Nothing in this
  Epic touched `app/network_writer.py`, `app/network_index.py`,
  `app/account_view.py`, or `app/duplicate_dismissals.py`.

## Epic 02 status

All 6 Sprints closed. Epic acceptance (journey personne->entreprise->
relation and entreprise->personnes, cross-workspace protected, stale role
blocks downstream use) is verified across S01-S06's tests: S04/S05's IDOR
tests prove cross-workspace protection; S02's `CurrentnessConflict` +
S05's `requires_human_review` flag prove a stale/contradictory role
blocks (surfaces for review rather than silently propagating) rather than
being used downstream as if current.
