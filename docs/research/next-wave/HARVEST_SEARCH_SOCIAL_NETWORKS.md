# Harvest audit: `achard-arnaud/search-social-networks` for candidate Epic E14

Status: **research and proposal only**. No code was written or modified in either
repository to produce this document. This is the G4 harvest gate audit
("no new search engine, editor, exporter or notes system is built before
auditing existing repos and libraries") for the search/acquisition capability
E14 would otherwise build from scratch.

Author context: prepared for francois.arnaud.rjc@gmail.com's review as part of
the E14 cadrage pack. Repo audited: `/home/user/search-social-networks`
(commit tree as cloned into this session). Target repo:
`/home/user/achard-arnaud/ai-maturity-diagnostic`.

---

## 0. What `search-social-networks` actually is

- Nine atomic, persona-neutral skills (`linkedin-search`, `youtube-search`,
  `x-search`, `reddit-search`, `hackernews-search`, `github-search`,
  `arxiv-search`, `perplexity-search`, `web-search`), each a thin skill
  wrapper around one Python function in `scripts/social_search/`.
- One shared, dependency-free (stdlib-only) runner:
  `scripts/search_social_networks.py`, which fans a query out across
  sources with a `ThreadPoolExecutor`, isolates per-source failure
  (`run_source` catches `Exception` and returns `SourceRun(status="error")`),
  and returns one JSON payload with per-source status plus a deduplicated
  `cross_source_results` view.
- Explicit design principle (`docs/ARCHITECTURE.md`): "one search capability
  = one discoverable skill name = one source-specific function," and
  "the skills are deliberately persona-neutral" — i.e. this repo's own
  authors already anticipated being consumed by a higher-level, persona-aware
  product like `ai-maturity-diagnostic` and designed the API surface (plain
  Python functions with a uniform signature
  `f(query, days, limit, enrich, allow_commercial=False) -> list[Result]`)
  for exactly that.
- Every acquisition function returns a list of `social_search.core.Result`
  dataclasses (`scripts/social_search/core.py:9`), and the CLI wraps runs of
  those into `SourceRun` records with `status ∈ {ok, empty, error}`.

## 1. Per-source classification (SOURCE / CAPABILITY / … / DECISION)

Function signatures below all live in `scripts/social_search/` and share the
exact call shape `f(query: str, days: int, limit: int, enrich: bool,
allow_commercial: bool = False) -> list[Result]`.

### LinkedIn

- **SOURCE**: `scripts/social_search/linkedin.py` — `search_linkedin`
  (`_search_linkedin_public` + optional `_search_linkedin_sc`).
- **CAPABILITY**: DuckDuckGo-indexed `site:linkedin.com/pulse`,
  `/posts`, `/in` lanes (`_search_linkedin_public`, line 6-13), each tagged
  with `content_type` (`article`/`post`/`profile_index_entry`) and explicit
  negative-capability metadata: `authenticated_linkedin_access: False`,
  `live_role_validation: False`, `canonical_identity_resolution: False`
  (line 11). Optional ScrapeCreators post-search enrichment
  (`_search_linkedin_sc`, line 14-21) only if `allow_commercial=True` **and**
  `SCRAPECREATORS_API_KEY` is already set; its results are merged but never
  replace the public lane (`search_linkedin`, line 22-27: `dedupe([*paid,
  *public], limit)`).
- **LICENSE**: repo-wide MIT (see §3). No LinkedIn ToS grant is claimed;
  this is public web-index scraping via DuckDuckGo HTML, not the LinkedIn
  API.
- **CURRENT MATURITY**: production-shaped for a CLI/skill context — retried
  HTTP, deterministic dedup, explicit fallbacks — but zero LinkedIn-specific
  tests beyond `test_linkedin_public_lane_always_runs` and
  `test_linkedin_sc_augments_but_does_not_replace_public`
  (`tests/test_search_social_networks.py:28-46`).
- **REUSE SURFACE**: the *shape* of the public-lane cascade and its
  explicit "this is not proof of X" metadata convention is directly
  reusable as a pattern; the DuckDuckGo-scrape mechanism itself is fragile
  (HTML scraping via a hand-rolled `HTMLParser`, `core.py:58-78`) and not
  something to depend on for a revenue-relevant product surface without
  a fallback/monitoring plan.
- **ADAPTATION REQUIRED**: (a) inject `ai-maturity-diagnostic`'s own budget/
  correlation-ID/run discipline (see §3); (b) map `Result` → `CanonicalSignalV1`
  + `CanonicalEvidenceV1`, never let a LinkedIn hit alone become
  `ExternalIdentityMapping.status="validated"` or a `current_role` claim
  (see §4); (c) DuckDuckGo HTML scraping is an external dependency risk this
  repo doesn't own or version — worth an explicit "known-fragile" note in
  any ADR, with the ok/empty/error status (already present) wired to a
  blocker rather than silently degrading UX.
- **SECURITY-PRIVACY**: no authenticated session, no cookies, no browser
  automation (`README.md:104`, `165`; `doctor()` in
  `search_social_networks.py:18` reports
  `authenticated_linkedin_scraping: False` as a machine-checkable
  guarantee). This directly matches `ai-maturity-diagnostic`'s own
  `LI-POL-001..008` invariants in `AGENTS.md:137-148` (see §4).
- **COUPLING**: none to ai-maturity-diagnostic; only optional coupling to
  ScrapeCreators (commercial, opt-in, keyed).
- **MAINTENANCE**: single external repo, MIT, last touched per this audit's
  clone; no CI badge beyond its own `qa.yml`. Sole named maintainer
  attribution is "search-social-networks maintainers" (`.claude-plugin/
  plugin.json`) — thin bus factor.
- **TEST STRATEGY**: reuse repo's own `tests/test_search_social_networks.py`
  as a contract test for the vendored/adapted function; add
  `ai-maturity-diagnostic`-side tests asserting the wrapper never lets a
  LinkedIn-sourced signal set `company_entity_id`/role fields without
  going through `role_validation_request.schema.yaml`'s flow.
- **EXIT STRATEGY**: swap-in cost is low — the function returns plain
  dataclasses; if DuckDuckGo scraping breaks or the repo goes unmaintained,
  the consuming wrapper's contract (produce zero-or-more `Result`-shaped
  dicts, or raise) is easy to reimplement or replace independently.
