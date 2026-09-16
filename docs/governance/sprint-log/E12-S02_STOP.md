# STOP — Epic 12 / Sprint S02

## Objective

Introduce the GTM shell, workspace-safe deep links and route-owned context.

## Result

The shell exposes the nine target spaces. `/w/{workspace}/{space}` URLs are
served by FastAPI and interpreted by an extracted History API router. The
authenticated session workspace is authoritative: a mismatched or malformed
route is replaced with that workspace's Home route. No mutable browser storage
holds workspace context.

## Evidence

`python -m unittest tests.test_gtm_router_contract -v`
