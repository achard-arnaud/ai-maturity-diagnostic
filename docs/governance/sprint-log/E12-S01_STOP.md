# STOP — Epic 12 / Sprint S01

## Objective

Make a frontend-stack decision by measured migration cost, rather than
preference. Stop condition: **"stack décidée"**.

## Result

ADR-010 retains the dependency-free SPA: it already serves the required
authenticated API surface and needs only an incremental routing layer. A new
framework/build pipeline would add a migration without a demonstrated E12
benefit.

## Next

E12-S02 implements the workspace-safe shell, URL routes and design tokens.