- **DECISION (proposed)**: **WRAP**. Never `REUSE_AS_IS` (no budget/
  correlation-ID discipline, no ai-maturity-diagnostic evidence framing);
  never `REJECT` (genuinely useful public-index acquisition that already
  encodes the right epistemic caution).

### YouTube

- **SOURCE**: `scripts/social_search/youtube.py` — `search_youtube`, plus
  helpers `_youtube_transcript_ytdlp`, `_youtube_transcript_direct`,
  `_youtube_transcript_sc`, `_youtube_comments_ytdlp`.
- **CAPABILITY**: search cascade `yt-dlp` search →
  (empty) optional ScrapeCreators → (empty) DuckDuckGo
  `site:youtube.com/watch` fallback (lines 59-81); enrichment cascade for
  transcripts `yt-dlp` captions → direct HTTP caption track → optional
  ScrapeCreators (lines 41-51); top-comments via `yt-dlp --write-comments`
  (line 52-58).
- **LICENSE**: MIT (repo-wide). `yt-dlp` itself is an external
  Unlicense-licensed binary dependency, invoked via `subprocess`, not
  vendored.
- **CURRENT MATURITY**: solid cascade design with per-stage try/except and
  timeouts (`timeout=45`/`60`/`120`); one dedicated test
  (`test_youtube_transcript_cascade_public_before_commercial`,
  tests file line 47-55).
- **REUSE SURFACE**: `search_youtube` function as a callable unit is
  directly reusable; it degrades gracefully to a web-index fallback if
  `yt-dlp` is absent from the host, which matters for a hosted/CI
  deployment of `ai-maturity-diagnostic` that may not ship `yt-dlp`.
- **ADAPTATION REQUIRED**: `yt-dlp` is a `shutil.which` runtime dependency —
  `ai-maturity-diagnostic`'s execution environment(s) must either bundle it
  or accept the (already-implemented) HTTP-caption/web-index degradation
  path as the default; budget/correlation wrapper same as LinkedIn;
  transcript text is trimmed to ≤ ~1800 words / 12000 chars in-repo
  (`_clean_vtt`, `_youtube_transcript_sc`) which is friendlier to
  `CanonicalEvidenceV1.excerpt`'s 1000-char `maxLength` than most sources
  but still needs a second truncation at the mapping boundary.
- **SECURITY-PRIVACY**: no authenticated YouTube session; comments/
  transcripts are pulled from public captions/comments only
  (`limitations("youtube")`, `search_social_networks.py:20`).
- **COUPLING**: runtime dependency on an external binary (`yt-dlp`); no
  coupling to ai-maturity-diagnostic.
- **MAINTENANCE**: `yt-dlp` is actively maintained upstream but is a moving
  target against YouTube's anti-scraping changes — this is an operational
  risk inherited by any adopter, not specific to this repo.
- **TEST STRATEGY**: keep the repo's cascade-order test as a contract test;
  add a CI check (or accept the existing `qa.yml` pattern) that `--doctor`
  reports `yt_dlp` availability so ai-maturity-diagnostic ops can see the
  degradation mode it is running in.
- **EXIT STRATEGY**: same as LinkedIn — plain function boundary, low
  switching cost.
- **DECISION (proposed)**: **WRAP** (search + transcript + comments as one
  capability, budget-wrapped — transcripts especially should be
  rate/cost-bounded since `yt-dlp` invocations are comparatively slow).

### X (Twitter)

