# PRD v0.5 — Productized diagnostic control plane

## Decision

The repository remains the evidence-based enterprise AI qualification and intelligence system defined by `README.md` and `AGENTS.md`. v0.5 adds an **operable control plane** over that system; it does not create a second business model, duplicate product truth, or merge account research with offers.

## Problem

The repository already contains mature skills, contracts, scripts, product profiles, tests and evidence boundaries, but no single operable surface for:
- discovering the available skills;
- invoking one skill deliberately;
- seeing canonical offers by lightweight shelf;
- discovering and staging company/vendor offer catalogs before product review;
- seeing the remaining release/productization backlog.

This makes the system harder to operate and easier to misuse despite strong internal contracts.

## Users and jobs

| User | Job |
|---|---|
| Maintainer | Inspect the current skills and run one responsibility at a time. |
| Product owner | See offers and unresolved product-truth gates without loading account evidence. |
| Research/operator | Discover public vendor/company offer sources or stage an existing catalog as unreviewed candidates. |
| Reviewer | Inspect backlog, invocation versions and promotion gates. |
| Future runtime | Consume a stable unit-invocation envelope and return structured execution results. |

## Functional requirements

### Skill registry and unit invocation
The backend discovers `skills/*/SKILL.md`; the UI exposes one CTA per discovered skill. An invocation identifies the exact skill path and SHA-256 plus optional explicit context paths. The gateway never loads another skill implicitly.

If `AI_DIAGNOSTIC_SKILL_EXECUTOR` is absent, the system returns `status=prepared`. It must not claim a model or agent ran.

### Offer shelves
Shelves are a lightweight navigation taxonomy in `catalog_sources/shelves.yaml`. They point to `offer_id` values already present in `product_catalog/index.yaml`; they do not copy the canonical profiles.

### Company/vendor catalog harvest
Two acquisition paths are supported:
- public discovery through the existing public-first `advanced_research` backend (`web`, or optional first-party Perplexity when already configured);
- import of a catalog harvested elsewhere.

Both paths stage source-derived candidates under ignored `data/private/catalog_harvest/<company>/`. Every claim remains `unreviewed_source_claim`. Automatic promotion to `product_catalog/` is forbidden. Canonicalization requires `product-icp-intelligence` plus human review.

### Backlog
The UI consolidates the historical v0.3 release TODO with the v0.5 productization TODO. Historical gates remain open until independently closed.

## Non-functional requirements

- Python 3.11 baseline.
- No new web framework dependency for the first control-plane slice.
- Bind to `127.0.0.1` by default.
- No shell execution: the optional executor command is tokenized with `shlex` and receives JSON over stdin.
- Request bodies capped at 1 MB.
- Context paths must stay inside the repository.
- Network-accessible deployment is blocked until authentication, authorization and audit logging are implemented.

## Acceptance criteria

1. `python -m app.server` serves the frontend and API.
2. `/api/skills` reflects actual `SKILL.md` packages.
3. Each frontend skill card has an `Appel unitaire` CTA.
4. A call without a configured executor returns an honest prepared envelope.
5. Public catalog discovery and imported catalogs both remain unreviewed candidates.
6. Catalog staging never writes into `product_catalog/`.
7. Shelves reference canonical offers rather than copy their truth.
8. Existing `scripts/check_release.py` remains the release gate.
9. No existing README/AGENTS invariant is weakened.

## Explicit exclusions

The Sarah × Isabelle public questionnaire is a related product, not part of this control plane. Its diagnostic UX, scoring, email capture, consent, lead funnel and localization require a separate PRD and validation cycle.
