# ADR-004 — Web control plane is orchestration, not business truth

- Status: accepted for v0.5 implementation
- Date: 2026-08-07

## Context

The repository needs a frontend/backend surface and unit CTAs for skills. A naïve web application could accidentally duplicate scoring, product profiles, account evidence or matching logic in UI code, breaking the architecture documented in `README.md`, `AGENTS.md` and `docs/00_architecture_and_audit.md`.

## Decision

The web layer is a thin adapter.

It may:
- discover skills and their versions;
- prepare or dispatch one explicit skill invocation;
- read offer indexes and shelf navigation;
- stage unreviewed company/vendor catalog candidates;
- display TODOs and runtime state.

It may not:
- create product truth from account evidence;
- research an account while a product skill is active;
- bypass hard gates or calculate a competing fit score;
- promote a harvested claim into a canonical offer automatically;
- silently invoke multiple skills or rely on cross-skill memory;
- strengthen claims in the frontend.

The production skill runtime is an adapter behind `AI_DIAGNOSTIC_SKILL_EXECUTOR`. Until configured, the backend returns a prepared invocation and explicitly states that no execution occurred.

## Consequences

The first web slice can remain dependency-light and reversible. Product truth, account truth and matching remain versioned in their existing artifacts. Network deployment is not production-ready until auth/RBAC/audit work is complete.