- **SOURCE**: `scripts/social_search/research.py` — `search_x`.
- **CAPABILITY**: two DuckDuckGo lanes, `site:x.com` and `site:twitter.com`
  (lines 12-18); no first-party API use (X's API is paid/restricted, so
  this repo doesn't touch it).
- **LICENSE**: MIT.
- **CURRENT MATURITY**: minimal — 7 lines, no dedicated test beyond the
  generic dedupe test; genuinely "index-only," explicitly flagged as
  `authenticated_x_access: False` and "not a complete feed"
  (`limitations("x")`).
- **REUSE SURFACE**: trivial function, easy to call as-is once wrapped;
  low signal density (web-index coverage of X is thin) so expectations
  should be set low in the ADR.
- **ADAPTATION REQUIRED**: budget/correlation wrapper only; no source-
  specific complexity to adapt.
- **SECURITY-PRIVACY**: no auth, no scraping of logged-in timelines.
- **COUPLING**: none.
- **MAINTENANCE**: trivially small surface, easy to keep or replace.
- **TEST STRATEGY**: contract test on the `Result` shape; no source-
  specific behavior worth testing beyond what the repo already has.
- **EXIT STRATEGY**: trivial to drop or reimplement.
- **DECISION (proposed)**: **WRAP** as a low-priority/low-confidence
  source; acceptable to defer to a later slice of E14 given its thin
  signal.

### Reddit

- **SOURCE**: `scripts/social_search/community.py` — `search_reddit`,
  `_reddit_comments`, `_reddit_ref`.
- **CAPABILITY**: public Reddit search RSS/Atom (`reddit.com/search.rss`)
  as primary path, falling back to DuckDuckGo `site:reddit.com` if the RSS
  path raises or returns nothing (lines 55-73); comment enrichment via
  public Shreddit JSON endpoints (`_reddit_comments`, lines 44-54) tried
  against two URL shapes with `retries=1`.
- **LICENSE**: MIT.
- **CURRENT MATURITY**: reasonably mature — explicit XML namespace
  handling, date-window filtering, graceful fallback; one dedicated test
  (`test_reddit_comment_ref`, line 56-58) covers the regex extraction only,
  not the network paths (appropriately, since tests are offline-only).
- **REUSE SURFACE**: `search_reddit` and the small `_reddit_ref` regex
  helper are reusable as-is; comment enrichment is best-effort by design
  (`limitations("reddit")`) and should be treated as optional metadata,
  never a required field downstream.
- **ADAPTATION REQUIRED**: budget/correlation wrapper only.
- **SECURITY-PRIVACY**: public RSS/JSON endpoints only, no Reddit API
  token, no authenticated session.
- **COUPLING**: none.
- **MAINTENANCE**: Reddit has a history of tightening anonymous API/RSS
  access; the repo's own fallback-to-web-index path is the mitigation
  already built in.
- **TEST STRATEGY**: keep `_reddit_ref` unit test; add a smoke check on
  `--doctor`/manual run cadence (already recommended in repo's own
  `UPSTREAM_AUDIT.md` QA section) rather than mocking Reddit's endpoints.
- **EXIT STRATEGY**: trivial function boundary.
- **DECISION (proposed)**: **WRAP**.

### Hacker News

- **SOURCE**: `scripts/social_search/community.py` — `search_hackernews`.
- **CAPABILITY**: Algolia HN Search API (`hn.algolia.com`), keyless,
  official, stable; optional per-story top-comments enrichment via the
  Algolia items endpoint (lines 6-17).
- **LICENSE**: MIT; Algolia's HN API is a free public API with no key
  required.
- **CURRENT MATURITY**: highest maturity of the nine sources — a genuinely
  stable, documented, versioned public API, not scraped HTML.
- **REUSE SURFACE**: **REUSE_AS_IS**-grade candidate for the acquisition
  logic itself; only the budget/correlation/evidence-mapping wrapper is
  new work.
- **ADAPTATION REQUIRED**: budget/correlation wrapper only.
- **SECURITY-PRIVACY**: no auth, fully public data.
- **COUPLING**: none.
- **MAINTENANCE**: Algolia's HN Search API is a long-lived, low-churn
  public service; low ongoing maintenance risk.
- **TEST STRATEGY**: contract test on `Result` shape is sufficient; this
  is the lowest-risk source to build the wrapper reference implementation
  against first.
- **EXIT STRATEGY**: trivial.
- **DECISION (proposed)**: **REUSE_AS_IS** for the acquisition function,
  **WRAP** at the call boundary (every source needs the budget/correlation
  wrapper — see §3 — so "as-is" here means the function body, not the
  final integration).

### GitHub

- **SOURCE**: `scripts/social_search/community.py` — `search_github`,
  `github_token`, `github_headers`.
- **CAPABILITY**: anonymous GitHub REST search (`/search/repositories`,
  `/search/issues`) with optional `GITHUB_TOKEN`/`GH_TOKEN`/`gh auth` for
  quota only, never a hard requirement (lines 19-40); issue/PR comment
  enrichment via the `comments_url` from search results.
- **LICENSE**: MIT; GitHub's public REST API terms apply to usage, not to
  this repo's code.
- **CURRENT MATURITY**: production-shaped; handles both repo and issue/PR
  result kinds with distinct scoring bases.
- **REUSE SURFACE**: directly reusable; `ai-maturity-diagnostic` may
  already have its own GitHub credential handling (worth checking for a
  `GITHUB_TOKEN`/`gh auth` convention already in use elsewhere in the repo
  before wiring this one in, to avoid two independent token-lookup
  conventions).
- **ADAPTATION REQUIRED**: budget/correlation wrapper; verify no existing
  GitHub-token convention in `ai-maturity-diagnostic` collides.
- **SECURITY-PRIVACY**: anonymous-first; token usage is quota-only,
  read-only REST calls.
- **COUPLING**: none beyond the optional token env var.
- **MAINTENANCE**: GitHub's REST API is stable and versioned; low risk.
- **TEST STRATEGY**: contract test on `Result` shape.
- **EXIT STRATEGY**: trivial.
- **DECISION (proposed)**: **REUSE_AS_IS** for the function body, **WRAP**
  at the integration boundary.

### arXiv

- **SOURCE**: `scripts/social_search/research.py` — `search_arxiv`.
- **CAPABILITY**: arXiv's public Atom export API (`export.arxiv.org/api/
  query`), keyless, official.
- **LICENSE**: MIT; arXiv API is free/public.
- **CURRENT MATURITY**: high — simple, correct Atom parsing, date-window
  filtering, author list flattening.
- **REUSE SURFACE**: **REUSE_AS_IS**-grade for the function body.
- **ADAPTATION REQUIRED**: budget/correlation wrapper only.
- **SECURITY-PRIVACY**: fully public, no auth.
- **COUPLING**: none.
- **MAINTENANCE**: arXiv's API is long-lived and low-churn.
- **TEST STRATEGY**: contract test on `Result` shape.
- **EXIT STRATEGY**: trivial.
- **DECISION (proposed)**: **REUSE_AS_IS** for the function body, **WRAP**
  at the integration boundary. Lowest relevance to a GTM sales-intelligence
  product unless E14's use case includes technical/AI-research signal
  detection for a target account.

### Perplexity

- **SOURCE**: `scripts/social_search/research.py` — `search_perplexity`.
- **CAPABILITY**: if `PERPLEXITY_API_KEY` exists, calls Perplexity's
  first-party Search API (`api.perplexity.ai/search`, POST, dated window
  filters); otherwise transparently relabels a `search_web` result set as
  `source="perplexity"` with `perplexity_api_used: False` (lines 19-29).
  This is the one source whose *keyless path is a rename of another
  source*, not an independent public API.
- **LICENSE**: MIT for the wrapper code; Perplexity's API itself is a
  commercial product requiring an account/key, but this repo does **not**
  require it — this is a good example of the "optional commercial
  providers... require explicit user authorization plus an existing
  environment key" rule already baked in (`CLAUDE.md`).
- **CURRENT MATURITY**: functionally complete but the keyless fallback
  path is arguably mislabeling (a `web` result relabeled `perplexity`
  could be surprising downstream if the `perplexity_api_used` flag isn't
  checked). Worth flagging in the mapping layer.
- **REUSE SURFACE**: reusable, but the mapping layer (§4) must read
  `metadata.perplexity_api_used` and `metadata.fallback` before treating a
  "perplexity" result as anything other than a web result.
- **ADAPTATION REQUIRED**: budget/correlation wrapper; explicit
  `PERPLEXITY_API_KEY` gate check before wiring into any workspace that
  hasn't opted in (this is a paid, keyed provider even though this repo's
  default path doesn't require the key — the *moment a key exists in the
  environment*, Perplexity is used, which is a different authorization
  model than LinkedIn's `--allow-commercial` flag; the wrapper should
  normalize this to the same "explicit user authorization" gate the other
  commercial paths use, not just "key present").
- **SECURITY-PRIVACY**: no key persistence in this repo (`README.md:101`);
  key is read from environment only, per-call.
- **COUPLING**: optional coupling to a commercial API vendor.
- **MAINTENANCE**: Perplexity's Search API is a maintained commercial
  product; risk is vendor pricing/availability, not code rot.
- **TEST STRATEGY**: contract test must assert the label-swap behavior on
  the no-key path so downstream code never silently treats a relabeled web
  result as if it came from Perplexity's actual index.
- **EXIT STRATEGY**: trivial to disable by never setting the key; trivial
  to drop the source entirely.
- **DECISION (proposed)**: **ADAPT** — the keyless fallback's relabeling
  behavior needs an explicit authorization gate matching
  `ai-maturity-diagnostic`'s own commercial-provider consent pattern
  before being wired in, not a straight `WRAP`.

### Web

- **SOURCE**: `scripts/social_search/core.py` — `search_web`, `web_index`,
  `DDGParser`, `unwrap_ddg`, `canonical_url`, `dedupe`.
- **CAPABILITY**: DuckDuckGo HTML search index scrape via a minimal
  hand-rolled `HTMLParser` subclass (`DDGParser`, lines 58-71); this is
  also the fallback mechanism used by LinkedIn, X, Reddit, YouTube and
  Perplexity when their primary path fails or is absent — i.e. **`web_index`
  is the single most load-bearing function in the whole repo**, not just
  the `web` source's own implementation.
- **LICENSE**: MIT.
- **CURRENT MATURITY**: functional but structurally fragile — depends on
  DuckDuckGo's HTML markup (`class="result__a"`/`result__snippet"`) not
  changing; no test in the suite actually exercises `DDGParser` against
  live or fixture HTML (the test suite is intentionally offline-only per
  `README.md`'s QA section, so this is untested against real DuckDuckGo
  markup drift).
- **REUSE SURFACE**: this is also the core dedup/scoring/URL-canonicalization
  utility library (`dedupe`, `canonical_url`, `relevance`, `trim`,
  `merge_meta`, `window`) used by every other source — reusing `web_index`
  effectively means reusing the whole `core.py` utility layer, which is
  reasonable, but the single point of failure risk (DuckDuckGo markup
  change silently degrading six of nine sources at once) should be called
  out explicitly in the ADR.
- **ADAPTATION REQUIRED**: budget/correlation wrapper; recommend adding an
  explicit "web_index came back empty/malformed" health signal distinct
  from "source had zero results for this query," since today both look
  identical from the caller's perspective (an empty list) — this matters
  for the blocker/resolver mapping in §5 (a `web_index` markup break should
  surface as an actionable "acquisition broken" blocker, not a silent
  "no signals found for this account").
- **SECURITY-PRIVACY**: no auth; scrapes DuckDuckGo's public HTML search
  result page, not an API with documented terms — this is the one place
  where "public-first" acquisition brushes against a host's likely-implicit
  scraping tolerance rather than a published API contract. Worth an
  explicit note in the ADR that this is accepted risk, not a documented
  legal permission.
- **COUPLING**: implicit coupling of six other sources to this one
  function's continued correctness.
- **MAINTENANCE**: highest maintenance risk of the whole repo precisely
  because it is the most load-bearing and least API-contract-backed piece.
- **TEST STRATEGY**: add a fixture-based unit test (saved DuckDuckGo HTML
  snapshot) to catch markup drift in CI, both in the upstream repo and/or
  in whatever thin wrapper module `ai-maturity-diagnostic` builds around it.
- **EXIT STRATEGY**: because `web_index` is centralized, a swap (e.g. to
  Bing's or another engine's HTML, or to a paid SERP API) is a single-
  function replacement, not a nine-source rewrite — this is a genuine
  architectural strength worth preserving in any port.
- **DECISION (proposed)**: **ADAPT** — reuse the function, but the wrapper
  must add markup-drift detection and treat `web_index` health as a
  first-class, cross-cutting operational signal, not just "one more source."

## 2. Cross-cutting reuse classification summary

| Source | Function(s) | Decision |
|---|---|---|
| LinkedIn | `search_linkedin` | WRAP |
| YouTube | `search_youtube` | WRAP |
| X | `search_x` | WRAP (low priority) |
| Reddit | `search_reddit` | WRAP |
| Hacker News | `search_hackernews` | REUSE_AS_IS (function body) + WRAP (integration) |
| GitHub | `search_github` | REUSE_AS_IS (function body) + WRAP (integration) |
| arXiv | `search_arxiv` | REUSE_AS_IS (function body) + WRAP (integration) |
| Perplexity | `search_perplexity` | ADAPT (authorization gate) |
| Web | `search_web`/`web_index` | ADAPT (markup-drift health signal) |
| Shared runner | `run_all`, `dedupe`, `doctor` | EXTRACT_PATTERN (fan-out/isolation/doctor design informs the wrapper; the concurrency/reporting shape is worth copying, the module itself should not be imported verbatim into a product that already owns `run_manager.py`/`execution_policy.py`) |
| DuckDuckGo scraping mechanism itself | `DDGParser`, `unwrap_ddg` | REFERENCE_ONLY (accept as an operational dependency, do not treat as a stable contract) |

No source is `REJECT`. Nothing in this repo proposes a Company/Demand/Fit
object, an authenticated LinkedIn session, or a persisted credential —
consistent with the harvest strategy's constraints.

## 3. Normalized result schema and mapping onto existing evidence primitives

### search-social-networks' own schema

`social_search.core.Result` (`core.py:9-11`):

```python
@dataclass
class Result:
    source: str
    title: str
    url: str
    snippet: str = ""
    date: str | None = None
    author: str | None = None
    score: float = .5
    metadata: dict[str, Any] = field(default_factory=dict)
```

Plus, at the run level, `SourceRun` (`core.py:12-14`: `source`, `status`,
`results`, `error`, `elapsed_ms`) and the CLI payload's per-source
`limitations` list (`search_social_networks.py:20`) and top-level
`summary`/`cross_source_results`.

### Mapping table (Result field → ai-maturity-diagnostic primitive field)

This repo's own north star ("evidence before inference; gate before score;
fit before person," `signal_v1.schema.yaml` x-rules) means a raw `Result`
must land as **evidence first**, with a **signal** as the thin
prioritization pointer on top — never as a `Claim` directly, and never as
a `CanonicalCompanyV1`/`CanonicalPersonV1` write.

| `Result` field | `CanonicalEvidenceV1` (`contracts/evidence_v1.schema.yaml`) | `CanonicalSignalV1` (`contracts/signal_v1.schema.yaml`) |
|---|---|---|
| `source` (string, e.g. `"linkedin"`) | `source.kind = "public"`, `source.ref = source` string kept in metadata/locator context | `source.kind = "public"`, `source.ref` |
| `url` | `locator` | `source.ref` (locator of the source) |
| `title` + `snippet` (trimmed) | `excerpt` (must be re-truncated to ≤1000 chars — the repo's own `trim()` caps vary from 350 to 1600/12000 chars depending on source, so the mapping layer, not the source repo, owns the final 1000-char cut) | not carried (signals are thin pointers, not text) |
| `date` | `dated_at` (needs conversion: `Result.date` is often `YYYY-MM-DD`, `evidence_v1` wants full `date-time` — pad to midnight UTC or use `observed_at` for the acquisition timestamp instead when `date` is null, which happens e.g. for LinkedIn `/in/` profile hits) | `observed_at` (when this signal was captured by the runner, not the underlying post's publish date) |
| `author` | not a schema field; keep in `entity_refs`-adjacent context only if/when resolved to a `CanonicalPersonV1`, never write it as a canonical person from this alone | not carried |
| `score` (0-1 relevance heuristic) | not a schema field — do not conflate `Result.score` (repo-internal ranking heuristic) with `evidence_grade` | not carried directly, but can inform triage ordering in the UI layer, outside the canonical record |
| `metadata` | free-form; the acquisition_method/*_access/*_validation flags (e.g. `live_role_validation: False`) should be preserved verbatim, since they are exactly the epistemic caveats `evidence_v1`'s `evidence_grade` and the LinkedIn LI-POL invariants care about | free-form is not part of `signal_v1`'s schema (`additionalProperties: false`) — so per-source metadata lives on the `Evidence` record, and the `Signal` only carries `dedup_key`/`freshness`/`provenance` |
| (derived) | `evidence_grade`: **never** `P1`/`P2` automatically from an unauthenticated public-index hit; default new-from-harvest evidence to `U1` (unverified) or `W1` per `08_EVIDENCE_DECISION_AND_GATES.md`'s grading rubric — an explicit business-rule decision for the ADR, not something this document assigns unilaterally | `provenance.epistemic_status`: default `"hypothesis"` or `"unknown"`, never `"fact"`, for anything sourced purely from `search-social-networks` without corroboration |
| `SourceRun.status` (`ok`/`empty`/`error`) | n/a (evidence records are per-hit, not per-run) | drives the *ingestion* pipeline's health, not a signal field — see §5 for the blocker mapping |

Key constraint carried forward from the task brief and confirmed by reading
`signal_v1.schema.yaml`'s own x-rules: **a signal never proves demand**, and
`research_case_v1.schema.yaml`'s x-rule that "ResearchCase never references
a product/offer object" — so nothing from `search-social-networks` should
ever populate a `demand_v1`/`fit_assessment_v1`/`product_fit` field directly.
The harvested `Result` stops at Evidence + Signal; anything past that
(Claim promotion, Demand inference, Fit scoring) is `ai-maturity-diagnostic`'s
own existing machinery consuming that evidence, exactly as it already does
for other Epic 03/04 evidence sources.

`CanonicalClaimV1` (`claim.schema.yaml`) is reachable only as a second step:
a human or an existing research workflow cites one or more `evidence_id`s
from harvested evidence to assert a `claim_type: hypothesis` (never
`fact` from harvest evidence alone, per the claim contract's own
`validate_claim_lineage` rule requiring a non-`N0` grade for a `fact`
claim — and harvested public-index evidence should not be graded above `U1`/`W1`
without independent corroboration).

## 4. Wrapper for budget/checkpoint/correlation-ID discipline

`ai-maturity-diagnostic` already has three cooperating primitives every
Epic 01+ integration uses, and E14 should follow the same pattern rather
than inventing a fourth:

1. **`app/execution_context.py`** — `correlation_scope()`/
   `current_correlation_id()`, a `contextvars`-based correlation ID
   propagated across the call. E14's wrapper should open a
   `correlation_scope()` at the top of a harvest run and pass that ID
   into every log line / evidence record it writes.
2. **`app/execution_policy.py`** — `BudgetEnvelope` (max_calls,
   max_input_tokens, max_output_tokens, max_cost_units, max_wall_seconds)
   and `BudgetLedger.consume()`/`.status()`, which returns a `BudgetStatus`
   with `mode ∈ {normal, checkpoint_required, blocked}` once utilization
   crosses 0.8/1.0. Each `search_social_networks` source call should be
   metered as one `Usage(calls=1, wall_seconds=elapsed_ms/1000, ...)`
   against a workspace-scoped `BudgetLedger`, exactly like any other
   external-tool call in this codebase; `SourceRun.elapsed_ms` already
   gives the wrapper `wall_seconds` for free.
3. **`app/run_manager.py`** — `RunManager.prepare/start/checkpoint/
   complete/block/fail/cancel/resume`, a durable, resumable run record
   with `resume_token`. A harvest run over 9 sources fans out with
   `ThreadPoolExecutor` today (repo's `run_all`); the wrapper should
   `prepare()` a run per harvest invocation, `start()` it, and
   `checkpoint()` after each source completes (mirroring the repo's own
   per-source isolation) so a partial harvest (e.g. 6/9 sources done
   before a budget-exceeded interrupt) is resumable rather than
   restarted from zero.

Concrete wrapper shape (proposal, not implemented here):

```
app/harvest_runner.py (new, E14)
  def run_harvest(root, workspace_id, actor_id, query, sources, *, days, limit, enrich, allow_commercial) -> HarvestRun:
      with correlation_scope() as corr_id:
          run_mgr = RunManager(root, workspace_id, actor_id)
          prepared = run_mgr.prepare("harvest.search_social_networks", input_ref=query)
          run_mgr.start(prepared.run["run_id"])
          ledger = BudgetLedger(root, workspace_id, envelope)
          for source in sources:
              ledger.consume(Usage(calls=1))       # BudgetExceeded -> run_mgr.block(...)
              handler = SEARCHERS[source]
              run = handler(query, days, limit, enrich, allow_commercial)
              # map Result -> Evidence/Signal here, tag with corr_id
              run_mgr.checkpoint(prepared.run["run_id"], {"source": source, "status": ...})
          run_mgr.complete(prepared.run["run_id"], output_refs=[...])
```

This is exactly the pattern `run_manager.py`'s own docstring calls
"durable, resumable execution run state for local-first workflows" —
`search-social-networks`' `run_all`/`doctor` functions are a good
**EXTRACT_PATTERN** reference for the fan-out and isolated-failure shape
(one thread per source, one try/except per source, one status per source)
but the actual state/budget/resume bookkeeping should be
`ai-maturity-diagnostic`'s own, not reimplemented.

`SourceRun.error` (a `f"{type(exc).__name__}: {exc}"` string) maps cleanly
onto `RunManager.fail(run_id, code, message, retryable=...)` — the wrapper
would classify which exception types are retryable (network timeouts,
HTTP 5xx/429 — already the same status codes `execution_policy.RetryPolicy`
treats as retryable) versus not (e.g. `argparse` misuse, unknown source).

## 5. LinkedIn epistemic discipline and how to preserve it

**How `search-social-networks` avoids over-claiming today:**

- Every public-lane LinkedIn `Result` is stamped with three explicit
  `False` flags in `metadata`: `authenticated_linkedin_access`,
  `live_role_validation`, `canonical_identity_resolution`
  (`linkedin.py:11`).
- The repo's own `limitations("linkedin")` function
  (`search_social_networks.py:20`) attaches, per run, the sentence
  "Public LinkedIn index is fallback/corroboration, not proof of current
  role or canonical identity."
- `doctor()`'s `guarantees` block machine-asserts
  `authenticated_linkedin_scraping: False` and `credential_persistence:
  False` (`search_social_networks.py:18`) — this is checkable at
  integration time, not just documented.
- The README's own hierarchy diagram (`README.md:153-165`) is: optional
  authorized provider → public index fallback → **"validation
  primaire/officielle ou humaine"** for any "décision sensible (rôle
  courant, identité, autorité)."

**How `ai-maturity-diagnostic` already enforces the same discipline
independently**, which is the important finding here — this is not a gap
E14 needs to invent a policy for, it's a case of two independently
designed systems agreeing:

- `AGENTS.md:135-148` defines `LI-POL-001` through `LI-POL-008` almost
  point-for-point matching the harvested repo's own guarantees: "le projet
  fonctionne entièrement sans plugin LinkedIn" (LI-POL-001), "aucune
  implémentation de connecteur authentifié avant les gates documentés"
  (LI-POL-002), "la sortie connecteur est une preuve externe, jamais une
  identité canonique" (LI-POL-005), and critically LI-POL-008: "absence,
  refus, panne ou couverture insuffisante du plugin déclenche le fallback
  public; si celui-ci ne suffit pas à établir un rôle courant, une identité
  ou une relation sensible, router ensuite vers une validation
  primaire/humaine sans bloquer la qualification."
- `contracts/role_validation_request.schema.yaml` formalizes the "route to
  human/primary validation" step as its own object with `purpose: const
  current_role_validation` and the explicit x-rule "A request does not
  authorize retrieval, storage, merge, or outreach."
- `contracts/external_identity_mapping.schema.yaml` formalizes the
  "external hit is an alias, not identity" boundary with
  `status ∈ {candidate, validated, rejected, expired}` and the x-rule
  "External identifiers are aliases and never replace internal IDs,"
  plus "This object is private and must not enter Git with real
  identifiers."

**Preserving this once wired in**: a LinkedIn `Result` from
`search-social-networks`, once mapped to `CanonicalEvidenceV1` (§3), should
at most create an `ExternalIdentityMapping` with `status: "candidate"` —
never `"validated"` — and the wrapper must never let a harvested LinkedIn
hit alone flip a `role_validation_request` to resolved, or write a
`current_role` onto a `CanonicalPersonV1`. That promotion path is already
gated by `role_validation_request.schema.yaml` and LI-POL-008's explicit
"route to human/primary validation" requirement; E14's job is to feed that
existing gate with better-triaged candidate evidence, not to bypass it.
`app/research_routes.py`'s own docstring reinforces the same "product-blind"
posture research must keep even as it consumes such evidence.

## 6. Propagating per-source ok/empty/error status into the blocker/resolver UX

`ai-maturity-diagnostic`'s blocker pattern (`contracts/blocker.schema.yaml`,
`app/blocker_actions.py`) is "Blocker = action à résoudre": a blocker
record names a `category`, `severity`, `message`, `required_state`,
`cta_label`/`cta_input`, and a `postcondition` — i.e. it is always paired
with a concrete next action, not a bare error.

`search-social-networks`' run-level status already gives the wrapper
almost everything needed to construct that record without inventing new
categories:

| Repo signal | Blocker mapping (proposed) |
|---|---|
| `SourceRun.status == "error"` with a **required** source (e.g. the account's primary evidence channel) | `category: "runtime"`, `severity: "blocker"` if the source is load-bearing for this research case, else `"warning"`; `message` built from `SourceRun.error` (`f"{type}: {msg}"`); `cta_label`: "Retry this source" / "Continue without <source>"; `postcondition`: "source status is ok or explicitly accepted as skipped" |
| `SourceRun.status == "empty"` | Not a blocker by default — an empty source is a normal outcome (`doctor()`'s own model treats `empty` and `ok` as both non-failing: CLI exit code is `0 if any(r.status=="ok" ...)`). Surface as an informational note on the research case, not a blocker, unless **all** sources for a case come back empty, in which case raise one `category: "human_review"` blocker: "no public evidence found for this account across N sources" with `cta_label: "Add evidence manually"`. |
| `web_index` (DuckDuckGo) markup drift (§1, Web source) — detectable when the `web` source and every source that falls back to it all return `error`/`empty` simultaneously across many unrelated queries | `category: "runtime"`, `severity: "critical"`, `message`: "public web index acquisition appears broken"; this is the one case worth a dedicated correlated-failure detector in the wrapper, since it is systemic rather than per-query. |
| `BudgetExceeded` (from the wrapper's `BudgetLedger`, §4) | `category: "runtime"`, `severity: "blocker"`; `cta_label`: "Request additional budget" / "Narrow the query"; matches how budget exhaustion should already be surfaced elsewhere per `execution_policy.py`'s `BudgetStatus.mode == "blocked"`. |
| ScrapeCreators/Perplexity commercial path requested but no key or no `--allow-commercial`-equivalent consent | `category: "security"` or `"human_review"`; `cta_label`: "Authorize commercial enrichment for this workspace"; `postcondition`: "workspace policy explicitly authorizes provider X." This mirrors LI-POL-003's "accès officiel et authentification approuvée uniquement." |
| LinkedIn public lane insufficient to resolve a sensitive claim (role/identity) | `category: "role"`, matching the existing `role` blocker category already in `blocker.schema.yaml`'s enum, `cta_label`: "Request role validation" wired to `role_validation_request` creation (§5) — this reuses an already-modeled blocker category, no schema change needed. |

Two things worth flagging for the ADR: (a) `blocker.schema.yaml`'s
`category` enum already includes `runtime`, `human_review`, `security`,
and `role` — every mapping above fits an existing category, so **no
contract change is proposed**; (b) the audit-log pattern in
`app/blocker_actions.py` (append-only, `study_id`-scoped, `cancel`/
`step_back`/`force` actions with mandatory `reason` on `force`) is a
different, narrower mechanism (qualification-pipeline dashboard actions)
than the generic `blocker.schema.yaml` object — the wrapper should emit
plain `blocker.schema.yaml`-shaped records for harvest failures, and only
touch `BlockerActionLog` if harvest failures ever need to be tracked
through that specific qualification-step audit trail (unclear from this
audit alone whether E14 sits inside that six-step `STEP_ORDER` pipeline —
flag as an open question for the ADR).

## 7. Discover vs. Research vs. Targeting placement

From `docs/gtm-transformation/04_INFORMATION_ARCHITECTURE.md`'s navigation
table and `app/frontend/gtm-spaces.js`'s space config (`discover`/
`research`/`targets` entries, lines 5-9):

| Space | Job (from IA doc) | Dominant objects | Which harvested sources conceptually belong here |
|---|---|---|---|
| **Discover** | "trouver signaux, personnes et entreprises" — broad discovery | Signal, Person, Company, List | Hacker News, arXiv, GitHub, general Web, and X — broad topic/account discovery, "who/what is out there talking about X," feeding `CanonicalSignalV1` records via `app/signal_store.py` / surfaced through `app/signal_routes.py`'s `/signals` and `queue-research` handoff. |
| **Research** | "comprendre le compte sans biais produit" — product-blind deep dive on an already-selected account | ResearchCase, Claim, Demand | YouTube (transcripts/comments as evidence for an already-identified company's public communications), Reddit (community discussion about a specific already-selected account/product), Perplexity (targeted corroboration search once a `ResearchCase` is open) — these feed `CanonicalEvidenceV1`/`CanonicalClaimV1` against a `research_case_id` via `app/research_case_store.py`/`app/claim_store.py`, surfaced through `app/research_routes.py`. |
| **Targets** | "construire le buying committee et le chemin relationnel" — person-level, post-Fit | TargetPlan, Role, Relationship | LinkedIn is the clearest fit here **once a Fit decision already exists**: LinkedIn's `/in/` profile-index lane is about *people*, and per `04_INFORMATION_ARCHITECTURE.md`'s explicit ordering ("fit avant ciblage personne," `AGENTS.md:118`) and LI-POL-008's role-validation routing, LinkedIn evidence should only feed `TargetPlan`/`Role`/`Relationship` objects after Fit, going through `role_validation_request`/`external_identity_mapping`, not directly from Discover. |

Important nuance: the **same LinkedIn acquisition function** can be called
from either Discover (a `/posts`/`/pulse` hit about a company signals "this
account is publicly discussing X," which is Discover-appropriate, product-
blind, pre-Fit) or Targets (an `/in/` hit about a named person, post-Fit,
feeding a `TargetPlan`). The source function itself is persona/space-
neutral (exactly as `search-social-networks`' own `docs/ARCHITECTURE.md`
intends); it is the **calling context and which canonical object the
result is mapped onto** that determines Discover vs. Targets placement —
this argues for one shared harvest wrapper (§4) parameterized by "which
space/case is asking," not per-space copies of the acquisition call.

## 8. License / maintenance / security-privacy summary

- **LICENSE**: MIT (`/home/user/search-social-networks/LICENSE`), copyright
  "Matt Van Horn (upstream portions/concepts where applicable)." The repo
  is an independent adaptation of `mvanhorn/last30days-skill` (also MIT);
  `NOTICE.md` explicitly states "does not import or call the upstream
  repository at runtime." MIT is fully compatible with vendoring/adapting
  into `ai-maturity-diagnostic`, subject to normal MIT attribution
  (retain copyright/license text for the portions reused).
- **Hard external service dependencies**: none that are mandatory.
  Everything keyless-required is either a documented public API (HN
  Algolia, arXiv Atom, GitHub anonymous REST, Reddit RSS) or a DuckDuckGo
  HTML scrape (`web_index`) used both directly (`web`, `x`, LinkedIn public
  lane) and as a fallback for others. The only binary dependency is
  `yt-dlp`, itself optional (degrades to HTTP captions/web-index).
- **Credential/env-key requirements beyond optional enrichment**: none.
  `doctor()`'s `guarantees` block (`search_social_networks.py:18`)
  machine-asserts `keyless_core: True`, `commercial_required: False`,
  `commercial_disabled_by_default: True`, `credential_persistence: False`.
  `SCRAPECREATORS_API_KEY` (YouTube/LinkedIn enrichment) and
  `PERPLEXITY_API_KEY` (Perplexity) are the only keys the code reads, both
  optional, both read from environment per-call, never persisted or logged.
  `GITHUB_TOKEN`/`GH_TOKEN` is optional and quota-only.
- **Privacy / "public-first, graceful degradation, no authenticated
  LinkedIn scraping"**: confirmed at the code level (§5) — no cookies, no
  browser automation anywhere in the repo (`grep`-verified: no
  `selenium`/`playwright`/cookie-jar imports exist in
  `scripts/social_search/`), and the `doctor()` guarantee is a testable
  claim, not just a README assertion.
- **Residual risk not covered by the above**: the DuckDuckGo HTML scrape
  (§1 Web) is the one place where "public-first" acquisition rests on
  *tolerated* rather than *documented* access — this is a reasonable,
  common pattern for this class of tool, but it is a scraping dependency
  on a third party's HTML markup and implicit tolerance, not a published,
  stable API contract, and should be named as such (not glossed over) in
  any ADR that ratifies this harvest.

## 9. Proposal statement (required closing)

This document is a **proposal for a human/architecture-owner to ratify**,
produced to satisfy the harvest gate (G4: "no new search engine, editor,
exporter or notes system is built before auditing existing repos and
libraries") for the search/acquisition capability a candidate Epic E14
would otherwise need to build. Nothing in this document authorizes writing
or modifying runtime code in either `search-social-networks` or
`ai-maturity-diagnostic`: the per-source DECISION classifications above
(a mix of REUSE_AS_IS, ADAPT, WRAP, EXTRACT_PATTERN and REFERENCE_ONLY,
with no REJECT) are recommendations only, and no wrapper, mapping layer,
blocker integration, or Epic E14 implementation work should begin until an
accepted ADR — written by the architecture owner, informed by this audit —
explicitly ratifies which sources are in scope, which DECISION each one
gets, and how the evidence/signal mapping in §3, the run/budget wrapper in
§4, the LinkedIn discipline in §5, the blocker mapping in §6, and the
Discover/Research/Targets placement in §7 are to be implemented.
