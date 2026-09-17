# MCP Opportunity Note — Research Note (CLAUDE_01 Workstream H)

**Status:** Research only. Not an implementation plan, not an authorization to build.
**Bottom line: DEFER.** No evidence of a real external-agent consumer exists in
this repository. The workstream's own gate — "MCP and gateway are not goals
in themselves; without a real consumer or a measured problem, the
classification is DEFER" — is met on the "no real consumer" branch, plainly,
not on the strength of a hypothetical one. See §2.

This note builds on the endpoint inventory in
`docs/research/next-wave/API_PRODUCTIZATION_OPTIONS.md` (100 HTTP endpoints:
48 under `/api/v1/workspaces/{workspace_id}/...`, 52 legacy flat `/api/...`).

## 1. Evidence search: is there a real external-agent consumer?

Searched the whole repo for "MCP" / "Model Context Protocol" and for
`docs/gtm-transformation/`, ADRs, and PRDs that might reference an agent
consumer of this product's own API. Every hit found:

- `scripts/validate_linkedin_design.py:127` — references a local `.mcp.json`
  path; this is about *this development environment's own* MCP tooling
  (Claude Code / Codex plugin config), not about the product exposing MCP to
  anyone.
- `docs/audit/post-epic/OPEN_BRANCH_AND_PR_MAP.md`, `IMPLEMENTATION_BASELINE.md`
  — mentions of `mcp__github__list_branches` etc.; these are citations of the
  *tool names an auditing agent used* to write those audit docs, not product
  architecture.
- `docs/PRD_linkedin_qualification_plugin_v0_1.md` and
  `docs/linkedin_integration_architecture.md` — the only substantive hits.
  Both describe a **not-yet-built, explicitly deferred** LinkedIn
  qualification connector, where MCP is one of the packaging options
  ("`.app.json or .mcp.json`") for a *future plugin adapter this product
  would use to call an approved LinkedIn program* — i.e. **outbound**, this
  product consuming an external capability via an MCP-shaped adapter, the
  opposite direction from "expose this product's API as an MCP server for
  external agents." `linkedin_integration_architecture.md` is headed
  "Status: Design accepted; runtime deferred," and the PRD says explicitly
  "Cette arborescence est une cible documentaire. Elle ne doit pas être créée
  avant LI-G3" (do not create before gate LI-G3).
- `docs/gtm-transformation/06_ROUTE_CONTEXT_AND_API_MODEL.md` and
  `12_PROGRAM_ROADMAP.md` (the two documents most likely to name an external
  API consumer if one existed): **no** mention of MCP, external agents, or
  third-party integration.
- No "E18" reference anywhere in the repo yet — the epic this note is meant
  to feed does not exist as a document to check against.
- Frontend consumer check (from the productization note): `app/frontend/app.js`
  (legacy UI) and `app/frontend/gtm-spaces.js` (newer GTM-space UI) are the
  **only** two callers of this app's HTTP API found anywhere in the repo.
  `scripts/run_e2e_gate.py` polls `/api/health`; no other script calls in.
  There is no CLI, no webhook receiver, no second internal service, and no
  documented external partner integration that talks to this API today.

**Conclusion of the search:** zero evidence of a real external agent, partner,
or internal automation that wants to consume this product's API via MCP.
The only "MCP" thread in the repo points the other way (this product as an
MCP *client* to LinkedIn, someday, after its own gate).

## 2. Recommendation: DEFER

