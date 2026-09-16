"""Workspace-scoped storage for CanonicalProductV1 records (Epic 06 S05).

Same ArtifactStore-backed JSONL shape as the other v1 stores. Products
are stored in a single flat index (like app.product_snapshot_store) --
visibility filtering (ADR-008) happens at the read-model/route layer via
app.product_visibility, not in this storage layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/products/products.jsonl"


class ProductStoreError(RuntimeError):
    pass


class ProductNotFound(ProductStoreError):
    pass


def _read_all(store: ArtifactStore) -> list[dict[str, Any]]:
    result = store.read_bytes(_RELATIVE_PATH)
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_product(root: Path, product: dict[str, Any]) -> None:
    store = ArtifactStore(root)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["product_id"] != product["product_id"]]
        records.append(product)
        records.sort(key=lambda r: r["product_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(_RELATIVE_PATH, _updater)


def get_product(root: Path, product_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store):
        if record["product_id"] == product_id:
            return record
    raise ProductNotFound(f"product {product_id} not found")


def list_all_products(root: Path) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = _read_all(store)
    records.sort(key=lambda r: r["product_id"])
    return records
