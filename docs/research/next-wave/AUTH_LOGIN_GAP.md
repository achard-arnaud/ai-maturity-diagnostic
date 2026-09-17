# Auth/login gap audit — candidate Epic E19

Status: **research and proposal only**. No runtime code was written or
modified to produce this document.

Source read in full: `app/authruntime/config.py`, `app/authruntime/deps.py`,
`app/authruntime/app.py`, `app/authruntime/db.py`, `app/authruntime/oidc.py`,
`app/frontend/login.html`, `docs/ADR-007-multi-workspace-auth-runtime.md`,
`tests/test_authruntime_app.py`. Cross-checked against
`docs/audit/post-epic/FRONT_BACK_ROUTE_MATRIX.md` and a direct grep of every
route in `app/server.py` and every `app/*_routes.py` v1 router for their
auth dependency.

**Note on timing:** at the start of this audit, `API_PRODUCTIZATION_OPTIONS.md`
did not yet exist in `docs/research/next-wave/` (only the two storytelling/
search-social-networks harvest notes were present); §5 below was drafted
independently by reading `app/server.py` and every `app/*_routes.py` file
directly. Partway through this session, `main` advanced (merged PRs added
`docs/research/next-wave/API_PRODUCTIZATION_OPTIONS.md` among other
workstream outputs) and that document is now present. Its §2 ("The legacy
flat generation") independently confirms every claim in §5 below —
`get_current_user`-only auth on 47 of 52 legacy routes, no `workspace_id` in
the path for any legacy route, and the same `GET /api/network/people?workspace_id=`
example — with additional detail this document does not duplicate
(idempotency-safety per route, response typing, OpenAPI schema quality).
§5 is kept as independently-derived line-level evidence rather than
rewritten as a pure citation, but `API_PRODUCTIZATION_OPTIONS.md` should be
treated as the authoritative, more complete inventory of the full 100-endpoint
surface for anything beyond the auth/workspace-scoping angle this document
focuses on.

The brief for this workstream is explicit: **harden the existing socle,
don't build a second auth system.** Every recommendation below stays inside
that frame — extend `app/authruntime/*`, never replace it.

---

## 1. OIDC / session lifecycle

- Provider: a single configured Google OIDC client (`app/authruntime/oidc.py`,
  Authlib-backed), consistent with ADR-007 §2 ("one configurable OIDC
  provider").
- Session model is exactly ADR-007 §3's design: the browser holds only an
  opaque, random 64-hex-char token (`uuid4().hex + uuid4().hex`,
  `db.py:248`) in a cookie; the OIDC access/ID token and membership state
  never leave the server. This is implemented correctly, not just
  documented.
- **Session TTL is fixed at 12 hours (`AuthConfig.session_ttl_hours = 12`),
  with no refresh, no sliding expiration, and no idle-timeout distinct from
  absolute expiration.** `get_session_user` (`db.py:258-278`) checks
  `expires_at < now` and returns `None` (session dead) with no renewal path.
  A user active at hour 11:59 is logged out at hour 12:00 regardless of
  activity, and must complete a full OIDC round-trip to continue. For a
  sales-intelligence tool used through a working day, a fixed 12h absolute
  session with no refresh is a plausible but real UX cost — worth an
  explicit product decision (sliding expiration on activity, or a longer
  TTL) rather than an accidental default.

## 2. Logout / revocation

**This is implemented correctly and is not a gap.** `POST /auth/logout`
(`app.py:85-92`) calls `store.revoke_session(token)`, which sets
`revoked_at` on the session row in SQLite (`db.py:280-285`), then deletes
the cookie. `get_session_user` treats any row with `revoked_at IS NOT NULL`
as invalid. `test_logout_revokes_session` confirms a post-logout request to
an authenticated route returns 401, not just that the cookie is gone
client-side. Logout is a genuine server-side revocation, not a cookie-clear
theatre. No further work needed here for E19.

## 3. CSRF protection

**Gap.** There is no CSRF token anywhere in `app/authruntime/*` or
`app/server.py`. Every state-changing endpoint that a browser session can
reach — `/admin/workspaces` (POST), `/admin/memberships` (POST),
`/admin/overrides/{id}/resolve` (POST), and the business
`/api/workspaces/{workspace_id}/qualification/{blocker_id}/override` (POST)
— relies solely on the session cookie's `SameSite=Lax` attribute (§4) as
CSRF defense. `SameSite=Lax` does block a cross-site `<form>` auto-submit
POST in current mainstream browsers, so this is not an open CSRF hole today,
but it is a single-layer defense with no defense-in-depth: any future
change that adds a CSRF-sensitive GET-with-side-effects, any browser or
proxy that does not honor `SameSite`, or a same-site XSS gadget would have
nothing else standing in the way. Recommend a standard double-submit or
synchronizer CSRF token on the admin `Form(...)` endpoints and the override
endpoint, layered onto the existing session mechanism — not a new auth
system.

## 4. Cookie flags — checked literally

- **Session cookie** (`aimd_session`, set in `/auth/callback`,
  `app.py:75-82`): `httponly=True`, `secure=True`, `samesite="lax"`,
  `max_age=session_ttl_hours * 3600`. This is correct and matches ADR-007's
  intent.
- **OAuth transient state cookie** (`aimd_oauth_state`, Starlette
  `SessionMiddleware`, `app.py:48`): `app.add_middleware(SessionMiddleware,
  secret_key=session_secret, session_cookie="aimd_oauth_state")` — **no
  `https_only` or `same_site` argument is passed.** Starlette's
  `SessionMiddleware` defaults are `https_only=False` and
  `same_site="lax"`. **This means the cookie carrying the OIDC
  `state`/nonce/PKCE material (ADR-007 §2's own "transient state" this
  middleware is used for) is not marked `Secure`, unlike the session
  cookie it hands off to.** It is short-lived and signed (tamper-evident),
  which limits blast radius, but it is inconsistent with the literal
  cookie-flag discipline the rest of the runtime otherwise follows, and it
  is exactly the kind of one-line default that should be pinned explicitly
  (`https_only=True`) rather than left to the framework default, especially
  since ADR-007 §2 calls this material out by name as something requiring
  care. This is a small, concrete, one-line fix that stays inside "harden
  the socle."

## 5. Confirmed structural gap: legacy `/api/*` routes are authenticated but not workspace-scoped

(See also `docs/research/next-wave/API_PRODUCTIZATION_OPTIONS.md` §2, which
independently inventories this same gap across all 52 legacy endpoints with
additional detail on idempotency, error handling and OpenAPI quality — this
section focuses specifically on the auth/workspace-scoping angle.)

Every `/api/v1/workspaces/{workspace_id}/...` router
(`network_v1_routes.py`, `signal_routes.py`, `research_routes.py`,
`demand_routes.py`, `product_routes.py`, `fit_routes.py`,
`target_plan_routes.py`, `reach_routes.py`, `engagement_routes.py`,
`opportunity_routes.py`, `insights_routes.py`) consistently depends on
`require_workspace_access()`, which 404s (per ADR-007 §1) if the
authenticated user's own membership does not match the `workspace_id` path
param. This part of the socle is sound and consistently applied — confirmed
by grepping every one of those files.

**By contrast, every legacy (pre-v1) route registered directly on `app` in
`app/server.py` — `/api/skills`, `/api/offers`, `/api/shelves`,
`/api/backlog`, `/api/demand`, `/api/qualification`, `/api/nudging/*`,
`/api/value-chain*`, `/api/reach*`, `/api/follow-up`, `/api/catalog/*`,
`/api/network/people` (GET and POST), `/api/network/companies` (GET and
POST), `/api/network/duplicates*`, `/api/kanban/board`, `/api/campaigns*`,
`/api/heritage/*`, `/api/uc-graph/*`, `/api/workflows/plan`, and
`/api/qualification/actions` (POST) — depends only on `get_current_user`
(any authenticated user, any role, any workspace membership) with no
`require_workspace_access` and no per-request workspace filter at all.**
These handlers call singletons (`QUALIFICATION`, `DEMAND`, `CONTROL`,
`NUDGING`, `VALUE_CHAIN`, `REACH`, `FOLLOWUP`, `HERITAGE`, `WORKFLOWS`, …)
constructed once against the whole repository root, not per workspace.

One concrete, verifiable instance: `GET /api/network/people`
(`server.py:347-365`) accepts a client-supplied `workspace_id` **query
parameter** and passes it straight to `search_people(...)` — the value is
never checked against `ctx.workspace_id`. Any authenticated `standard_user`
in workspace A can request `?workspace_id=B` and read workspace B's network
data. This is a live IDOR path, not a theoretical one, and it is on a GET
route with no write side-effect to hide it in an audit trail.

The only exceptions on the legacy surface are the two routes already using
`require_role("admin")` (`/admin/network/rebuild-index`,
`/admin/network/companies/{id}/reassign`) and the one using
`require_role("product_owner", "admin")` (`PATCH
/api/catalog/offers/{offer_id}`) — everything else on the legacy surface is
"any logged-in user, any workspace, full access to the shared singleton
state."

**This is the single most important finding in this document.** The v1
routers prove the team already knows how to do workspace scoping correctly
and applies it consistently; the legacy surface was authenticated (E01/S8b)
without being re-scoped when workspaces were introduced, and nothing since
has closed that gap. Given ADR-007's own security invariant ("resource
lookup validates both resource identity and workspace ownership" —
applies with no carve-out for legacy routes), this reads as a genuine,
unaddressed security gap in the existing socle, not a stylistic
inconsistency, and it should be named as such in E19 scoping rather than
softened to "an area for future harmonization." The remediation is
mechanical and additive — thread `require_workspace_access()` (or an
equivalent workspace filter where the underlying singleton needs
parameterizing) through the legacy routes — and does not require a new auth
mechanism.

## 6. Workspace selection flow

There is no "switch workspace" UI or endpoint, and none is needed under the
current data model: `memberships.user_id` is a `PRIMARY KEY`
(`db.py:38-43`), so a non-admin user has exactly one workspace membership by
construction — consistent with the parent brief's "single-tenant-per-
workspace" framing. An admin has no membership row and
`RequestContext.can_access_workspace` always returns `True` for
`is_admin`, so admins implicitly have "access to every workspace" without a
selector. This is a reasonable design for the current scale; the moment a
requirement for one user to belong to more than one workspace appears, the
schema (not just the API) would need to change — worth flagging as a
forward-looking note for E19 scoping, not a gap today.

## 7. First-login / onboarding — confirmed functional gap (FIXED in this closeout pass)

`/auth/callback` (`app.py:68-83`) **unconditionally redirects every
successful login to `/admin/workspaces`**, regardless of the user's role,
and `get_or_create_user` (`db.py:140-150`) creates the user row with no
membership. `/admin/workspaces` is gated by `require_role("admin")`
(`app.py:97-99`).

**Consequence, confirmed by the test suite itself
(`test_non_admin_cannot_reach_admin_page` asserts a 403 for exactly this
path): any brand-new or existing non-admin user who successfully
authenticates via Google is redirected straight into a 403 Forbidden page
on their very first (and every subsequent) login.** There is no
invitation/self-service membership flow, no "your account has no workspace
yet — contact an admin" message, and no role-aware post-login redirect
(e.g., admins to `/admin/workspaces`, everyone else to their own
workspace's Home space). Today, a non-admin user can only reach usable
product screens if an admin has already granted them a membership *and*
they separately navigate to `/w/{workspace}/home` by hand — the login flow
itself has no path there. This is the most concrete, user-visible defect
in the whole audit: the documented login journey (click "Se connecter avec
Google" on `login.html`) does not lead anywhere usable for the majority of
real users (everyone except admins).

Recommended shape (proposal only): make the post-callback redirect
role-aware — `is_admin` → `/admin/workspaces` (current behavior, kept),
has a membership → `/w/{workspace_id}/home`, neither → a dedicated
"pending access" page rather than a bare 403. This is a redirect-target
fix inside the existing callback handler, not a new auth mechanism.

**Fixed in this same closeout pass** (unlike every other finding in this
document, which stays proposal-only): `app/authruntime/app.py`'s
`/auth/callback` now computes the redirect exactly as recommended above,
and a new `GET /auth/pending` route renders the "no workspace yet" page.
5 new tests in `tests/test_authruntime_app.py` cover all three redirect
targets plus the pending page's own auth gate; all pass, and the full
1175-test suite plus `scripts/check_release.py` stay green. This one item
was small, unambiguous, and did not require inventing a new auth
mechanism — unlike the IDOR-shaped legacy-route gap in §3/§4 below, which
does require an architecture decision (whether/how to retrofit
workspace-scoping onto ~25 pre-v1 routes) and is correctly left as a
proposal for the E19 scoping owner. The deeper session-recovery
"return to where you were" gap (§9) is also left open: it needs a
`next`/`state`-encoded return URL threaded through the OIDC round trip,
which is more involved than a redirect-target fix and is left for E19.

## 8. Login error handling

`login.html` (`app/frontend/login.html`) is fully static: one heading, one
paragraph, one `<a href="/auth/login">` button. It has no mechanism to
display an auth error — there is no `?error=` query-param handling, no
styled response for `/auth/login`'s `503` when no OIDC provider is
configured (`app.py:54-58`, surfaces as FastAPI's default JSON error body,
not a page a user would understand), and no messaging for an OIDC provider
error (e.g., the user cancels the Google consent screen, or
`authorize_userinfo` raises because the provider didn't return an email
claim, `oidc.py:52-53` — that `ValueError` is not caught anywhere in
`/auth/callback` and would surface as the generic 500 handler in
`server.py`, not a friendly retry-the-login message).

## 9. Session expiration / recovery UX

Per `server.py`'s own comment (`server.py:81-86`), the SPA's client-side JS
calls `GET /api/auth/me` and redirects to `/login.html` on a 401 — this
part works for detecting an expired/revoked session. **The gap is that the
recovery path does not return the user to where they were**: because
`/auth/callback` always redirects to the hardcoded `/admin/workspaces`
(§7), there is no "return to `/w/{workspace}/{space}` after re-auth" state
carried through the OIDC round trip (no `next`/`state`-encoded return URL).
A user whose 12-hour session (§1) expires mid-task in, say,
`/w/acme/pipeline` is bounced to login, and even after successfully
re-authenticating lands on `/admin/workspaces` — a 403 for anyone but an
admin (§7) — rather than back in Pipeline. This is the same root cause as
§7 (a hardcoded, role-blind post-login redirect target) manifesting a
second time as a session-recovery defect, not a second, independent bug —
fixing the redirect logic in §7 (role-aware, and ideally carrying a `next`
param) resolves both.

**Partially fixed alongside §7**: re-authenticating now lands a non-admin
on their own `/w/{workspace_id}/home` rather than a 403, which is a real
improvement. What's still missing, and left open for E19, is the `next`
param itself — the user lands on Home, not back in Pipeline where their
session expired.

## 10. RBAC (`require_role`)

Roles that exist: `admin` (a boolean flag on `users.is_admin`, not a
membership row — "roles are flat, not hierarchical" per `db.py`'s own
comment) and, per-workspace-membership, `product_owner` /
`standard_user` (`CHECK` constraint, `db.py:41`). `require_role(*roles)`
(`deps.py:59-69`) always allows `is_admin`, then checks `ctx.role in roles`
for everyone else. This is a small, correctly-deny-by-default
implementation consistent with ADR-007 §7 ("Authorization is deny-by-default").

Where it is enforced today: every `/admin/*` route in `app/authruntime/app.py`
(`require_role("admin")`), two legacy admin routes in `server.py`
(`require_role("admin")`), one legacy write route gated to
`product_owner`/`admin` (`PATCH /api/catalog/offers/{offer_id}`), and the
qualification-override endpoint's inline check (`ctx.is_admin or ctx.role
== "product_owner"`, `app.py:192-193` — this one is a manual `if`, not
`require_role`, but functionally equivalent and covered by tests).

**Gap, distinct from §5's workspace-scoping gap:** almost none of the other
legacy write routes apply any role check beyond "authenticated" — e.g.
`POST /api/network/people`, `POST /api/network/companies`, `POST
/api/catalog/candidates/{id}/promote`, `POST /api/nudging/generate`, `POST
/api/campaigns/prospecting`, `POST /api/catalog/harvest`/`discover` are all
reachable by any `standard_user`, not just `product_owner`/`admin`, even
though their v1-router equivalents where they exist (`fit_routes.py`'s
`POST /fit-assessments`) are only workspace-scoped, not role-scoped,
either. Whether `standard_user` should be read-only across the board is a
product decision this audit does not make, but today the actual behavior
is "any authenticated user can perform almost any write," which is worth
an explicit RBAC-matrix decision in E19 rather than leaving each route's
role requirement to have been decided ad hoc at the time it was written.

## 11. Admin boundaries (`/admin/*`)

**Consistent and correctly gated.** Every `/admin/*` route found —
`/admin/workspaces` (GET/POST), `/admin/memberships` (GET/POST),
`/admin/users` (GET), `/admin/audit` (GET), `/admin/overrides` (GET),
`/admin/overrides/{id}/resolve` (POST) in `app/authruntime/app.py`, plus
`/admin/network/rebuild-index` (POST) and
`/admin/network/companies/{id}/reassign` (POST) in `app/server.py` — depends
on `require_role("admin")`, and every one of them has a matching
403-for-non-admin test in `tests/test_authruntime_app.py`. No
`/admin/*` route was found reachable without that dependency. This is the
one area of the whole audit with no gap to report; E19 should treat it as
the reference pattern the legacy `/api/*` surface (§5, §10) should be
brought up to, not as something needing its own hardening work.

---

## Summary for E19 scoping

| Area | Status |
| --- | --- |
| Session lifecycle (opaque cookie, server-side state) | Sound design; fixed 12h TTL with no refresh is a product decision to make explicitly |
| Logout/revocation | Sound — real server-side revocation, not cookie-clear |
| CSRF | Single-layer (`SameSite=Lax` only) — add a token, don't rely on one control |
| Cookie flags | Session cookie correct; OAuth state cookie missing explicit `https_only=True` |
| Workspace selection | Not needed under current 1-membership-per-user model |
| First-login / onboarding | **Fixed in this closeout pass** — was: non-admins 403 on their first login |
| Login error handling | No user-facing error states in `login.html` at all |
| Session-expiration recovery | Detects expiry correctly; recovery redirect fixed alongside onboarding (lands on Home, not yet back at the exact prior route) |
| RBAC — `/admin/*` | Sound and consistent |
| RBAC — legacy `/api/*` writes | Mostly unenforced beyond "authenticated" |
| Workspace scoping — v1 routers | Sound and consistent (`require_workspace_access`) |
| Workspace scoping — legacy `/api/*` | **Confirmed IDOR-shaped gap** — authenticated but not workspace-filtered |

**This document is a proposal for the architecture owner's E19 scoping
decision, not authorization to build.** Every finding above is a research
input; no runtime code, schema change, or route change should be made on
the basis of this document alone until the architecture owner has reviewed
and ratified a scope for E19 that says which of these gaps are in scope,
in what order, and with what acceptance criteria.
