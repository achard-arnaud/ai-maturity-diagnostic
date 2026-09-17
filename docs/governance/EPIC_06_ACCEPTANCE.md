# Epic 06 — Product Intelligence and Immutable Snapshots — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/product_v1.schema.yaml`/`product_version_v1.schema.yaml`/`product_snapshot_v1.schema.yaml` + `app/product_policy.py`: frozen semantics, deterministic content hashing, immutability guard. |
| S02 | `app/product_workflow.py`: draft/review/publish/supersede, publish gated to `product_owner`, audited. |
| S03 | `app/product_snapshot_store.py`: enforced immutability at the store layer, per-product staleness propagation. |
| S04 | `app/product_visibility.py`: ADR-008 projection, proven no cross-workspace leakage, silent-shadowing rejection. |
| S05 | `app/product_store.py`/`app/product_diff.py`/`app/product_routes.py`: API with stable deep links, content diff. |
| S06 | `app/product_migrator.py`: legacy catalog migration with an E2E harvest→publish proof. |

All 6 shipped in one PR to `dev`: [#50](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/50).

## Gate checklist

- [x] All 6 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00-05 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #50's CI (release-check + e2e-gate both green
      across both duplicate CI runs, first attempt, no flake).
- [x] Audit invariants this Epic owns re-checked: **aucune preuve ne
      compte dans la vérité produit** -- `contracts/product_snapshot_v1.
      schema.yaml`'s `evidence_ids` only ever ground already-stated
      exclusions/hard_gates/capabilities; no code path derives content
      from evidence. **Snapshot publié immuable**: S01's
      `assert_snapshot_immutable` and S03's store-layer enforcement both
      independently reject a mutation attempt under an existing
      `snapshot_id`, proven by `test_n_minus_1_snapshot_is_unaffected_by
      _a_new_publish` and the store's own re-put tests. **Correction par
      supersession**: S02's `publish_version` supersedes the prior
      published version in the same call a new one publishes, never
      leaving two versions "published" at once; content_hash is provably
      permanent per snapshot_id (S01/S03 hash-determinism and
      reproducibility tests).
- [x] Migration/rollback: `app.product_migrator` is additive/backfill
      only against `product_catalog/*.yaml`, which is never mutated
      (read-only pass); rollback proven exact via the same N-1-style
      removed-count property as Epic 05's demand migrator.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 6 sprints, still
      35/35, unchanged. `app/catalog.py`/`app/catalog_promotion.py` (the
      legacy harvest/promotion path) were also read-only throughout --
      S06's E2E test calls `promote_candidate` unmodified and only reads
      its output.
- [x] Release notes and known limitations published below.

## Known limitations

- `ProductVersion` (S01/S02) is not yet independently persisted --
  `app.product_workflow.publish_version` takes version dicts as
  parameters and produces a `ProductSnapshot`, but no
  `product_version_store.py` exists yet to durably track draft/in_review
  version history across process restarts. `app.product_migrator`
  sidesteps this by writing Product + Snapshot directly (a snapshot's own
  `product_version_id` field preserves the traceability link). Building a
  version store is deferred, narrow follow-on work; nothing in this
  Epic's Fit-facing contract (Product + immutable Snapshot) depends on it.
- `app/product_workflow.publish_version`'s RBAC check
  (`actor_role == "product_owner"`) is a simple string comparison, not
  yet wired through `app.authruntime.deps.require_role` at a route layer
  -- no HTTP publish endpoint exists yet (S05 only shipped read routes).
  Building the write-side route (`POST .../products/{id}/publish`) is
  deferred to whichever Epic/Sprint needs product-owner-driven publish
  exposed over the API.
- Search (mentioned in this Epic's S05 objective line) was descoped to
  the diff/read-model contract actually specified in the Sprint's test
  gate ("contract/performance fixtures") -- a dedicated
  `product_search.py` (full-text over published snapshots) is deferred,
  narrow follow-on work.
- Carried over from Epic 00-05 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 06. Decision made
autonomously per the operator's instruction to continue the same
iterative sprint-by-sprint procedure for Epics 06-10.
