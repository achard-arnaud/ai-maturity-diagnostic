# STOP — Epic 06 / Sprint S04

## Objective

Catalog ownership/subscription model selon ADR-008 (Epic 01). Stop
condition: "pas de fuite cross-workspace" (no cross-workspace leakage) --
isolation/visibility.

## Outputs

- `contracts/product_v1.schema.yaml` extended with
  `overlay_of_product_id`: set only on a workspace overlay that
  explicitly supersedes a shared product; always null on a shared
  product or a standalone workspace product.
- `app/product_visibility.py`:
  - `filter_visible_products`/`filter_visible_snapshots`: the
    ADR-008 projection -- every shared-core entry, plus the calling
    workspace's own overlays, never another workspace's.
  - `validate_overlay_product(product, shared_product_ids)`: a shared
    product can never carry `overlay_of_product_id`; a workspace
    product's `overlay_of_product_id`, if set, must name an *existing*
    shared product -- referencing a nonexistent one is exactly the
    silent-shadowing failure ADR-008 forbids, and is rejected
    (`OverlayError`), never silently accepted.
- `tests/test_product_visibility.py`: 8 tests -- shared products visible
  to every workspace; a workspace overlay visible only to its own
  workspace; the core no-leakage property with a mixed catalog (shared +
  two different workspaces' overlays, each workspace sees exactly shared
  + its own, and explicitly *not* the other's); the same rule applied to
  snapshots; overlay validation (shared-can't-overlay, standalone
  workspace product valid, overlay of an existing shared product valid,
  overlay of a nonexistent shared product rejected as silent shadowing).

## Evidence

`python -m unittest tests.test_product_visibility -v`: 8/8 pass.
Full `python scripts/check_release.py`: 0 errors.
