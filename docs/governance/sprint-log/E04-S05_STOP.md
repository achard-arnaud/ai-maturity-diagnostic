# STOP — Epic 04 / Sprint S05

## Objective

Company 360 read model et provenance UI. Stop condition: "product data
absente" (no product data) -- API/UI contracts.

## Outputs

- `app/claim_store.py` / `app/evidence_store.py`: workspace-scoped
  `ArtifactStore`-backed JSONL storage for `CanonicalClaimV1`/
  `CanonicalEvidenceV1`, same shape as Epic 02/03's stores
  (upsert-by-id, filters, stable sort).
- `app/company360_view.py`: `get_company_360(root, workspace_id,
  company_entity_id)`. Aggregates a company's open `ResearchCase`s,
  active `Claim`s grouped by truth type (`fact`/`inference`/`hypothesis`,
  per `02_DOMAIN_AND_TRUTH_MODEL.md`), `unknowns` (hypotheses carrying a
  due date), `contradictions` (via S04's `find_contradictions`), and an
  evidence count -- never a claim body or an evidence excerpt copied
  wholesale, and, structurally, **never a product/catalog/offer/fit
  field anywhere in the view's shape**. `_FORBIDDEN_FIELD_TOKENS` names
  the banned vocabulary; the guard test walks every result key and every
  claim-type key against it, mirroring Epic 03's
  `signal_screening`'s "never a fit score" structural guard.
- `app/research_routes.py`: `GET
  /api/v1/workspaces/{workspace_id}/companies/{company_entity_id}/360`,
  reusing `require_workspace_access` for the same IDOR-safe
  cross-workspace 404 as every other v1 route. Wired into
  `app/server.py`'s `build_app`.
- `tests/test_claim_store.py` (5), `tests/test_evidence_store.py` (4):
  round-trip/isolation/filter tests, same shape as the other v1 stores.
- `tests/test_company360_view.py` (8): aggregation across case/claim/
  evidence stores, truth-type grouping, superseded claims excluded,
  unknowns, contradictions surfaced, empty-company case, and the 2
  structural product-data-absence guard tests.
- `tests/test_research_routes.py` (3): auth-required, own-workspace
  success, cross-workspace 404 (IDOR).

## Evidence

`python -m unittest tests.test_claim_store tests.test_evidence_store tests.test_company360_view tests.test_research_routes -v`:
20/20 pass. Full `python scripts/check_release.py`: 0 errors.
