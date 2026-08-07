# Output contract

The upstream skill owns the argument, evidence, recommendation, and source ledger. Nice Output Engine receives only a stable document specification.

Required document fields:

- `title`, `language`, `template`, and `theme`;
- ordered `pages` matching the registered page range;
- a decision or purpose for every page;
- preserved evidence labels and source identifiers.

Use `executive-brief-v1` only for the legacy dense card layout. Use `universal-sections-v1` for benchmarks, business notes, and application packs. A universal page contains a header, optional decision, ordered sections, and blocks. Blocks may contain a title, evidence status, metric, body, bullets, or a table with at most five columns.

Reject an input that contains unresolved placeholders, unsupported claims presented as facts, untraceable metrics, or more content than the page contract can carry. Return it to the functional skill rather than shrinking typography.
