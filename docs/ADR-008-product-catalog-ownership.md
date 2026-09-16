# ADR-008 — Product catalog ownership is shared-core plus workspace overlays

## Status

Accepted for Epic 01, Sprint 01.

## Context

The legacy default workspace reads `product_catalog/` from the repository root. Non-default workspaces resolve business paths below `workspaces/<id>/`, which currently makes the catalog either invisible or accidentally duplicated. The catalog is business truth, not runtime control state, and must not be moved into SQLite.

## Decision

Adopt a hybrid publication/subscription model:

1. `product_catalog/` at repository root is the shared, read-only published catalog.
2. `workspaces/<id>/product_catalog/` contains workspace-owned drafts and optional published overlays.
3. A workspace catalog view is a deterministic projection: shared published entries plus its own overlays.
4. An overlay may add an offer or supersede a shared offer only with an explicit `base_offer_id`, version and provenance. Silent shadowing is forbidden.
5. Writes always target the workspace overlay, except explicit product-owner publication to the shared catalog.
6. Fit records continue to reference immutable snapshot IDs and hashes; changing visibility never changes historical fit inputs.
7. The default legacy workspace remains backward-compatible with the root catalog during migration.

## Authorization

- `standard_user`: read visible published catalog entries.
- `product_owner`: create/review workspace drafts and publish workspace overlays.
- global publication: explicit privileged operation, separately audited.

RBAC permits an operation; it never overrides product hard gates or evidence requirements.

## Consequences

Positive: shared truth is reusable; tenant customization is possible; historical fits remain reproducible; no early SQL migration.

Costs: catalog reads need a projection/merge layer; publication needs conflict detection; overlays require provenance and version validation.

## Rejected alternatives

- Global-only: prevents legitimate workspace-owned offers.
- Workspace-only copies: creates drift and expensive duplication.
- Catalog in control SQLite: creates a second business truth and violates ADR-004/007.

## Compatibility and rollback

Before the projection layer ships, existing root reads remain authoritative for the default workspace. The decision can be rolled back by disabling overlays; no shared entry is rewritten by an overlay.
