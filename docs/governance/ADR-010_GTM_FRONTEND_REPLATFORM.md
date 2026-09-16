# ADR-010 — Frontend replatform E12

**Status:** accepted — 2026-09-17  
**Scope:** Epic 12 only

## Context

The current product is a FastAPI-served HTML/CSS/JavaScript SPA with no
production client build step. It already has authenticated workspace APIs and
three Playwright journeys. E12 needs deep links, an explicit workspace in the
URL, a job-based shell and accessible responsive navigation; it does not need
client-side server state or offline operation.

## Measured spike

Baseline measured on 2026-09-17: `app.js` is 885 lines / 72,452 bytes,
`index.html` is 342 lines / 20,502 bytes and `styles.css` is 298 lines /
18,374 bytes. The shell has eight DOM-switched panels but no URL router,
History API handling or authoritative workspace context.

| Criterion | Existing vanilla SPA | New framework + build pipeline |
| --- | --- | --- |
| Production build artifacts | 0 | new runtime/toolchain required |
| Existing route/API compatibility | direct | migration required |
| Workspace deep-link implementation | History API + explicit URL parser | router migration required |
| Test baseline | existing Playwright journeys | fixtures and harness migration required |
| E12 job-based shell requirement | satisfied by a small routing layer | satisfied, but no incremental gain demonstrated |

## Decision

Keep the existing dependency-free SPA for E12. Add a small, tested routing
and workspace-context layer in vanilla JavaScript, CSS design tokens and
feature-flagged shell components. Do not introduce React, a bundler or a
second client state store in this Epic.

The decision is conditional: navigation and workspace logic must be extracted
from `app.js`; new navigation behavior may not grow that monolith. Failure to
hold that boundary triggers a successor ADR before E12 release.

## Consequences

- The E12 migration is incremental and reversible at the shell boundary.
- Browser URL remains the sole active workspace/navigation context, avoiding
  cross-tab mutable state.
- Revisit only if the measured E12 component surface demonstrates a concrete
  maintainability or performance limit; any change requires a successor ADR.
