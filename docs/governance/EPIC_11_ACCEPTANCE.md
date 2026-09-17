# Epic 11 — Opportunity, Proof, Deal and Expansion — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

Authored retroactively during the post-E13 closeout audit
(`docs/audit/post-epic/`): every other Epic (00-10, 12, 13) has both a
spec/decision doc and this acceptance record; Epic 11 shipped with six
`docs/governance/sprint-log/E11-S0[1-6]_STOP.md` files but neither a spec
doc under `docs/gtm-transformation/epics/` nor this record. The code and
tests below were independently re-verified during that audit, not taken on
faith from the STOP files alone.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/lead_v1.schema.yaml`/`opportunity_v1.schema.yaml`/`proof_v1.schema.yaml`/`deal_v1.schema.yaml`/`expansion_v1.schema.yaml` + `app/opportunity_policy.py`: **prospect ≠ opportunity** — a raw prospect has no Opportunity representation, and an Opportunity preserves the qualified Lead's Demand/Fit/TargetPlan lineage; same-workspace chain enforced, rewritten upstream links rejected. |
| S02 | `app/opportunity_lifecycle.py` (transition policy): **no stage skip** — `draft → discovery → proof → proposal → won/lost` is the sole transition graph, every destination has named exit criteria; qualification requires a `PURSUE` fit, an active TargetPlan and a `meeting_booked` EngagementEvent; conversion never implicitly creates an Opportunity. |
| S03 | Bounded, provenance-linked Discovery notes (4,000-char cap, `commercial_reviewer`/`admin` only) and an append-only commercial decision log (attributed, source-linked, `commercial_decider`/`admin` only); neither mutates Demand/Fit/TargetPlan/Engagement inputs. |
| S04 | `app/proof_policy.py`: **preuve avant claim client** — a proof requires at least one measurable target and a falsifier before it can run; outcome is `met`/`not_met`/`inconclusive` (missing observation is never success); only a `met` outcome with evidence may support a client claim. |
| S05 | `app/opportunity_store.py`/`app/opportunity_routes.py`: atomic Opportunity persistence, deterministic list pagination, IDOR-safe `GET /opportunities`, detail and Pipeline-board endpoints; the board contains every canonical stage (including empty ones), sorted deterministically, as a pure projection of Opportunity records. |
| S06 | Commercial lifecycle closure: loss reasons required, won-only expansion (impossible before a won Deal), outcome-linked learning events that are observational and cannot mutate a rule. |

Release PR to `main`: [#64](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/64) ("Release Epic 11 — Opportunity, Proof, Deal and Expansion"), merge commit `59007c4058091f2854303b6501fa0b30b7b8c63f`.

## Gate checklist

- [x] All 6 Sprints accepted against their own STOP-file stop condition; code and tests re-verified during the post-E13 audit (`docs/audit/post-epic/EPIC_DELIVERY_MATRIX.md`), not inferred from commit messages or branch names.
- [x] Full release gate green: `scripts/check_release.py` reproduced locally during the audit (0 release errors, 91% app line coverage, well above the 80% gate) and confirmed green on GitHub Actions for the current `main` head.
- [x] Audit invariants this Epic owns, re-checked: **prospect ≠ opportunity** (S01), **aucun stage skip** (S02), **notes bornées** (S03), **preuve avant claim client** (S04), **projections stables** (S05), governed won/lost closure with non-mutating learning events (S06) — each has a dedicated test module (`test_opportunity_contracts.py`, `test_opportunity_lifecycle.py`, `test_opportunity_notes.py`, `test_proof_policy.py`, `test_opportunity_store.py`, `test_commercial_outcomes.py`).
- [x] Migration/rollback: not applicable — this Epic introduces new, additive objects (Lead/Opportunity/Proof/Deal/Expansion) with no legacy artifact to migrate from.
- [x] Release notes and known limitations published below.

## Known limitations

- Carried over from prior Epics (not created by this Epic): `feat/prospection-principes-todo` remains unmerged, now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo` rather than a live branch (see `docs/governance/SUPERSESSION_REGISTRY.md`); GitLab's `e2e-gate` mirror unverified against a live runner.
- Same pattern as prior Epics' still-unbuilt write routes (Epic 06 product-publish, Epic 08 target-plan write, Epic 09 reach write, Epic 10 engagement write): this Epic's HTTP surface (S05) is read-only; lifecycle transitions (S02, S04, S06) are Python-API-only, not yet exposed as HTTP write routes.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a named owner (consistent with every other closed Epic's deferrals); no open blocker is specific to Epic 11. This record closes a documentation-authority gap only — the Epic itself was already fully merged to `main` (PR #64) and in continuous production use through E12/E13 before this record existed.
