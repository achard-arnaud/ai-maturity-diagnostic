# Advanced research backends — public-first core, provider-enhanced when approved

## Purpose

Provide one deterministic acquisition layer for public evidence without changing the ownership or reasoning boundaries of the existing skills. The backend is `scripts/advanced_research.py`; it is optional infrastructure, not a new source of truth.

The implementation is intentionally independent from any external research-skill repository. No runtime import, submodule, package dependency, or cross-repository call is allowed.

The general routing principle is:

```text
approved/native provider when available and permitted
        ↓ unavailable / denied / failed / incomplete
public or first-party keyless acquisition
        ↓
web-index fallback / triangulation
        ↓
primary or human validation when the decision needs stronger evidence
```

The Python backend owns the public fallback. Host-native tools (for example a future approved LinkedIn plugin) are invoked by the agent/skill layer because a local Python script cannot and must not impersonate a host connector.

## Source matrix

| Source | Baseline acquisition | Optional enhancement | Primary use | Important limitation |
|---|---|---|---|---|
| web | public web index | host-native web search | broad discovery / triangulation | indexed coverage can be incomplete |
| Reddit | public RSS, web-index fallback | comments where public endpoints allow it | practitioner/community signals | qualitative signal, not representative sampling |
| YouTube | `yt-dlp` when available, public/index fallback | transcripts/comments; host-native video search | talks, interviews, demos | transcript coverage depends on subtitles/platform reachability |
| X / Twitter | public web index | approved/native search if available | recent public statements | public index is not a complete feed |
| Hacker News | HN Algolia public API | discussion comments | technical/community signals | community selection bias |
| GitHub | GitHub public REST | existing `GITHUB_TOKEN`/`GH_TOKEN` or native GitHub connector | repositories, issues, PR signals | activity does not prove enterprise adoption |
| arXiv | public Atom API | host-native academic/web discovery | research / technical frontier | paper publication does not prove deployment |
| LinkedIn | public web index `/pulse/`, `/posts/`, `/in/` | **approved read-only plugin first, once gates pass** | professional/public evidence and role-validation candidates | fallback cannot validate live role/identity |
| Perplexity | public-web fallback | first-party Search API if `PERPLEXITY_API_KEY` already exists | additional ranked discovery | never initiate billing or persist the key |

## CLI

```bash
python scripts/advanced_research.py "<query>" --source web --days 90 --limit 12 --pretty
python scripts/advanced_research.py "<query>" --source linkedin --days 180 --limit 12 --pretty
python scripts/advanced_research.py "<query>" --source youtube --days 180 --limit 8 --enrich --pretty
```

Output is normalized JSON with `source`, `title`, `url`, `snippet`, `published_at`, `author`, `relevance`, `metadata`, plus source-level `limitations`.

## LinkedIn routing — provider first, public fallback

LinkedIn has two quality tiers, not two competing products.

### Tier 1 — approved connector/plugin

Use an official, approved read-only LinkedIn integration **only after** `LI-G0..LI-G6` permit it. The host agent should try this tier first when the connector is actually available and authorized.

Connector evidence remains external evidence. It is subject to purpose limitation, storage policy, provenance, merge gates and the `LI-POL-*` rules. A connector result is not automatically the canonical identity record.

### Tier 2 — public-index fallback

If Tier 1 is absent, refused, unavailable, rate-limited, fails, or returns insufficient coverage, run:

```bash
python scripts/advanced_research.py "<personne ou sujet>" --source linkedin --days <window> --limit <n> --pretty
```

This searches only publicly indexed LinkedIn surfaces:

- `/pulse/` — long-form articles, high-signal for authored positions;
- `/posts/` — public indexed posts;
- `/in/` — profile-index entries useful to generate validation candidates.

Tier 2 is also useful as corroboration when Tier 1 succeeds. It does **not** authenticate to LinkedIn and cannot by itself set `current_role=true`, merge identities, infer authority, or make outreach `ready`.

### Tier 3 — validation

For role currency, canonical identity, reporting line or authority decisions, insufficient Tier 1/Tier 2 evidence routes to an approved primary source or human validation. The research workflow remains useful even when LinkedIn is unavailable; only the strength of person-level claims is constrained.

## Routing by existing skill

### Direct acquisition users

- `corporate-ai-strategy-intelligence`: web first; YouTube/X for executive statements; Perplexity only as discovery; primary corporate/IR evidence remains authoritative.
- `tech-leadership-org-intelligence`: web + LinkedIn hierarchy + GitHub + YouTube. Try an approved LinkedIn provider first when available; otherwise public fallback. Neither tier establishes hierarchy without corroboration.
- `ai-hiring-workspace-intelligence`: web plus LinkedIn hierarchy for discovery, then official career pages and job descriptions for evidence.
- `ai-newsflow-sourcing-intelligence`: web + X + YouTube + Hacker News + GitHub + arXiv as appropriate; deduplicate event reprises before interpretation.
- `enterprise-demand-intelligence`: orchestrates source choice across its four evidence passes; it must not treat acquisition relevance as a business score.
- `enterprise-icb-mapping`: web only as a discovery lane to locate primary evidence of revenue-generating activity; classification remains grounded in dated company evidence.
- `product-icp-intelligence`: web/GitHub/Hacker News/arXiv can enrich product truth and alternatives; never query a named target account while this skill is active.
- `person-opportunity-targeting`: use approved LinkedIn evidence first if available; otherwise public fallback can create a **validation candidate**, never a `current` role observation by itself.

### Skills that must not perform external acquisition

- `network-contact-intake`: private-input normalization only. External identity observations belong to a later explicit resolution/validation step.
- `network-account-screening`: score only private-network research attractiveness. Do not improve the tier with public research signals.
- `network-study-orchestration`: lifecycle/queue only. It may trigger an enterprise research pass but does not research itself.

This separation prevents public evidence from contaminating private-network priors and preserves the existing handoff architecture.

## LinkedIn governance

`scripts/advanced_research.py` implements **only Tier 2**, the public fallback. It does not implement or emulate the deferred connector. It does not authenticate to LinkedIn, fetch authenticated LinkedIn pages, use cookies, automate a browser, message users, or write to LinkedIn.

Public-index results carry explicit limitations such as:

- `authenticated_linkedin_access: false`
- `live_role_validation: false`
- `canonical_identity_resolution: false`

The existing `LI-POL-*` rules, PRD gates, connector contracts and deferred evaluation remain in force. The architectural change is only the failure behavior: a missing/broken provider now falls back to useful public discovery before escalating unresolved person claims to validation.

## Evidence discipline

1. Preserve publication date when available and record retrieval date in the study ledger.
2. Record acquisition method, provider tier and limitations.
3. Prefer primary sources before strengthening a claim.
4. Deduplicate syndicated coverage and event reprises.
5. Separate retrieval relevance from epistemic confidence and from any commercial score.
6. Do not infer provider-grade freshness from public snippets.
7. Keep `Non établi` when the accessible corpus is insufficient.
