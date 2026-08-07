# ICB mapping policy

Use `data/taxonomies/icb_v5_2026.yaml`, sourced from FTSE Russell ICB Equity v5.0, March 2026.

## Assignment rule

Classify from the source of revenue or majority of revenue when available. Do not classify from:

- a contact’s function;
- the technology stack;
- the product the seller wants to propose;
- a parent name when the record is a distinct operating entity;
- a single unverified name pattern.

## Status

- `candidate`: a plausible branch requiring company evidence;
- `validated`: primary company evidence supports the revenue activity;
- `pending`: insufficient information;
- `conflict`: multiple branches remain plausible;
- `out_of_scope`: public, academic, judicial, nonprofit, or other non-equity entity.

Use `sector` only when evidence supports it. Do not infer a subsector from this contact file.
