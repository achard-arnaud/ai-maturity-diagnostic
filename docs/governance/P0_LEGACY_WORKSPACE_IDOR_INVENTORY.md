# P0 — Legacy `/api/*` Workspace/IDOR Inventory and Classification

**Status:** Gate deliverable, per `00_PROGRAM_README.md`'s mandatory pre-wave
gate ("inventory tenant-scoped legacy `/api/*` routes; classify
RETAIN/MIGRATE/RETIRE; align retained routes with workspace isolation used
by `/api/v1`; add own-workspace/cross-workspace/unauthenticated tests;
release the security correction to `main`") before any E14 runtime work.

**Method:** every `@app.get/post/patch/delete/put` route read directly from
`app/server.py` (54 matches incl. the 2 SPA catch-alls → 52 real
endpoints, matching `docs/research/next-wave/API_PRODUCTIZATION_OPTIONS.md`'s
earlier count); every distinct path referenced by `app/frontend/app.js`
(including template-literal dynamic segments) extracted separately and
cross-matched; every underlying business module read for its actual
storage model (SQLite column vs. per-workspace directory vs. mono-root
file), not inferred from the route signature alone.

## 1. Headline finding

Of the 52 legacy routes, **51 are live** — called somewhere in
`app/frontend/app.js`, the only consumer of this generation (confirmed by
grep including dynamic `${encodeURIComponent(...)}` segments, which an
earlier, shallower pass in this repo's own `API_PRODUCTIZATION_OPTIONS.md`
missed). Only `POST /admin/network/rebuild-index` has no frontend caller
(it's an on-demand ops trigger per its own comment — "manual/on-demand").
**"RETIRE" is not a realistic classification for this wave**: almost the
entire legacy surface is what the live product's only frontend (`app.js`)
actually runs on. This P0 pass is therefore "harden every route that
touches tenant data," not "delete the unused ones."

## 2. Category A — Confirmed workspace IDOR (client-controllable
workspace/company selector, zero verification against caller's own
membership)

These touch `app/network_index.py`'s data, which is **already correctly
tenant-partitioned** (`companies` SQLite table has a real `workspace_id`
column, `idx_companies_workspace_id` index) — the storage layer is not the
problem. The problem is purely at the route layer: nothing checks that the
caller (`ctx.workspace_id` / `ctx.can_access_workspace(...)`) is authorized
for the `workspace_id` a request supplies (or defaults to "all workspaces"
when none is supplied).

| Route | Current behavior | Confirmed exposure |
|---|---|---|
| `GET /api/network/people` | `workspace_id: str = ""` query param passed straight into `search_people(..., workspace_id=workspace_id.strip() or None)` | Any authenticated user can read **any workspace's** people by passing its id; omitting the param returns **every workspace's** people unfiltered |
| `GET /api/network/companies` | same pattern via `search_companies(...)` | same — any-workspace read, or all-workspace read by default |
| `POST /api/network/people` (create) | `workspace_id=payload.get("workspace_id")` from the request body, no check | Any authenticated user can **create a person record inside another workspace** |
| `POST /api/network/companies` (create) | same pattern | Any authenticated user can **create a company record inside another workspace** |
| `GET /api/network/duplicates` | `find_potential_duplicates(NETWORK_INDEX_PATH, root=ROOT, ...)` — no workspace filter parameter exists at all | Duplicate-detection pairs are computed **across every workspace's companies** in the one shared index |
| `POST /api/network/duplicates/dismiss` | `dismiss_duplicate_group(ROOT, payload.get("person_ids") or [], ...)` — no ownership check on the target `person_ids` | Any authenticated user can dismiss a duplicate-group flag touching **another workspace's** people |
| `GET /api/accounts/{company_id}/360` | `get_account_360(ROOT, company_id, index_path=NETWORK_INDEX_PATH)` looks the company up by id only, in `app/account_view.py` | Any authenticated user can read the **full aggregated 360** (people, qualification study, reach status, blocker actions) of **any company in any workspace** by guessing/enumerating a `company_id` |
| `POST /api/campaigns/prospecting` | `campaigns.launch_prospecting_campaign(ROOT, criteria=payload.get("criteria") or {}, ...)`; `campaigns.py`'s `_CRITERIA_FIELDS` includes `workspace_id`, forwarded unchecked into `search_people`/`search_companies` | Same cross-workspace read as the direct network routes, reachable through a second, indirect path |

**Not vulnerable, RETAIN as-is:**
- `POST /admin/network/rebuild-index`, `POST /admin/network/companies/{id}/reassign` — both `require_role("admin")`-gated; reassignment moving a company **between** workspaces is the intended admin capability here (ADR-007's own admin boundary), not a gap.

### Fix strategy (no ADR needed — this is the exact pattern already used by
every `/api/v1/...` route)

For every Category A route: resolve the effective `workspace_id` as
`ctx.workspace_id` by default (never an empty/"all" fallback), and if the
caller explicitly supplies a different `workspace_id`, require
`ctx.can_access_workspace(workspace_id)` (true for admins, true for a
member of exactly that workspace, false otherwise) before running the
query — 404 (not 403) on failure, matching ADR-007 §1's "don't disclose
another workspace's object exists" rule already used by every v1 route.
`GET /api/accounts/{company_id}/360` and the duplicates routes gain the
same check applied to the resolved company/person's own `workspace_id`
column rather than a request parameter. This preserves every existing
successful call shape for a same-workspace caller (`app.js` never breaks)
and only changes behavior for a request that was, today, silently reading
or writing across a tenant boundary.

## 3. Category B — Unfinished ADR-007 §5 mono-root migration (structural
gap, not a request-parameter bug)

