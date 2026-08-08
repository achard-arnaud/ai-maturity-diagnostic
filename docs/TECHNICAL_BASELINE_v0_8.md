# Technical baseline review — v0.8

## TL;DR

The v0.7 codebase is a strong local control-plane prototype with explicit domain boundaries and a real release gate, but it is not yet a network/multi-user runtime. The next technical investment should be concentrated in the HTTP/runtime boundary, workspace isolation, file integrity, packaging and observability rather than rewriting the business core.

## What is already solid

- Domain responsibilities are split into plain Python modules rather than embedded in the frontend.
- Path traversal for skill context is checked relative to the repository root.
- Skill execution does not use a shell and has an explicit timeout.
- Request bodies are bounded at the current HTTP adapter.
- The application defaults to loopback binding.
- The release gate parses structured files, validates package resources/contracts, scans for private-key material/non-portable paths, runs tests and enforces >=80% application coverage.
- GitHub and GitLab both call the same `scripts/check_release.py`, reducing semantic CI drift.
- Private network data is ignored by Git.

## P0 before non-loopback exposure

### 1. Identity and workspace isolation
Current state: one global repository root, no user identity, no tenant/workspace boundary.

Required:
- RequestContext from verified authentication;
- WorkspacePaths for every mutable/private lookup;
- membership authorization at the data-access boundary;
- adversarial cross-workspace tests.

Owner: #17 / RFC #23.

### 2. Executor data leakage
Current `RepoControlPlane.invoke` captures and returns raw subprocess stdout/stderr and runs with the parent environment.

Required:
- allowlisted child environment;
- bounded diagnostic capture;
- redaction;
- safe public result envelope;
- audit + request correlation;
- workspace-scoped context paths.

Owner: #17 / RFC #23.

### 3. Error boundary
Current domain errors are largely collapsed into HTTP 400 and unexpected exceptions have no stable safe public envelope.

Required:
- typed error hierarchy;
- standard HTTP mapping;
- request/error IDs;
- server-side exception trace only;
- safe client messages.

Owner: RFC #23.

### 4. Network hardening
Current local-first server has no authentication middleware, CSRF/origin model, host allowlist, rate limiting or security-header policy.

Required before network exposure:
- reverse-proxy HTTPS;
- auth/session middleware;
- trusted host/proxy handling;
- CSRF/origin controls;
- rate limits on auth/expensive routes;
- CSP/nosniff/referrer/frame policy;
- minimal public health output.

Owner: #17 / RFC #23.

## P1 operability / correctness

### 5. HTTP adapter maintainability
Current stdlib `ThreadingHTTPServer` is intentionally simple and dependency-light, but multi-user auth/error/logging would require extensive bespoke middleware.

Recommendation: migrate only the HTTP adapter to FastAPI/Starlette. Keep domain modules framework-independent.

### 6. File-write integrity
Current mutable files are written directly in several flows. Concurrent users could race or observe partial logical updates.

Recommendation:
- shared atomic-write helper;
- resource/workspace write locks;
- optimistic version checks for interactive edits;
- no wholesale SQL migration of business artifacts.

Owner: #24.

### 7. Packaging
`pyproject.toml` currently declares `packages = []`. Tests pass in a repository checkout because modules are available from the working directory, but that is not a production artifact contract.

Recommendation:
- install `app` explicitly;
- define service entry point;
- build/test a wheel or container from CI;
- run production smoke tests from built artifact rather than repository cwd.

Owner: #24.

### 8. Configuration
Runtime configuration is currently read ad hoc from environment variables in several code paths.

Recommendation:
- one validated Settings object at startup;
- explicit `dev/test/prod` behavior;
- fail closed on invalid security configuration;
- no secret values in startup output.

Owner: #24 / #17.

### 9. Structured logging
Current HTTP logs are `BaseHTTPRequestHandler` text logs and startup uses `print`.

Recommendation:
- stdlib `logging` with JSON formatter first;
- request_id, workspace, actor, route, status, duration, error/skill metadata;
- keep vendor APM optional.

Owner: #24.

### 10. Health and lifecycle
Current `/api/health` returns runtime details such as executor configuration and there is no distinction between process liveness and readiness.

Recommendation:
- `/health/live`: process alive;
- `/health/ready`: sanitized dependency/config readiness;
- graceful shutdown of server/executor operations.

Owner: #24.

## P1/P2 supply chain and CI

### 11. Dependency/action updates
The project has bounded dependency ranges but no repository configuration for routine automated updates. GitHub Actions currently uses action versions whose runtime emits Node deprecation warnings in CI.

Recommendation:
- Dependabot (Python + GitHub Actions) or equivalent;
- refresh action majors/current runtime;
- add dependency vulnerability check;
- consider action SHA pinning for production-sensitive workflows once maintenance ownership is clear.

Owner: #24.

### 12. Lint / typing
There is no lightweight lint/format gate.

Recommendation:
- add Ruff first because it has low operational cost;
- defer broad strict typing until it solves observed defects; targeted typing around RequestContext, Settings, errors and persistence contracts is more valuable initially.

Owner: #24.

### 13. Dual CI
Both `.github/workflows/qa.yml` and `.gitlab-ci.yml` run the same release script. This is acceptable and actually useful if both hosting surfaces remain relevant.

Guardrail:
- keep business/release semantics in `scripts/check_release.py`;
- avoid duplicating logic independently in YAML CI definitions.

## P2 — only after measured need

- PostgreSQL instead of SQLite control store;
- multi-instance application deployment;
- Redis/cache/queue;
- graph/vector runtime;
- Kubernetes;
- external APM vendor lock-in;
- SAML/SCIM or complex policy engine.

Each requires a measured concurrency, compliance, latency, reliability or administration need.

## Recommended implementation order

1. Close v0.7 release discrepancy/hotfix and synchronize main/dev.
2. Implement Settings + typed errors + request IDs/log redaction while still local.
3. Introduce WorkspacePaths and cross-workspace tests.
4. Add SQLite control store + User/Workspace/Membership/Session/Audit.
5. Migrate HTTP adapter to ASGI and wire RequestContext/RBAC.
6. Add generic OIDC and secure browser sessions.
7. Harden executor and atomic writes.
8. Add deployment artifact, security headers/rate limits/readiness.
9. Run security/spec review and only then permit non-loopback deployment.
10. Reassess PostgreSQL/multi-instance only from real usage.
