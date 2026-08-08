# ADR-007 — Multi-workspace auth and runtime boundary

## Status

Proposed for v0.8 implementation. Parent RFC: #23.

## Context

The v0.7 control plane is intentionally local-first. Its HTTP adapter uses Python's `ThreadingHTTPServer`, constructs global services against one repository root, and has no authenticated user/workspace context. This is acceptable for local usage but unsafe to extend directly to multiple users or non-loopback deployment.

The goal is not to design a full SaaS architecture. The goal is the smallest reversible runtime boundary that gives real identity, isolation, authorization, errors, audit and operability.

## Decision

### 1. Introduce `workspace`, not technical `account`

`account/company` already means a commercial enterprise in the domain. A new `workspace` is the security and storage isolation boundary.

Every protected request resolves an immutable `RequestContext` from a verified session and membership. The client may request a workspace switch only among memberships already granted to the authenticated user; an arbitrary tenant header is never trusted as authority.

### 2. Externalize identity

The application will not store passwords or implement an identity provider.

Production-capable mode uses one configurable OIDC provider. Local development may run with auth disabled only while bound to loopback.

### 3. Use server-side revocable sessions

The browser receives only an opaque session identifier in a secure cookie. OIDC tokens and membership state remain server-side. This keeps logout, revocation and audit simple and avoids exposing provider tokens to frontend JavaScript.

### 4. Add a small runtime control store

SQLite/WAL is the first implementation target for users, workspaces, memberships, sessions and audit events. It is explicitly not the store for canonical business artifacts.

PostgreSQL is deferred until concurrency/topology requirements justify it.

### 5. Scope mutable/private file paths through `WorkspacePaths`

All workspace-specific data access goes through one path resolver rooted under `workspaces/<workspace_id>/`. Path escape checks remain mandatory. Shared read-only assets stay outside the workspace tree.

### 6. Replace only the HTTP adapter with ASGI

FastAPI/Starlette is recommended for the v0.8 boundary because middleware, dependency injection, validation and exception handlers become first-class. Existing business modules remain plain Python and must not import framework request/session objects.

### 7. Separate RBAC from business gates

Initial technical roles: reader, reviewer, contributor, admin. Authorization is deny-by-default.

RBAC permits a technical operation; it never turns an unproven claim into proof, changes an evidence confidence, or overrides a product-fit blocker.

### 8. Separate operational logs from audit

Operational logs are structured JSON and disposable. Audit records are append-only security/control events with explicit retention. Neither is a second source of business truth.

## Alternatives rejected

### Home-grown username/password auth
Rejected: unnecessary credential risk and maintenance burden.

### Signed cookie containing all session/membership state
Rejected as the primary production pattern: lightweight but weaker for revocation and workspace membership changes; a runtime store is already justified by audit.

### JWT-only stateless application sessions
Deferred: provider tokens still do not solve local workspace membership/revocation cleanly and would move complexity into every request.

### Full PostgreSQL/ORM from day one
Rejected for value-for-money: single-instance internal use does not yet justify it.

### Separate database/schema per workspace
Deferred: strong isolation but operationally excessive at the current scale. Workspace-scoped file roots plus control-store tenant checks are the first step. A future regulated deployment may choose stronger physical separation.

### Keep extending `BaseHTTPRequestHandler`
Rejected for multi-user runtime: possible, but auth/error/security middleware and typed contracts would become bespoke infrastructure.

### Microservices/Kubernetes
Rejected: no demonstrated scale or isolation need.

## Security invariants

- Workspace is derived from authenticated membership, never trusted from arbitrary user input.
- Resource lookup validates both resource identity and workspace ownership.
- All protected writes are workspace-scoped and audited.
- Local auth-disabled mode cannot start on a non-loopback interface.
- Tokens, cookies, secrets, private payloads and raw executor diagnostics are redacted from logs and responses.
- Cross-workspace access attempts are observable security events.
- Admin role does not override domain hard gates.

## Consequences

Positive:
- small number of new concepts;
- clear migration path to PostgreSQL/multi-instance later;
- current artifact contracts survive;
- framework migration is localized to web/runtime adapter;
- easier testing of 401/403/409/500 and request correlation.

Costs:
- one small control database and migration discipline;
- workspace path migration for mutable/private content;
- session lifecycle and OIDC callback handling;
- a deliberate product decision is still required for global vs workspace-scoped product catalog.

## Feedback gates before implementation release

1. Product owner: global/shared versus workspace-scoped `product_catalog`.
2. Deployment owner: first OIDC provider and reverse-proxy topology.
3. Security review: workspace context injection, IDOR and session threat model.
4. Value-for-money review: SQLite remains adequate for the actual deployment.
