---
name: enterprise-icb-mapping
description: Map canonical company records to the FTSE Russell Industry Classification Benchmark with explicit level, evidence, confidence, conflicts, and validation status. Use when companies need ICB industry, supersector, sector, or subsector candidates for segmentation and sector rollups. Do not classify from contact job titles, force unknown companies, or treat name-pattern candidates as validated ICB assignments.
---

# Enterprise ICB Mapping

## Responsibility

Create reviewable ICB candidates independently of product fit and contact seniority.

Read [mapping-policy.md](references/mapping-policy.md) before confirming any classification.

## Procedure

1. Load the canonical company record and ICB v5.0 taxonomy.
2. Determine whether the entity is within the equity-company scope.
3. Use name rules only to seed a candidate.
4. Validate the primary revenue-generating activity with dated company evidence before upgrading the mapping.
5. Assign only the deepest defensible level.
6. Preserve alternatives, conflicts, confidence, and validation requirements.

Seed candidates with:

```bash
python scripts/map_companies_icb.py
```

When company evidence is missing, use the shared acquisition backend only as a discovery step to locate primary company evidence:

```bash
python scripts/advanced_research.py "<entreprise> revenue business segments annual report" --source web --days 730 --limit 10 --pretty
```

Do not use social/community results, retrieval relevance, contact titles, or inferred demand to validate ICB. The classification upgrade still requires dated evidence about the primary revenue-generating activity.

Write `data/private/network/company_icb_mappings.jsonl`. Never use an ICB candidate as evidence of enterprise demand.
