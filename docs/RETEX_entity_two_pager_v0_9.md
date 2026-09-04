# RETEX v0.9 — canonical company × product × person two-pager

## Trigger case

The François Rivard / Gabriel Greenfield briefing exposed a useful asymmetry:

- narrative quality was strong;
- company and person coverage was strong;
- a named material methodology (Meridian) was present in the research;
- but no contract guaranteed a first-class product explanation in page 2.

The defect is therefore not primarily prose quality. It is **lack of runtime guarantee**.

## Current architecture before v0.9

The repository had:

- `company.schema.yaml`: private/network company registry, not public company intelligence;
- `person.schema.yaml`: private identity registry, not executive intelligence;
- `product_profile.schema.yaml`: our own canonical offer truth, unsafe for describing a target company's products;
- `business-intelligence-content.schema.json`: generic decision content with free-form `analysis`;
- a generic executive two-pager playbook;
- no entity-specific assembly contract;
- no gate that protected named external products/frameworks/methodologies from compression.

## Delta rubric

This rubric measures **structural guarantee**, not how good one human/LLM-written answer happens to be.

| Capability | Before | v0.9 target |
|---|---:|---:|
| Canonical external company intelligence atom | 0 | 1 |
| Canonical external product/intellectual-asset atom | 0 | 1 |
| Canonical public person intelligence atom | 0 | 1 |
| Stable cross-references between entity atoms | 0 | 1 |
| Material-product retention gate | 0 | 1 |
| Deterministic entity-specific two-page assembly | 0.5 | 1 |
| Persona relevance isolated from canonical target facts | 0 | 1 |
| Contract + regression-test enforcement | 0 | 1 |
| **Total** | **0.5 / 8 (6.25%)** | **8 / 8 (100%)** |

The 6.25% baseline does not mean the previous two-pager contained only 6.25% of useful information. It means almost none of that useful structure was enforceable by the artifact contracts.

## Architectural correction

```text
public evidence
  -> company_intelligence_atom
  -> external_product_intelligence_atom[*]
  -> person_intelligence_atom
  -> completeness/materiality gate
  -> executive_entity_brief
  -> nice-output-engine / entity-two-pager
```

Canonical atoms are audience-neutral.

Only `executive_entity_brief` may contain `francois-pro` or `sarah-pro` relevance.

## Product/materiality correction

The new rule is binary at assembly time:

> Every external product/framework/methodology classified `core` or `material` must have its own atom and must appear by ID in page 2 `product_spotlights`.

For the trigger case, this makes a Meridian-style method impossible to leave as only a passing company paragraph.

## Boundaries reinforced

1. **Target product ≠ internal offer.**
   External target offerings never enter `product_catalog/`.

2. **Public person intelligence ≠ private identity/contact record.**
   Career/thesis analysis does not mutate the private network registry.

3. **Persona fit ≠ target fact.**
   "Why this is interesting for François/Sarah" is a derived assembly inference.

4. **Rendering ≠ synthesis.**
   Nice Output Engine receives frozen content and cannot drop material entities to satisfy page density.

5. **Title ≠ authority.**
   The briefing can describe role and public positioning without inferring budget/decision rights.

## Regression test

`tests/test_entity_two_pager_contracts.py` checks:

- existence and separation of the three atom contracts;
- explicit exclusion of external target products from internal `product_catalog`;
- mandatory page-2 product spotlight;
- fixed two-page Nice template;
- metaprompt material-product retention language;
- balanced trigger evaluation for the new skill.
