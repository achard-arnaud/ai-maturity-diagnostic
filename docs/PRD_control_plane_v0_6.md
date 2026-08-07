# PRD v0.6 — Demand catalog, qualification cockpit and use-case nudging

## Decision

v0.6 turns the existing ICB/network/study machinery into a navigable user journey. It does not replace any existing skill boundary.

The control plane exposes four operational surfaces:

1. **Demand** — ICB taxonomy -> sector -> companies -> studies -> use cases.
2. **Offers** — canonical offer shelves and product-truth lifecycle.
3. **Qualification & Matching** — gated crossing between demand truth and immutable offer snapshots.
4. **Nudging** — expansion hypotheses derived only from use-case inventory, dependency graph and recorded feedback.

## Demand catalog

### Navigation model

```text
ICB industry
  -> supersector
    -> sector
      -> companies
        -> current study
          -> use-case inventory
```

ICB classifies the browsing context. It never proves enterprise demand.

### Sector maturity states

| State | Rule | Primary CTA |
|---|---|---|
| Empty | 0 eligible company studies | Add contact / company |
| Building | 1 eligible study | Add another company |
| Benchmark edge | 2 eligible studies | Add a 3rd company |
| Benchmark ready | >=3 eligible current complete studies | Launch benchmarking |
| Consolidated | eligible rollup + use-case evidence | Refresh / deepen benchmark |

The existing `sector-intelligence-consolidation` threshold of three current sufficiently complete studies remains authoritative.

### Demand CTAs

- **Add contact** — prepare `network-contact-intake`; next governed steps are ICB mapping, screening and study queue.
- **Add/update use flow** — prepare `enterprise-use-case-intelligence` for one company/study.
- **Add a 3rd company** — prepare a guided demand-acquisition flow focused on filling a selected ICB sector, without treating sector membership as proof of need.
- **Launch benchmarking** — enabled only when sector eligibility is met; invokes `sector-intelligence-consolidation`.
- **Harvest/consolidate use cases** — extract company use-case inventories, then aggregate traceable sector use-case evidence.
- **Full demand SDLC** — guided sequence with explicit gates; never a silent one-shot chain.

## First-class use-case inventory

Each study may produce `05b_use_case_inventory.yaml`.

A use case records:
- stable use-case ID and company/study provenance;
- business line / workflow / job-to-be-done;
- problem and expected outcome;
- evidence status and supporting claim IDs;
- maturity state;
- explicit dependencies/enablers;
- repeatability and variant axes;
- reusable assets;
- recorded feedback and outcomes;
- confidence and unknowns.

Use-case intelligence remains product-blind. It may not name or recommend an offer.

## Qualification & Matching cockpit

The cockpit reads artifacts rather than chat memory.

```text
Demand profile ready
-> product snapshots present
-> hard-gate / fit matching
-> contact targeting if private network exists
-> engagement/pilot design
```

For every study it displays:
- current stage;
- present/missing artifacts;
- blockers/open gates;
- next owner skill;
- individual CTA;
- guided full-SDLC CTA.

No UI shortcut may bypass `qualification-tunnel-router` or let a score override a hard gate.

## Nudging workspace

### Boundary

Nudging does **not** perform initial account qualification. It does not read ICB classification, sector rollups, enterprise-demand scoring or offer fit.

Allowed inputs:
- company use-case inventory;
- use-case dependency/enabler graph;
- use-case maturity/repeatability metadata;
- recorded company feedback/outcomes.

### Modes

#### Productivization
Industrialize an already known use case: make it repeatable, enrich it, generate variants, standardize reusable assets or reduce marginal delivery cost.

This can create an up/down efficiency move without asserting a new business problem.

#### Upsell by dependency
Suggest a **dependent or enabled use case** only where an explicit graph relationship exists with a use case already specified for the company.

No dependency edge -> no upsell claim.

#### Cross-sell package
Package multiple already catalogued use cases for the company into a coherent story. The narrative must be anchored in that company’s recorded feedback, outcomes or operating experience.

### Nudge output
Every nudge contains:
- mode;
- source use-case IDs;
- proposed target/package IDs;
- rationale;
- evidence/feedback references;
- prerequisites;
- unknowns;
- falsifier;
- confidence;
- status `hypothesis` until reviewed.

A nudge is never a `PURSUE`/`VALIDATE` qualification decision.

## UX principles

- User sees lifecycle, not raw scripts.
- Each card answers: **where am I, what is missing, what can I do next?**
- Disabled CTAs explain the missing gate.
- `Full SDLC` creates a guided sequence with checkpoints and next actions.
- Demand and Offer use parallel visual grammar, but never share truth stores.
- Nudging is visually and conceptually distinct from Qualification.

## Acceptance criteria

1. ICB browser exposes sector readiness and companies without requiring private data to exist.
2. Third-company CTA appears at 2/3 eligible studies.
3. Benchmark CTA remains disabled below threshold 3.
4. Use-case inventory has a versioned contract and owner skill.
5. Sector rollups ingest use-case evidence when present.
6. Qualification cockpit derives stage from artifacts.
7. Nudging engine cannot receive ICB or product-fit inputs.
8. Productivization, upsell and cross-sell rules are separately testable.
9. UI exposes unit CTAs plus guided full-SDLC flows.
10. Existing v0.5 security/production gates remain open and visible.
