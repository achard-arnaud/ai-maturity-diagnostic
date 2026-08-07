# User flows v0.6

## 1. Demand — from contact to sector intelligence

```text
Demand menu
-> choose ICB sector or search company
-> inspect readiness
   0 studies: Add contact/company
   1 study: Add another company
   2 studies: Add a 3rd company
   >=3: Launch benchmarking
-> open company
-> inspect study + use-case inventory
-> Add/update use flow
-> Harvest use cases
-> consolidate sector benchmark
```

### Add contact CTA
1. User chooses `Add contact`.
2. UI asks for private source path or explicit intake instruction.
3. It prepares `network-contact-intake`.
4. Guided SDLC shows the next steps: `enterprise-icb-mapping` -> `network-account-screening` -> `network-study-orchestration`.
5. User sees when the company becomes study-ready.

### Add a 3rd company CTA
1. Sector card shows `2 / 3 eligible`.
2. CTA is promoted to `Add a 3rd company`.
3. The flow asks for a company/contact source but does **not** assume that candidate belongs to the sector.
4. ICB validation remains mandatory.
5. Benchmark becomes available only after the third study is current and complete.

### Benchmark CTA
1. CTA disabled below 3 eligible studies.
2. At >=3, prepare `sector-intelligence-consolidation` with the selected sector rollup path.
3. Result remains exploratory if ICB mappings are candidate/mixed; decision-grade requires validated mappings.

## 2. Use-case harvesting

```text
company study
-> enterprise-use-case-intelligence
-> 05b_use_case_inventory.yaml
-> sector rollup ingestion
-> sector-intelligence-consolidation
```

The user can update a use flow without rerunning the whole company diagnosis, provided evidence/provenance is preserved.

## 3. Qualification & Matching

```text
Qualification menu
-> select study
-> cockpit identifies current stage
-> next CTA only
   Demand missing -> Refresh demand
   Snapshot missing -> Refresh offer snapshot
   Match missing -> Run matching
   Fit eligible + contacts available -> Target contacts
   Match eligible -> Design pilot
-> Full SDLC opens the complete gated sequence
```

The full sequence is guided and stateful, never blind batch execution.

## 4. Nudging

```text
Nudging menu
-> choose company use-case inventory
-> choose mode
   Productivization
   Dependency upsell
   Cross-sell package
-> deterministic preview
-> inspect evidence, prerequisites, unknowns, falsifier
-> optional unit call to use-case-nudging skill for richer narrative
-> record feedback before reusing the nudge
```

### Productivization
User starts from one existing use case and asks: how can this become cheaper, more repeatable, more reusable or richer?

### Upsell
User starts from one use case. The UI only offers explicitly connected `depends_on` / `enables` candidates.

### Cross-sell
User sees packages made from use cases already catalogued for the company. Storytelling cites that company’s own recorded feedback/outcomes.

## 5. Follow-up menu semantics

Every workflow item has one of:
- `ready` — CTA executable/preparable;
- `blocked` — gate missing, reason shown;
- `in_progress` — artifact exists but requires refresh/validation;
- `completed` — handoff artifact present;
- `review` — human validation required.

Follow-up views sort by blockers first, then stale work, then ready next actions.
