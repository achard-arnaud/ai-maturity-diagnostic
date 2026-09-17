# ADR-011 — Evidence Acquisition and Search (Epic 14)

Status: **Accepted**
Repository: `achard-arnaud/ai-maturity-diagnostic`
Baseline: `main == dev` at P0 closeout (`85e9632`)

## Context

Epic 03's `app/signal_ingestion.py` ships an `ingest_public()` adapter whose
own module docstring explicitly defers "a real live fetch/premium
connector" behind the "public" path. Epic 14's purpose (per
`EPIC_14_RESEARCH_ACQUISITION_AND_SEARCH.md`) is to build that live
acquisition layer: `SearchRequest -> source adapters -> EvidenceCandidate[]
-> dedupe/rank -> provenance + acquisition method -> explicit promotion to
Signal/Evidence/ResearchCase`.

Per this program's harvest gate (G4: "no new search engine ... is built
before auditing existing repos and libraries"), a full source-by-source
audit of `achard-arnaud/search-social-networks` was already produced at
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md`. That document
is the primary input to this ADR; this ADR **ratifies its recommendations**
rather than re-deriving them, and resolves the small number of decisions
it explicitly left open for an architecture owner.

## Decision

### 1. Source disposition (ratifying the harvest note's §1/§2 verbatim)

All nine `search-social-networks` sources are adopted, none rejected:

| Source | Function | Disposition |
|---|---|---|
| Hacker News | `search_hackernews` | REUSE_AS_IS (body) + WRAP (integration) |
| GitHub | `search_github` | REUSE_AS_IS (body) + WRAP (integration) |
| arXiv | `search_arxiv` | REUSE_AS_IS (body) + WRAP (integration) |
| LinkedIn | `search_linkedin` | WRAP |
| YouTube | `search_youtube` | WRAP |
| Reddit | `search_reddit` | WRAP |
| X | `search_x` | WRAP (low priority — thin signal, may ship last) |
| Perplexity | `search_perplexity` | ADAPT — the keyless path's silent relabeling of a web result as `"perplexity"` needs an explicit workspace-authorization gate, normalized to the same "explicit user authorization" model every other commercial path uses (never "key present in env" alone) |
| Web (`web_index`) | `search_web` | ADAPT — this function is also the shared fallback for five other sources; the wrapper must expose "web_index came back malformed" as a distinct, first-class operational health signal, not indistinguishable from "zero results" |

**Vendoring, not cross-repo import.** `search-social-networks` is a
separate git repository; `ai-maturity-diagnostic` vendors the adopted
source files under `scripts/social_search/` (mirroring the upstream
package layout, MIT license/copyright header preserved verbatim per the
harvest note §8) rather than depending on it as a live import or git
submodule. This keeps the "no new integration coupling without measured
need" invariant (Program invariant #11) intact and matches this repo's
existing convention of vendoring `scripts/*_common.py`-style utilities
rather than adding cross-repo runtime dependencies.

The upstream `run_all`/`doctor`/dedupe orchestration in
`scripts/search_social_networks.py` is **EXTRACT_PATTERN only**: the
fan-out/per-source-isolation *shape* is copied into this repo's own
`app/harvest_runner.py` (§3 below), built on this repo's own
`RunManager`/`BudgetLedger`/`correlation_scope` rather than re-implemented
or imported as a module.

### 2. SearchRequest / EvidenceCandidate contract

Two new plain-Python, dependency-free shapes in `app/acquisition_policy.py`
(mirroring `app/research_policy.py`'s established convention: frozen
dataclasses, an `*Error` dataclass return from validators, no I/O):

- **`SearchRequest`**: `workspace_id`, `query`, `sources` (subset of the 9,
  never "all" by default per Program invariant "do not fan out to all
  sources by default" — S03), `days`, `limit`, `enrich`, `allow_commercial`,
  `requested_by` (actor id), `space` (`discover | research | targets` —
  determines the canonical-object mapping per harvest note §7), and an
  optional `research_case_id` (set only when the request originates from
  an open ResearchCase, S05).
- **`EvidenceCandidate`**: the mapped, not-yet-promoted shape a source
  adapter's raw `Result` becomes before it is written as
  `CanonicalEvidenceV1`/`CanonicalSignalV1`. Carries everything the harvest
  note's §3 mapping table requires (`source`, `locator`, `excerpt`
  pre-truncated to 1000 chars, `dated_at`/`observed_at`, `evidence_grade`
  defaulted per source per harvest note §3, `epistemic_status` defaulted
  per source, raw per-source `metadata` preserved verbatim including
  epistemic-caveat flags like `live_role_validation: False`) plus a
  `dedup_key` computed the same way `app/signal_policy.compute_dedup_key`
  already does, so a candidate and the signal it becomes never diverge on
  identity.

**Validation rules (S01 tests, per the Epic brief):**
- A candidate with no provenance (`source.ref`/`locator` empty, or
  `evidence_grade`/`epistemic_status` missing) is rejected before it can
  become an `EvidenceCandidate` at all — never silently defaulted to
  something more confident than the source warrants.
- No code path from `SearchRequest`/`EvidenceCandidate` may set a Demand,
  Fit, or TargetPlan-readiness field, mirroring
  `app/signal_policy.assert_no_demand_fields`'s existing guard — enforced
  by an equivalent `assert_no_demand_or_fit_fields` in
  `app/acquisition_policy.py`, reused by every sprint that touches these
  shapes.
- A harvested candidate's `evidence_grade` is never assigned above `U1`
  (unverified) without independent corroboration already present in the
  workspace — see §4.

### 3. Budget/correlation/run wrapper (ratifying harvest note §4)

`app/harvest_runner.py` (new): `run_harvest(root, workspace_id, actor_id,
request: SearchRequest) -> HarvestRun`, built entirely on three existing
primitives (no new durable-state mechanism):

1. `app.execution_context.correlation_scope()` — one correlation ID per
   harvest run, threaded into every `EvidenceCandidate` and log line.
2. `app.execution_policy.BudgetLedger`/`BudgetEnvelope`/`Usage` — one
   `Usage(calls=1, wall_seconds=...)` charge per source call, workspace-
   scoped; `BudgetExceeded` stops the run rather than degrading silently.
3. `app.run_manager.RunManager` — `prepare()` once per harvest invocation,
   `start()`, `checkpoint()` after each source completes (mirrors upstream's
   own per-source isolation), `complete()`/`block()`/`fail()` as
   appropriate. A partial harvest is resumable via `resume_token`, never
   silently restarted from zero.

Retryable vs. non-retryable failure classification reuses
`app.execution_policy.RetryPolicy`'s existing status-code set (408, 425,
429, 500, 502, 503, 504, plus timeouts).

### 4. Evidence grading and epistemic defaults (ratifying harvest note §3/§5)

Per-source default `evidence_grade`/`epistemic_status` for a freshly
harvested, uncorroborated `EvidenceCandidate`:

| Source class | `evidence_grade` | `epistemic_status` |
|---|---|---|
| Any `search-social-networks` source, first observation | `U1` | `hypothesis` |
| Same underlying fact corroborated by ≥2 independent sources (S04/S05 dedupe/rank layer) | may promote to `W1`, never above, and only via an explicit function a human-facing surface calls, never automatically | `inference` at most |

**Never**: a harvested candidate reaching `P1`/`P2`, or `epistemic_status:
fact`, purely from acquisition. That promotion path is `CanonicalClaimV1`'s
existing lineage rule (`app.research_policy.validate_claim_lineage`) —
Epic 14 feeds candidate evidence into it, never bypasses it.

**LinkedIn specifically** (harvest note §5): a LinkedIn hit may create an
`ExternalIdentityMapping` with `status: "candidate"` only, never
`"validated"`, and never by itself flips a `role_validation_request` to
resolved or writes `current_role` onto a `CanonicalPersonV1`. This is
enforced by construction: `app/acquisition_policy.py`'s LinkedIn mapping
path has no return type that could satisfy either write.

### 5. Blocker mapping (ratifying harvest note §6, no contract change)

Harvest failures/degradation map onto `blocker.schema.yaml`'s existing
`category` enum (`runtime`, `human_review`, `security`, `role`) exactly as
tabulated in the harvest note — no new blocker category is introduced.
`web_index` markup drift (correlated `error`/`empty` across many unrelated
queries) is the one case worth a dedicated cross-run detector, raised as
`category: runtime, severity: critical`.

### 6. Discover / Research / Targets placement (ratifying harvest note §7)

One shared harvest wrapper, parameterized by `SearchRequest.space`, not
per-space copies:

- **Discover** (pre-Fit, broad): Hacker News, arXiv, GitHub, Web, X —
  feed `CanonicalSignalV1` via `app/signal_store.py`.
- **Research** (product-blind, account already selected): YouTube, Reddit,
  Perplexity — feed `CanonicalEvidenceV1`/`CanonicalClaimV1` against a
  `research_case_id` via `app/research_case_store.py`.
- **Targets** (post-Fit only): LinkedIn's `/in/` lane — feeds
  `TargetPlan`/`Role`/`Relationship` only after a Fit decision exists, and
  only through `role_validation_request`/`external_identity_mapping`
  (§4). A `SearchRequest{space: "targets", sources: ["linkedin"]}` issued
  before Fit is rejected by `app/acquisition_policy.py`, not merely
  discouraged by convention.

### 7. Sprint sequencing

Matches `EPIC_14_RESEARCH_ACQUISITION_AND_SEARCH.md`'s S01-S07 exactly;
this ADR is S01's required contract-first deliverable. S02 vendors the
source adapters behind the wrapper; S03 adds query orchestration/budgets;
S04 ships Discover search read APIs; S05 wires ResearchCase-initiated
acquisition; S06 hardens LinkedIn/person handling; S07 ships the
workspace-safe API/UI/NRT closing the loop.

## Consequences

- No second search/reasoning engine is built; `search-social-networks`'
  acquisition functions are reused almost verbatim, with this repo's own
  budget/run/workspace discipline wrapped around them.
- `web_index` (DuckDuckGo HTML scraping) remains a load-bearing, accepted
  operational risk (harvest note §1/§8) — not a documented API contract.
  This is named explicitly rather than glossed over; a future ADR may
  replace it with a paid SERP API behind the same single function boundary
  without touching the other eight sources.
- Every new workspace-scoped write introduced by this epic (harvest runs,
  evidence, signals) follows the already-established per-workspace-path
  storage convention (`data/private/evidence/{workspace_id}/...`,
  `runtime/budgets/{workspace_id}.yaml`, `runtime/runs/{run_id}.yaml`
  scoped by the owning `RunManager.workspace_id`) — not the legacy
  mono-root pattern P0 just finished migrating away from.
