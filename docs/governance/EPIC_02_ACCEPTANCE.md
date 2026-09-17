# Epic 02 — Canonical Account and Network Graph — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `docs/ADR-009-canonical-identity-model.md` + `contracts/{person,company,relationship}_v1.schema.yaml`: additive `entity_id`/`legacy_ids` projection fixing the legacy hash-derived, non-immutable ID problem. Zero legacy code touched. |
| S02 | `app/network_temporal.py`: currentness policy combining `current_status` with the new `valid_from`/`valid_to` interval; contradictory records raise for human review. |
| S03 | `app/identity_resolution.py`: human-audited, reversible merge proposals; never auto-merge, never delete. |
| S04 | `app/network_v1_store.py` + `app/network_v1_routes.py`: first `/api/v1/...` routes, real auth/pagination/IDOR tests against the actual app. |
| S05 | `app/person_view.py`: Person 360 composing identity/relationships/companies without fusing their provenance. |
| S06 | `app/network_v1_migrator.py`: legacy→v1 dry-run/apply/rollback backfill, deterministic entity_ids, legacy files verified untouched. |

All six shipped in one PR to `dev`: [#38](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/38).

## Gate checklist

- [x] All 6 Sprints accepted; one deferred item explicit (below), carried
      over from Epic 00, not created by this Epic.
- [x] Full release gate (`scripts/check_release.py`) green on `dev` at
      `0745d56`: 0 errors, re-verified fresh after the merge (not just
      trusted from CI).
- [x] E2E gate (`scripts/run_e2e_gate.py` / CI's `e2e-gate` job): green on
      both duplicate CI runs for PR #38 (one clean on the first try, the
      other needed one re-run of the same pre-existing flaky UI test
      already documented in `EPIC_00_ACCEPTANCE.md` — not a regression
      from this Epic, which touched no frontend/E2E-covered surface).
- [x] Audit invariants this Epic owns re-checked, not assumed:
      evidence-first (every v1 record keeps its own `provenance` block),
      workspace isolation (S04's IDOR tests against the real app, not
      just unit-level), currentness (S02's `evaluate_currentness` +
      S05's `requires_human_review` surfacing, never silently assumed
      current), lineage (S06's `legacy_ids` links, S03's merge/reverse
      trail that never deletes).
- [x] Migration rehearsed: S06's dry-run/apply/rollback tested with real
      counts/hash-equivalence assertions (legacy JSONL byte-for-byte
      unchanged after apply) and a rollback-removes-only-its-own-entities
      test.
- [x] `docs/governance/TRACEABILITY_MATRIX.md` — not updated with new
      rows in this record; the per-sprint `E02-Sxx_STOP.md` files carry
      the requirement-to-test mapping for this Epic in full detail
      already (this repo's existing matrix predates Epic 02 and is owned
      by Epic 00's governance scope, not restated per-Epic).
- [x] Release notes and known limitations published below.

## Known limitations

- `feat/prospection-principes-todo` remains unmerged, now archived as tag
  `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`
  rather than a live branch (carried over from Epic 00's own acceptance
  record; still fails the package validator;
  still not this Epic's or Epic 00's to fix — a dedicated skill-authoring
  sprint's job).
- The v1 store (`data/private/network_v1/...`) has **no real production
  data** yet outside migration-rehearsal tests. `app/network_v1_migrator`
  is built, tested, and dry-run-verified, but no operator has run it
  against a real workspace's legacy data. The `/api/v1/...` routes are
  therefore live but will return empty pages until that backfill is
  actually run — this is intentional (Epic 02's stop conditions are about
  the contracts/mechanics being correct, not about a specific workspace's
  data being migrated) but worth flagging before anyone expects the new
  API to already serve real people/companies.
- `app.identity_resolution`'s merge proposals are not wired to
  `app.network_index.find_potential_duplicates` (detection) or to any
  storage — S01-S06 prove the mechanics are correct in isolation; wiring
  detection → proposal → human review → applied merge into one operator
  workflow is follow-on work for whichever future Epic/Sprint needs real
  dedup throughput (not scoped by Epic 02's own sprint plan).
- The GitLab `e2e-gate` mirror job remains unverified against a live
  GitLab runner (same limitation as Epic 00).

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 02. Decision made
autonomously per explicit operator instruction to continue Epic-by-Epic,
sprint-by-sprint on `dev`, merging progressively, with `main` release at
Epic acceptance.
