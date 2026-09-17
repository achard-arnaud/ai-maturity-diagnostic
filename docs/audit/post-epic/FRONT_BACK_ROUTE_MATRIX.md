# Front/Back Route Matrix — GTM spaces (E12/E13)

Sources read in full: `app/frontend/router.js` (32 lines), `app/frontend/gtm-spaces.js`
(62 lines), the wiring in `app/frontend/app.js` lines 805–838, and each
`app/*_routes.py`/`app/server.py` router registration (lines 190–200).

## Router (`app/frontend/router.js`)

Nine spaces, one URL shape: `/w/{workspace}/{space}[/{objectId}]`, parsed by
regex and validated against a fixed `Set` of space names
(`home, discover, research, fit, targets, reach, engagement, pipeline,
insights`). History API (`pushState`/`replaceState`/`popstate`), no client
router library. A `?legacy=1` query param bypasses the GTM shell entirely and
falls back to the pre-E12 panel-switcher (`showPanel`) — this is the
documented one-release rollback flag from ADR-010/E12-S06, confirmed present
in `index.html` (`id="legacyNav" class="hidden"`) and asserted by
`tests/test_gtm_shell_quality.py`.

## Per-space matrix

| Space | Route | Backing API call (`gtm-spaces.js` → `app/*_routes.py`) | Registered in `server.py`? | Rendering |
|---|---|---|---|---|
| **Home** | `/w/{ws}/home` | `GET /api/follow-up` (legacy dashboard endpoint, `app/server.py:337`, not a `/api/v1/...` route) | Yes (direct `@app.get`) | Generic card list (same template as Discover/Research/etc.) |
| **Discover** | `/w/{ws}/discover` | `GET /api/v1/workspaces/{ws}/signals` → `app/signal_routes.py` | Yes (`create_v1_signal_router`, `server.py:191`) | Generic card list |
| **Research** | `/w/{ws}/research` | `GET /api/v1/workspaces/{ws}/research-cases` → **no such route exists** | **No.** `app/research_routes.py` (the only router imported under the name "research") registers exactly one route: `GET /companies/{company_entity_id}/360` (Company 360, an Epic 04 deliverable). Nothing in the entire `app/` tree registers a path containing `research-cases` (confirmed by grepping every `app/*_routes.py` and `app/server.py`) — `app/research_case_store.py`/`app/research_queue.py`/`app/research_orchestration.py`/`app/research_review.py` all exist and are tested, but none of them exposes an HTTP router. | Generic card list — but the underlying `GET` will 404 in a real deployment; the space will always render its empty/error state |
| **Fit** | `/w/{ws}/fit` | `GET /api/v1/workspaces/{ws}/fit-assessments` → `app/fit_routes.py` | Yes (`create_v1_fit_router`, `server.py:195`); this router also has `POST /fit-assessments` and `PATCH /fit-assessments/{id}` (write path exists, unlike most other v1 routers) | Generic card list, with gate badges (`item.gates` → pass/blocked) |
| **Targets** | `/w/{ws}/targets` | `GET /api/v1/workspaces/{ws}/target-plans` → `app/target_plan_routes.py` | Yes (`create_v1_target_plan_router`, `server.py:196`); GET-only router confirmed by grep (no POST/PATCH) | Generic card list |
| **Reach** | `/w/{ws}/reach` | `GET /api/v1/workspaces/{ws}/sequences` → `app/reach_routes.py` | Yes (`create_v1_reach_router`, `server.py:197`); GET-only router confirmed by grep | Generic card list |
| **Engagement** | `/w/{ws}/engagement` | `GET /api/v1/workspaces/{ws}/conversations` → `app/engagement_routes.py` | Yes (`create_v1_engagement_router`, `server.py:198`); GET-only router confirmed by grep | Generic card list |
| **Pipeline** | `/w/{ws}/pipeline` | `GET /api/v1/workspaces/{ws}/opportunities/pipeline-board` → `app/opportunity_routes.py` (`GET /opportunities/pipeline-board`, confirmed) | Yes (`create_v1_opportunity_router`, `server.py:199`) | **Purpose-built**: `config.board=true` flattens `payload.stages` into per-status columns — a real Kanban-style board, not the generic card list |
| **Insights** | `/w/{ws}/insights` | `GET /api/v1/workspaces/{ws}/insights` + `GET /api/v1/workspaces/{ws}/learning-proposals` → `app/insights_routes.py` (`GET /learning-proposals`, `POST /learning-proposals`, `POST /learning-proposals/{id}/transitions`, confirmed) | Yes (`create_v1_insights_router`, `server.py:200`) | **Purpose-built**: dedicated `renderInsights()` function — funnel/quality/cost metric tiles, privacy-suppression banner, and a separate LearningProposal review section with a link to workspace admin. Not the generic card list. |

## Generic-card vs. purpose-built — confirmed against ADR-010

Per `docs/governance/ADR-010_GTM_FRONTEND_REPLATFORM.md`, E12 deliberately
kept the existing dependency-free vanilla-JS SPA and added only "a small
routing layer" rather than adopting a component framework — **this is
documented as an intentional, cost-justified decision, not a defect.**
Consistent with that: 7 of 9 spaces (Home, Discover, Research, Fit, Targets,
Reach, Engagement) share one generic card-rendering code path in
`gtm-spaces.js`'s `render()` function (title/summary/status/gate-badge per
item, from whichever list field the payload happens to expose). Only
**Pipeline** (board layout) and **Insights** (metrics + proposal review) get
dedicated rendering functions — matching E12/E13's own stated scope
(Pipeline needed a Kanban board per its stage semantics; Insights needed
metric tiles and a privacy-suppression state that a generic card cannot
express).

## Confirmed defect: Research space calls a route that does not exist

`app/frontend/gtm-spaces.js` wires the Research space to
`GET /api/v1/workspaces/{workspace}/research-cases`. No backend route by
that name exists anywhere in `app/` — confirmed by reading
`app/research_routes.py` in full (its only route is Company 360) and
grepping every `app/*_routes.py` file plus `app/server.py` for
`research-cases`. `docs/gtm-transformation/06_ROUTE_CONTEXT_AND_API_MODEL.md`
also mentions the path (as a target-model reference, not as evidence it was
built).

The test that is supposed to guard this
(`tests/test_gtm_upstream_spaces.py::test_home_discover_research_use_real_endpoints`)
only asserts that the **string** `"/research-cases"` appears in
`gtm-spaces.js`'s source — it does not start the app or make an HTTP call,
so it cannot and does not catch a missing backend route. E12-S03's own STOP
file claims "Home, Discover and Research now render workspace-scoped queues
from their real endpoints" — true for Home and Discover, **not accurate for
Research** as written today. In production this means opening the Research
space always shows its empty/error state (a 404 from `api()`, caught and
rendered as `<div class="error">`), never real data, regardless of how many
ResearchCases exist in the workspace. This was not called out in any Epic
12 or Epic 13 acceptance record and is the most concrete, previously-unknown
functional defect found in this audit — see the final report.
