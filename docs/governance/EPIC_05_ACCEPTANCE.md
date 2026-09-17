# Epic 05 — Demand as a First-Class Object — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/demand_v1.schema.yaml` + `app/demand_mapping.py`/`app/demand_policy.py`: 8 knowable dimensions, each an explicit known-or-unknown pair; migration parity from the legacy `enterprise_demand_profile`. |
| S02 | `app/demand_lifecycle.py`: transition table + `qualify_demand` as sole gated path to `qualified`; every rejection carries a specific reason. |
| S03 | `app/demand_evidence.py`: idempotent claim linking, provenance completeness/staleness, confidence from active-claim evidence grade. |
| S04 | `app/demand_store.py` + `app/demand_routes.py`: optimistic-concurrency mutation (409 on stale version), duplicate-create refused, IDOR-safe auth. |
| S05 | `app/demand_resolver.py` + Company 360 dossier extension: full resolver contract; unknowns always visible; E2E detect→qualify. |
| S06 | `app/demand_migrator.py`: dry-run/apply/rollback, deterministic ids, content hashes, validated N-1 rollback. |

All 6 shipped in one PR to `dev`: [#47](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/47).

## Gate checklist

- [x] All 6 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00/02/03/04 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #47's CI (release-check + e2e-gate both green
      across both duplicate CI runs, first attempt, no flake).
- [x] Audit invariants this Epic owns re-checked: **Demand indépendante
      du catalogue** -- `contracts/demand_v1.schema.yaml` carries no
      product/catalog/offer/fit/targeting field anywhere
      (`additionalProperties: false`, structurally impossible to add
      one). **Inconnues visibles**: every one of the 8 knowable
      dimensions is an explicit `{known, value}` pair -- an unknown
      dimension is never silently omitted, defaulted, or inferred; S05's
      Company 360 dossier extension surfaces `unknown_dimensions` by
      name for every listed Demand. **Fit et ciblage interdits**: no
      match/score/recommendation object exists anywhere in this Epic;
      `qualify_demand` (S02) is the only lifecycle gate, and it tests
      problem+buying-signal knowledge, never product fit -- Fit itself
      is out of scope (Epic 07, not yet built).
- [x] Migration/rollback: this Epic's own migration
      (`app.demand_migrator`) is additive/backfill-only against the
      legacy `05_enterprise_demand_profile.yaml` artifacts, which are
      never mutated (read-only pass); rollback is proven exact (removes
      precisely the applied `demand_id` set, leaving any other demand
      untouched -- the N-1 property from S06's own tests).
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 6 sprints, still
      35/35, unchanged -- no file under `app/network_writer.py`/
      `network_index.py`/`account_view.py`/`duplicate_dismissals.py` or
      `skills/network-account-screening/` was touched. `app/demand.py`
      (the legacy `DemandCatalog`) was also read-only throughout -- no
      Sprint modified it; S01/S06 both build strictly additive v1
      modules alongside it.
- [x] Release notes and known limitations published below.

## Known limitations

- `app/demand_migrator.py`'s `company_entity_id` mapping derives a
  deterministic hash from the legacy `company_id`/`company` name, not
  from Epic 02's canonical `CanonicalCompanyV1.entity_id` -- reconciling
  the two id schemes (so a migrated Demand's `company_entity_id` matches
  the same company's Epic 02/04 canonical entity) is follow-on work, not
  yet built. Until then, `company360_view`'s demand aggregation only
  finds a migrated Demand if that reconciliation has separately happened.
- `app/demand_lifecycle.py`'s qualification checklist requires exactly
  "problem known + >=1 buying signal known" -- a fixed, simple bar. A
  richer, workspace-configurable qualification policy (weighted
  dimensions, required evidence grade thresholds) is deferred; nothing
  in this Epic prevents adding one later without changing the checklist's
  own contract shape (`QualificationChecklist(passed, missing)`).
- `app/demand_evidence.py`'s `compute_confidence` reads a claim's own
  `evidence_grade` field directly rather than looking up its linked
  Evidence records' grades (Epic 04's `Claim`/`Evidence` are separate
  objects) -- a claim that doesn't carry this convenience field will
  under-report confidence. Wiring `compute_confidence` through
  `app.evidence_store` for the claim's actual linked evidence is
  follow-on work.
- Carried over from Epic 00/02/03/04 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner; Epic 04's `ResearchCase` has
  no automated `ResearchQueued`-event consumer yet (still follow-on work,
  unrelated to Demand).
- Fit (Epic 07) and voice-to-text interview capture are both explicitly
  deferred per this Epic's own "Deferred work" line -- not started.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 05. Decision made
autonomously per the operator's instruction to process Epics 03, 04, 05
iteratively with the same procedure, merging progressively to `dev` and
releasing to `main` at each Epic's acceptance -- this closes that
instruction's three-Epic scope.
