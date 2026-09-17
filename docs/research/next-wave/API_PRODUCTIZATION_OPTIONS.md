# API Productization Options — Research Note (CLAUDE_01 Workstream G)

**Status:** Research only. No runtime code was changed to produce this note.
**Scope:** exhaustive inventory of every HTTP endpoint defined in `app/server.py`
and `app/*_routes.py`, as of the current `main` (post-PR #67).
**Method:** `grep` of every `@router.get/post/patch/delete/put` in `app/*_routes.py`
and every `@app.get/post/patch/delete/put` in `app/server.py`, cross-checked
against each route's dependency list, the corresponding test file, and the two
frontend bundles (`app/frontend/app.js`, `app/frontend/gtm-spaces.js`).

## Headline numbers

| Generation | Location | Endpoint count |
|---|---|---|
| `/api/v1/workspaces/{workspace_id}/...` | `app/*_routes.py` (11 router-factory modules) | **48** |
| Legacy flat `/api/...`, `/admin/...` | directly in `app/server.py` | **52** |
| **Total HTTP API endpoints** | | **100** |

(Two additional `@app.get` routes in `server.py`, `/w/{workspace_slug}/{space}`
and `/w/{workspace_slug}/{space}/{object_id}`, are `include_in_schema=False`
SPA deep-link catch-alls that return `index.html` — not API endpoints, and
excluded from the count above.)

---

## 1. The v1 generation — `/api/v1/workspaces/{workspace_id}/...`

All 11 router-factory modules share one construction: `APIRouter(prefix="/api/v1/workspaces/{workspace_id}")`,
every route depends on `require_workspace_access()` (never `get_current_user`
alone, never no auth), and every 404 path is deliberately generic (`"not found"`)
so a cross-workspace lookup can't be distinguished from an unknown ID (ADR-007 §1).
Pagination, where it applies, is a uniform `limit` (1–100, else `400`) + opaque
`cursor` → `{"items": [...], "next_cursor": ...}`. Errors are typed per-route
`HTTPException` (400 validation, 404 not-found, 409 optimistic-concurrency
conflict), not the generic 500 fallback the old generation relies on.

| Module | Endpoints (method + path suffix) | Command/Query | Response shape | Errors raised | Pagination | Idempotency | Tests | Known consumers |
|---|---|---|---|---|---|---|---|---|
| `network_v1_routes.py` (Epic 02 S04) | GET `/people`, GET `/people/{id}`, GET `/companies`, GET `/companies/{id}`, GET `/relationships`, GET `/relationships/{id}`, GET `/people/{id}/360` | Query (7 GET) | list→`{items,next_cursor}`; get→entity dict; 360→aggregated dict | 400 (bad limit), 404 (not found / cross-workspace) | cursor+limit on the 3 list routes | trivially safe — all reads | `tests/test_network_v1_routes.py` (10 tests incl. `test_cross_workspace_list_is_404_not_leaked`, `test_cross_workspace_entity_lookup_is_404_not_leaked`) | none yet (`app/frontend/gtm-spaces.js` does not call `/people`, `/companies` or `/relationships`; only `app.js` calls the legacy `/api/network/*`) |
| `signal_routes.py` (Epic 03 S05) | GET `/signals`, GET `/signals/{id}`, POST `/signals/{id}/queue-research` | Query ×2, Command ×1 | list/get dicts; queue-research → handoff event dict | 400, 404 | cursor+limit on list | queue-research is **not** idempotent (re-POST creates another handoff event; no idempotency key) | `tests/test_signal_routes.py` (9 tests, incl. 2 cross-workspace-404) | `gtm-spaces.js` (`discover` space reads `/signals`); queue-research has no known caller yet |
| `research_routes.py` (Epic 04) | GET `/companies/{id}/360`, GET `/research-cases`, GET `/research-cases/{id}` | Query | dicts / paginated list | 400, 404 | cursor+limit on list | safe (reads) | `tests/test_research_routes.py` (10 tests, 2 cross-workspace-404) | `gtm-spaces.js` (`research` space) |
| `demand_routes.py` (Epic 05 S04) | GET `/demands`, GET `/demands/{id}`, POST `/demands`, PATCH `/demands/{id}`, GET `/demands/{id}/resolver` | Query ×3, Command ×2 | dict + `version` field (optimistic concurrency) | 400, 404, **409** (`DemandConflict`/`DemandAlreadyExists`) | cursor+limit on list | **PATCH is explicitly optimistic-concurrency**: caller must send `expected_version`, a stale version 409s rather than silently overwriting (docstring: "mutation sûre"); POST create has no idempotency key, a retried POST can 409 on `DemandAlreadyExists` if the caller reuses the same natural key, but there is no dedup for a genuinely duplicate create | `tests/test_demand_routes.py` (11 tests, 1 cross-workspace-404) | none in either frontend bundle yet — reads and writes both unconsumed today |
| `product_routes.py` (Epic 06) | GET `/products`, GET `/products/{id}`, GET `/products/{id}/snapshots/{sid}`, GET `/products/{id}/diff` | Query | dicts | 404 (incl. "snapshot doesn't belong to this product" as 400) | none (no list pagination params) | safe (reads) | `tests/test_product_routes.py` (7 tests) | none in either frontend bundle |
| `fit_routes.py` (Epic 07) | GET `/fit-assessments`, GET `/fit-assessments/compare`, GET `/fit-assessments/{id}`, POST `/fit-assessments`, PATCH `/fit-assessments/{id}` | Query ×3, Command ×2 | dict + version | 400, 404, 409 | cursor+limit on list | same optimistic-concurrency PATCH pattern as demand | `tests/test_fit_routes.py` (7 tests, 1 cross-workspace-404) | `gtm-spaces.js` reads `/fit-assessments`; POST/PATCH unconsumed |
| `target_plan_routes.py` (Epic 08) | GET `/target-plans`, GET `/target-plans/{id}`, GET `/target-plans/{id}/stakeholders`, GET `/target-plans/{id}/committee-graph` | Query | dicts | 400, 404 | cursor+limit on list | safe (reads) | `tests/test_target_plan_routes.py` (8 tests, 3 cross-workspace-404) | `gtm-spaces.js` reads `/target-plans`; stakeholders/committee-graph unconsumed |
| `reach_routes.py` (Epic 09) | GET `/sequences`, GET `/sequences/{id}`, GET `/sequences/{id}/steps`, GET `/sequences/{id}/tasks`, GET `/sequences/{id}/steps/{sid}/touchpoints` | Query | dicts | 400, 404 | cursor+limit on list | safe (reads) | `tests/test_reach_routes.py` (10 tests, 3 cross-workspace-404) | `gtm-spaces.js` reads `/sequences`; steps/tasks/touchpoints unconsumed |
| `engagement_routes.py` (Epic 10) | GET `/conversations`, GET `/conversations/{id}`, GET `/conversations/{id}/events`, GET `/conversations/{id}/events/{eid}/objections` | Query | dicts | 400, 404 | cursor+limit on list | safe (reads) | `tests/test_engagement_routes.py` (7 tests, 2 cross-workspace-404) | `gtm-spaces.js` reads `/conversations`; events/objections unconsumed |
| `opportunity_routes.py` (Epic 11 S05) | GET `/opportunities`, GET `/opportunities/pipeline-board`, GET `/opportunities/{id}` | Query | dicts | 400, 404 | cursor+limit on list | safe (reads) | **none** — no `test_opportunity_routes.py` exists at all; nothing in `tests/` imports `create_v1_opportunity_router`. The module's own docstring calls itself "IDOR-safe" but that claim is untested at the route layer (only `test_opportunity_store.py` etc. test the storage layer below it) | `gtm-spaces.js` reads `/opportunities/pipeline-board` only |
| `insights_routes.py` | GET `/metrics/catalog`, GET `/insights`, GET `/learning-proposals`, POST `/learning-proposals`, POST `/learning-proposals/{id}/transitions` | Query ×3, Command ×2 | dicts (POST create returns `201`) | 400 | `limit` (`Query(50, ge=1, le=100)`) on proposals list, no cursor | POST create/transition have no idempotency key; a retried POST creates a duplicate proposal or double-fires a transition | `tests/test_insights_routes.py` (3 tests only — thin relative to its 5 routes; the small-cohort-suppression/cross-workspace test covers `/insights` but proposal create/transition routes have no dedicated test) | `gtm-spaces.js` reads `/learning-proposals` (for the insights space); create/transition unconsumed |

**Cross-cutting v1 observations:**
- Every v1 module is `workspace_id`-in-path + `require_workspace_access()`, and 10 of the 11 modules have an explicit cross-workspace-404 test. **`opportunity_routes.py` is the one gap**: it has the same `require_workspace_access()` dependency and the same generic-404 pattern as its siblings, so it is very likely equally safe, but there is no test proving it, which matters for exactly the kind of endpoint (opportunities/pipeline) an IDOR would be most damaging on.
- Of the 48 v1 endpoints, only **9** have a live frontend caller today (`gtm-spaces.js`, the newer GTM-space UI): `/signals`, `/research-cases`, `/fit-assessments`, `/target-plans`, `/sequences`, `/conversations`, `/opportunities/pipeline-board`, `/insights`, `/learning-proposals` — and of those 9, only the plain list/get GETs are called; every v1 POST/PATCH command (`queue-research`, demand create/patch, fit create/patch, learning-proposal create/transition) has **zero** known consumers, internal or external. The legacy `app.js` bundle calls none of the v1 surface at all.

## 2. The legacy flat generation — `/api/...`, `/admin/...`

Defined inline in `build_app()` in `app/server.py` (52 endpoints). Structurally
different from v1 in every dimension that matters:

- **Auth:** almost all use `Depends(get_current_user)` (any authenticated
  session, no role check) — 47 of 52. Three use `Depends(require_role("admin"))`
  (`POST /admin/network/rebuild-index`, `POST /admin/network/companies/{id}/reassign`)
  or `require_role("product_owner", "admin")` (`PATCH /api/catalog/offers/{id}`).
  One (`POST /api/qualification/actions`) does the role check **by hand inside
  the handler body** (`if action == "force" and not (ctx.is_admin or ctx.role
  == "product_owner"): raise HTTPException(403, ...)`) rather than via a
  dependency — a documented, deliberate choice per its inline comment, but an
  inconsistent pattern next to the `require_role()` dependency used two routes
  away for a materially similar gate. `GET /api/health` is the one fully
  unauthenticated route (ops probe).
- **Workspace-scoping:** `workspace_id` is **not** in the path for any legacy
  route. Where it exists at all it's an optional query string (`GET
  /api/network/people?workspace_id=...`, `/api/network/companies`) or is
  derived implicitly from `ctx` inside the handler; most legacy routes
  (`/api/demand`, `/api/qualification`, `/api/reach`, `/api/campaigns`, etc.)
  don't scope by workspace at the route signature at all. `tests/test_server_v07.py`
  (41 tests) checks assorted role/403/404 cases (e.g. non-admin trying
  `/admin/network/companies/{id}/reassign` → 403, unknown company →
  404) but there is **no systematic per-endpoint cross-workspace-404 sweep**
  comparable to the v1 test suites — the closest is a single manual check that
  `?workspace_id=acme-ws` vs `?workspace_id=default` return different result
  sets, which tests filtering, not IDOR-safety of a fixed-shape lookup.
- **Errors:** most legacy routes have no per-route `HTTPException` at all;
  they rely on the app-level handlers for `ControlPlaneError` → 400, timeout →
  504, and any uncaught `Exception` → 500. Only a handful raise explicit
  `HTTPException` (`GET /api/accounts/{id}/360` → 404 on unknown company, the
  admin reassign/rebuild routes, the one hand-rolled 403 above).
- **Pagination:** none. Every list-returning route (`/api/network/people`,
  `/api/network/companies`, `/api/campaigns`, `/api/catalog/candidates`, `/api/skills`,
  etc.) returns the full result set; filtering is via query params
  (`text=`, `status=`, `category=`), not cursoring.
- **Idempotency:** no idempotency keys anywhere in this generation. The
  clearest cases that are **not** safe to retry blindly: `POST /api/demand/intake`,
  `POST /api/catalog/harvest`, `POST /api/catalog/discover` (each stages new
  records), `POST /api/network/people` / `POST /api/network/companies`
  (plain creates — the code comment at `app/server.py:611-621` explicitly
  frames this as "any authenticated user may create" a new record, with no
  dedup), and all four `POST /api/campaigns/*` routes. Routes that are
  effectively idempotent by construction: `POST /api/network/duplicates/dismiss`
  (dismissal is a set-membership flip), `POST /api/nudges/{id}/accept|reject|ack-falsifier`
  (state transitions on an id — a repeat is a no-op or a clean re-raise from
  the domain layer), `admin/.../reassign` (sets workspace_id, replaying with
  the same target is a no-op).
- **Response typing:** no `response_model=` anywhere; handlers return raw
  `dict`/`Any` via bare returns or manual `JSONResponse(status_code=..., content=...)`.
- **Tests:** the bulk of coverage lives in `tests/test_server_v07.py` (41 tests)
  plus the frontend-contract tests (`test_v06_frontend_contract.py` through
  `test_v10_frontend_contract.py`), which assert on frontend/route wiring more
  than on the HTTP contract itself.
- **Consumers:** `app/frontend/app.js` calls all 34 of the distinct legacy
  paths it references (confirmed by grep — `app.js` never touches `/api/v1/*`).
  `scripts/run_e2e_gate.py` polls `GET /api/health` as a readiness probe.
  No other script in `scripts/*.py` calls into this app's own HTTP API
  (`scripts/advanced_research.py` calls external APIs — HN Algolia, arXiv —
  unrelated to this inventory).

## 3. Should `/api/v1/` be standardized further?

**Yes, directionally, but not urgently, and not as a lift-and-shift.** The v1
convention (`workspace_id` in path + `require_workspace_access()` + generic
404 + cursor pagination + typed per-route errors) is demonstrably the safer
and more consistent pattern — it's the only generation with IDOR tests as a
matter of course. Migrating the 52 legacy routes to it would fix the two real
gaps documented above (no workspace_id in path, no systematic cross-workspace
test). But:

- The legacy routes are still the **only** ones any frontend actually calls
  today. A migration is a live-traffic cutover of the whole product's UI, not
  a quiet refactor — it needs its own epic-sized plan (frontend rewire +
  parallel-run + deprecation window), not something to tuck into an
  incremental pass.
- Several legacy routes (`/api/skills/{id}/invoke`, `/api/catalog/harvest`,
  `/api/catalog/discover`, the value-chain/uc-graph/heritage triad) look like
  internal control-plane operations more than resource CRUD; forcing them
  into `/api/v1/workspaces/{workspace_id}/...` resource-noun shape may not be
  a natural fit without first deciding what workspace-scoped "resource" they
  actually are.
- The nearer-term, lower-risk fix is narrower: (a) close the `opportunity_routes.py`
  test gap now (cheap, matches an existing pattern exactly), and (b) decide
  whether the 39 v1 endpoints with zero consumers are premature (built ahead
  of a UI that doesn't call them yet) before adding more v1 surface — a
  question for whoever owns the next-wave epic, not something this note
  resolves.

## 4. Is OpenAPI/Swagger already usable?

**FastAPI's `/openapi.json` and `/docs` are reachable** (no `docs_url=None`
override in `app/authruntime/app.py` or `app/server.py`), but the schema they
produce is **low-quality today**: `grep -rn "response_model=" app/*.py` and
`grep -rln "BaseModel" app/*_routes.py app/server.py` both return **zero
matches** across the entire app — every one of the 100 endpoints returns a
bare `dict`/`Any`, so FastAPI has nothing to introspect and every response in
the generated spec will show as an untyped `object` with no declared
properties. Request bodies fare no better: routes take `dict[str, Any] =
Body(...)` rather than a Pydantic model, so request schemas are equally
opaque. The auto-generated spec exists and is navigable (you can see every
path, method, and query param — those are typed, e.g. `limit: int = 20`), but
it cannot currently serve as a real API contract for consumer or client-generation
purposes; that would require introducing `response_model=`/Pydantic
schemas per route, which is a non-trivial, endpoint-by-endpoint typing effort
across both generations (100 routes), not a config flag.

## 5. Note for the epic owner

This document is a research input to the human/architecture-owner's next-wave
Epic decision (E18 in particular). It is not a plan, a proposal, or an
authorization to start building the v1 migration, the opportunity-route test,
or Pydantic response models — those are scoping decisions for whoever owns
that epic to make with this inventory in hand.