`app/workspace_paths.py` (`WorkspacePaths.root()`) and 8 business modules
already implement **step 1** of ADR-007 §5's documented 5-step migration
sequence — each has a `for_workspace(cls, workspace_id, repo_root=None)`
factory built on `resolve_workspace_root()`. **None of the 8 is actually
used in `app/server.py`** — every one is instantiated exactly once at
import time as a plain, workspace-blind singleton:

```python
HARVESTER = CatalogHarvester(ROOT)      # excluded below, see §3b
DEMAND = DemandCatalog(ROOT)
QUALIFICATION = QualificationCockpit(ROOT)
NUDGING = UseCaseNudger(ROOT)
VALUE_CHAIN = ValueChainCatalog(ROOT)
UC_GRAPH = UseCaseGraph(ROOT)
REACH = ReachMatchmaker(ROOT)
FOLLOWUP = FollowUpDashboard(ROOT)
HERITAGE = UseCaseHeritage(ROOT)
```

`ROOT` is the repository root — `WorkspacePaths.root()`'s own docstring
confirms this is *exactly* what `for_workspace("default")` would resolve
to, so today every request, regardless of the caller's real
`ctx.workspace_id`, reads and writes the **"default" workspace's** studies/
data/private files. A `standard_user` whose membership is workspace
`"acme"` (never `"default"`) currently sees and can mutate `"default"`'s
Demand/Qualification/FollowUp/Heritage/Reach(legacy)/Nudging/ValueChain/UcGraph
data through these 8 modules' routes — the same class of gap as Category
A, but caused by an incomplete internal migration rather than a
request-parameter bug.

Affected routes (all currently `Depends(get_current_user)`, no workspace
check applicable because the singleton has no workspace concept applied
to it at the route layer): `/api/demand`, `/api/demand/inventories`,
`/api/demand/intake`, `/api/qualification`, `/api/qualification/actions`,
`/api/follow-up`, `/api/heritage/company`, `/api/heritage/sector`,
`/api/reach`, `/api/reach/preview`, `/api/reach/prepare`,
`/api/nudging/generate`, `/api/nudging/inventories`,
`/api/nudges/{id}/accept`, `/api/nudges/{id}/reject`,
`/api/nudges/{id}/ack-falsifier`, `/api/value-chain`,
`/api/value-chain/study`, `/api/value-chain/prepare`,
`/api/uc-graph/company`, `/api/uc-graph/sector`.

### 3a. A real subtlety found while scoping the fix: shared reference data
lives under the same `self.root` as tenant data

