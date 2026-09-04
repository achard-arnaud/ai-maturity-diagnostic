# Output contract

The upstream skill owns the argument, evidence, recommendation, and source ledger. Nice Output Engine receives only a stable document specification.

Required document fields:

- `title`, `language`, `template`, and `theme`;
- ordered `pages` matching the registered page range;
- a decision or purpose for every page;
- preserved evidence labels and source identifiers.

Use `executive-brief-v1` only for the legacy dense card layout. Use `universal-sections-v1` for benchmarks, business notes, and application packs. A universal page contains a header, optional decision, ordered sections, and blocks. Blocks may contain a title, evidence status, metric, body, bullets, or a table with at most five columns.

Reject an input that contains unresolved placeholders, unsupported claims presented as facts, untraceable metrics, or more content than the page contract can carry. Return it to the functional skill rather than shrinking typography.


## Entity two-pager invariant

For `entity-two-pager`, accept only a frozen `executive_entity_brief` that references canonical company, external-product and person atoms.

The renderer must preserve every `core|material` product referenced by the brief in page 2 `product_spotlights`. If the page is too dense, return the brief to synthesis; never shrink or silently remove the product spotlight.
