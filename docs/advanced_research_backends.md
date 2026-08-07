# Advanced research backends — public-first

## Purpose

Provide one deterministic acquisition layer for public evidence without changing the ownership or reasoning boundaries of the existing skills. The backend is `scripts/advanced_research.py`; it is optional infrastructure, not a new source of truth.

The implementation is intentionally independent from any external research-skill repository. No runtime import, submodule, package dependency, or cross-repository call is allowed.

## Source matrix

| Source | Acquisition | Credential | Primary use | Important limitation |
|---|---|---|---|---|
| web | public web index | none | broad discovery / triangulation | indexed coverage can be incomplete |
| Reddit | public RSS, web-index fallback | none | practitioner/community signals | qualitative signal, not representative sampling |
| YouTube | `yt-dlp` when available, web-index fallback | none | talks, interviews, demos, public transcripts | transcript coverage depends on subtitles |
| X / Twitter | public web index | none | recent public statements | not a complete feed |
| Hacker News | HN Algolia public API | none | technical/community signals | community selection bias |
| GitHub | GitHub public REST | optional `GITHUB_TOKEN`/`GH_TOKEN` | repositories, issues, PR signals | activity does not prove enterprise adoption |
| arXiv | public Atom API | none | research / technical frontier | paper publication does not prove deployment |
| LinkedIn | **public web index only** | none | discover public posts/articles/profile candidates | not a LinkedIn connector; cannot validate live role/identity |
| Perplexity | first-party Search API if `PERPLEXITY_API_KEY` already exists; web fallback otherwise | optional runtime env only | additional ranked discovery | never initiate billing or persist the key |

## CLI

```bash
python scripts/advanced_research.py "<query>" --source web --days 90 --limit 12 --pretty
python scripts/advanced_research.py "<query>" --source linkedin --days 180 --limit 12 --pretty
python scripts/advanced_research.py "<query>" --source youtube --days 180 --limit 8 --enrich --pretty
```

Output is normalized JSON with `source`, `title`, `url`, `snippet`, `published_at`, `author`, `relevance`, `metadata`, plus source-level `limitations`.

## Routing by existing skill

### Direct acquisition users

- `corporate-ai-strategy-intelligence`: web first; YouTube/X for executive statements; Perplexity only as discovery; primary corporate/IR evidence remains authoritative.
- `tech-leadership-org-intelligence`: web + LinkedIn public index + GitHub + YouTube. LinkedIn output may seed manual validation but never marks a role `current`.
- `ai-hiring-workspace-intelligence`: web and LinkedIn public index for job/career discovery, then official career pages and job descriptions for evidence.
- `ai-newsflow-sourcing-intelligence`: web + X + YouTube + Hacker News + GitHub + arXiv as appropriate; deduplicate event reprises before interpretation.
- `enterprise-demand-intelligence`: orchestrates source choice across its four evidence passes; it must not treat the acquisition relevance score as a business score.
- `enterprise-icb-mapping`: web only as a discovery lane to locate primary evidence of revenue-generating activity; classification remains grounded in dated company evidence.
- `product-icp-intelligence`: web/GitHub/Hacker News/arXiv can enrich product truth and alternatives; never query a named target account while this skill is active.
- `person-opportunity-targeting`: LinkedIn public index can create a **validation candidate** for role currency, never a `current` role observation by itself.

### Skills that must not perform external acquisition

- `network-contact-intake`: private-input normalization only. External identity observations belong to a later explicit resolution/validation step.
- `network-account-screening`: score only private-network research attractiveness. Do not improve the tier with public research signals.
- `network-study-orchestration`: lifecycle/queue only. It may trigger an enterprise research pass but does not research itself.

This separation prevents public evidence from contaminating private-network priors and preserves the existing handoff architecture.

## LinkedIn governance

The backend does **not** implement the deferred LinkedIn connector. It does not authenticate to LinkedIn, fetch authenticated LinkedIn pages, use cookies, automate a browser, message users, or write to LinkedIn.

Public-index results are discovery evidence with explicit flags:

- `connector_runtime: false`
- `authenticated_linkedin_access: false`
- `live_role_validation: false`
- `canonical_identity_resolution: false`

The existing `LI-POL-*` rules, PRD gates, connector contracts and deferred evaluation remain unchanged. An indexed profile or snippet can generate a validation task; it cannot close one.

## Evidence discipline

1. Preserve publication date when available and record retrieval date in the study ledger.
2. Record acquisition method and limitations.
3. Prefer primary sources before strengthening a claim.
4. Deduplicate syndicated coverage and event reprises.
5. Separate retrieval relevance from epistemic confidence and from any commercial score.
6. Keep `Non établi` when the accessible corpus is insufficient.