Swapping the singleton for a per-request `ClassName.for_workspace(ctx.workspace_id)`
call is not a safe blind find-replace: at least `DemandCatalog._taxonomy_sectors()`
reads `self.root / "data" / "taxonomies" / "icb_v5_2026.yaml"` — a static,
shared ICB sector taxonomy, not tenant data. For any workspace other than
`"default"`, `WorkspacePaths.root()` resolves to a fresh, empty
`workspaces/<id>/` directory (by design — "no data migration happens
here"), so that taxonomy file would not exist there and the sector list
would silently go empty for every non-default-workspace user. (Checked:
`_taxonomy_sectors()` already degrades gracefully — `if not path.is_file():
return {}` — so this is a silent feature regression, not a crash, but a
regression nonetheless.) `CatalogHarvester` has the same shape of problem
one level worse (`catalog_sources/shelves.yaml` has no graceful-empty
fallback checked) — see §3b for why it's excluded from this pass instead.

This is exactly the shared-core-vs-tenant-data distinction **ADR-008
already decided** for `product_catalog/` ("shared, read-only published
catalog" at the repo root plus workspace-owned overlays). §5 below applies
that same, already-accepted principle to the other shared reference paths
found in Category B, rather than proposing a new pattern — no new ADR
required, only a short decision note recording the extension (§5).

### 3b. Excluded from Category B this pass: `CatalogHarvester`

`CatalogHarvester` also has a `for_workspace()` factory, but its `root`
governs `catalog_sources/shelves.yaml` reads with **no** graceful-missing
fallback path checked, and ADR-007 §5 itself says explicitly: *"Do not
move `product_catalog/` during this migration until its global-versus-
workspace ownership gate is decided"* — which ADR-008 then decided, for
`product_catalog/` specifically, as shared-core-plus-overlay. Catalog
harvesting (`/api/catalog/harvest`, `/api/catalog/discover`) stages
candidates that flow toward that same shared/overlay-governed catalog;
migrating `CatalogHarvester` to a bare per-workspace root without also
applying ADR-008's projection model would risk exactly the kind of
"invisible or accidentally duplicated" catalog state ADR-008's own Context
section warns about. **Left untouched in this P0 pass** — folding catalog
harvesting into ADR-008's projection model is E15/artifact-library-
adjacent work, not a mechanical workspace-path swap, and forcing it here
would be scope creep beyond "harden the existing invariant."

## 4. Category C — No workspace concept, RETAIN as-is (no fix needed)

- `GET /api/health` — unauthenticated liveness probe, no tenant data.
- `GET /api/auth/me` — returns the caller's own identity; nothing to leak across a boundary.
- `GET /api/skills`, `POST /api/skills/{id}/invoke` — skill catalog is code/config, not workspace data; a skill's *execution* operates on inputs the caller supplies in the request body, which are not workspace-scoped resources looked up by id.
- `GET /api/offers`, `GET/POST /api/catalog/candidates*`, `PATCH /api/catalog/offers/{id}` (`catalog_search.py`, `catalog_promotion.py`) — no `for_workspace` factory exists on either module; product catalog is governed by ADR-008's shared-core-plus-overlay model already, not a per-workspace mono-root split. Out of scope here for the same reason as §3b.
- `GET /api/blocker-actions` — `BlockerActionLog(ROOT)`, parameterized by `study_id` in its actual query methods, not by an open workspace selector; once Category B's `QualificationCockpit`/`ReachMatchmaker` are fixed, a `study_id` is only ever obtainable through an already-workspace-checked path, so there is no independent exposure here to fix in this pass.
- `GET /api/kanban/board`, `POST /api/workflows/plan` — no `for_workspace` factory, no workspace-shaped query parameter; these are ROOT-global by construction (a workflow plan / kanban projection over campaigns and nudges, not tenant-partitioned resources). No fix identified; flagged for the architecture owner if this assumption should be revisited later, not blocking P0.
- `GET /api/shelves`, `GET /api/backlog` — same as above (dashboard projections over `HARVESTER`/`CATALOG_SEARCH`, already excluded per §3b/this list).
- `GET /api/campaigns`, `POST /api/campaigns/{id}/mark-sent`, `POST /api/campaigns/cross-sell` — `campaigns.py` has no `for_workspace` factory and its storage is ROOT-global; **`POST /api/campaigns/prospecting` is the one campaigns route with an actual cross-workspace read** (§2, via its `criteria.workspace_id` passthrough into `network_index`) and is fixed there. The other three campaigns routes operate on campaign records that are not themselves workspace-columned anywhere found — flagged as a smaller, separate finding (campaigns records have no workspace_id field at all, so "which workspace does a campaign belong to" is presently undefined) worth a follow-up note for whoever eventually migrates `campaigns.py`, not a P0 blocker since no cross-tenant read is reachable through them today.

## 5. Decision note extending ADR-008's shared-core principle to Category B

Per §3a, applying ADR-007 §5 step 4 ("switch runtime reads to workspace
paths") to `DemandCatalog`, `QualificationCockpit`, `UseCaseNudger`,
`ValueChainCatalog`, `UseCaseGraph`, `ReachMatchmaker`, `FollowUpDashboard`,
`UseCaseHeritage` will be done as: **tenant paths (`studies/`,
`data/private/...`) resolve through `for_workspace(ctx.workspace_id)`;
static shared-reference paths identified per module (currently only
`DemandCatalog`'s `data/taxonomies/icb_v5_2026.yaml`) continue to resolve
from the mono/default root regardless of the caller's workspace**, exactly
mirroring ADR-008's "shared, read-only published catalog at the repo root"
principle rather than inventing a new mechanism. Implementation: each
affected method keeps reading its shared-reference path via a fixed
`DEFAULT_WORKSPACE_ID` resolution (or, equivalently, the module keeps an
internal reference to the un-scoped mono-root purely for those specific
reads) while the instance's own `self.root` is the caller's real
workspace root for everything else. No other shared-reference path beyond
`icb_v5_2026.yaml` was found in the 8 modules during this inventory pass
(each module's `self.root / ...` usages were read in full — see §3
commit's diff for the grep evidence); if implementation surfaces another
one, it gets the same treatment, not a special case.

## 6. Sprint plan

- **P0-S01** — Category A (network_index IDOR): own-workspace/cross-
  workspace/unauthenticated tests written first (TDD), then the fix, per
  route.
- **P0-S02..S09** — Category B, one module per sprint (Demand,
  Qualification, FollowUp+Heritage, Reach, Nudging, ValueChain, UcGraph),
  each: workspace-scoped construction wired in, shared-reference-path
  exception applied where found, existing tests re-verified green (proves
  the default-workspace behavior is unchanged byte-for-byte), new
  cross-workspace-isolation tests added.
- Each sprint: tests -> `scripts/check_release.py` green -> commit -> merge
  toward `dev`. P0 as a whole -> NRT -> `dev -> main`, per the program's
  own delivery discipline.

## 7. OIDC exact-return-URL gap

Explicitly out of scope for P0 per the program brief — remains assigned to
E19.