Per the workstream's own framing, MCP/gateway classification work is
justified by a real consumer or a measured problem — neither is present.
Building an MCP server (or even a full tool/resource taxonomy pass ready to
implement) now would be classification in search of a consumer, which is
exactly what the gate warns against. Recommend the epic owner treat MCP
exposure as **not in scope for E18** unless a concrete external-agent use
case is named first (e.g., "a sales-ops LLM agent needs to read pipeline
state" or "an SDR copilot needs to trigger `queue-research`") — at which
point the classification below becomes the starting draft rather than a
speculative exercise.

## 3. Speculative classification (for if/when a consumer appears)

Given the DEFER conclusion, this section is deliberately kept short and
skeptical — a placeholder mapping, not a spec. Using the endpoint inventory
from `API_PRODUCTIZATION_OPTIONS.md` and the workstream's taxonomy
(READ_SAFE / WRITE / EXPENSIVE / HUMAN_GATED / PRIVACY_SENSITIVE):

| Class | Candidate endpoints | Why |
|---|---|---|
| **READ_SAFE** | All v1 GET list/get routes with no PII concentration: `/products*`, `/target-plans*`, `/opportunities*`, `/fit-assessments` (read), `/research-cases*`, `/signals` (read), `/insights`, `/metrics/catalog` | Idempotent, workspace-scoped, already IDOR-tested (except `opportunity_routes.py`, see productization note §1) |
| **PRIVACY_SENSITIVE** | `/people`, `/people/{id}`, `/people/{id}/360` (network_v1), `/conversations*` (engagement — message/objection content), anything touching `app/network_writer.py`-created person records | Person-level identity and conversation content; a naive READ_SAFE tool would leak PII to whatever agent/session calls it, with no product-side redaction layer today |
| **WRITE** | `POST /demands`, `PATCH /demands/{id}`, `POST /fit-assessments`, `PATCH /fit-assessments/{id}`, `POST /learning-proposals`, `POST /learning-proposals/{id}/transitions`, `POST /signals/{id}/queue-research` | Mutates workspace state; the PATCH routes' optimistic-concurrency contract (`expected_version`) is a poor fit for a stateless tool call unless the MCP layer round-trips versions correctly |
| **EXPENSIVE** | `POST /api/catalog/harvest`, `POST /api/catalog/discover` (legacy), `POST /signals/{id}/queue-research` (kicks off research handoff) | Triggers downstream work (harvesting, research orchestration), not a cheap read |
| **HUMAN_GATED** | `POST /api/qualification/actions` (action="force"), `PATCH /api/catalog/offers/{id}`, `/admin/network/*` | Already role-gated in the HTTP layer (`product_owner`/`admin`); an MCP tool wrapping these would need to preserve that gate, not just forward the session cookie |

This table is illustrative, not exhaustive, and intentionally does not cover
all 100 endpoints — doing that fully is the work to defer.

## 4. API_GATEWAY_DECISION

A dedicated gateway (API-key issuance, per-consumer rate limiting, quota
enforcement) is justified by real external auth/rate-limit/quota needs. That
premise does **not** currently hold:

- Auth is `starlette.middleware.sessions.SessionMiddleware` + a Google OIDC
  login flow (`app/authruntime/app.py`, `app/authruntime/deps.py`) — a
  browser session cookie (`aimd_session`), not an API key or OAuth
  client-credentials flow. There is no mechanism today for a third-party
  program to authenticate to this API at all, gateway or not.
- The only rate/quota logic in the codebase, `app/reach_scheduler.py`
  (`daily_quota`, send windows), governs outbound LinkedIn/email sends — a
  domain-level sending policy, not an API-layer rate limit.
- The product is explicitly single-tenant-per-workspace with membership-based
  access (`RequestContext.can_access_workspace`) — there's no multi-tenant
  external-partner surface a gateway would typically exist to protect.

Given that, a separate API_GATEWAY_DECISION section beyond this paragraph
isn't warranted: there is nothing to gate. If a real external consumer
appears (per §2), the auth question ("how does an external agent
authenticate without a browser session?") would need solving *before* an MCP
server or a gateway does, since MCP tool calls would otherwise need to either
proxy a human's session cookie (fragile, defeats "external agent" framing) or
wait on a genuine API-key/OAuth story that doesn't exist yet in this repo.

## 5. Note for the epic owner

This document is a research input to the human/architecture-owner's next-wave
Epic decision (E18 in particular). It documents an absence of evidence and a
DEFER recommendation, not a build plan — nothing here is an authorization to
start implementing an MCP server, a gateway, or the tool classification in
§3.
