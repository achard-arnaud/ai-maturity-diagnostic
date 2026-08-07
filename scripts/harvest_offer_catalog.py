#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from app.catalog import CatalogHarvester
from app.core import RepoControlPlane

ROOT = Path(__file__).resolve().parents[1]


def load_items(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError("input must be a JSON/YAML list or an object containing items")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage a company/vendor offer catalog without mutating canonical product truth."
    )
    parser.add_argument("--company")
    parser.add_argument("--shelf")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--list-shelves", action="store_true")
    args = parser.parse_args()

    if args.list_shelves:
        for shelf in RepoControlPlane(ROOT).list_shelves():
            print(f"{shelf.get('shelf_id')}\t{shelf.get('name')}")
        return 0

    missing = [name for name in ("company", "shelf", "input") if getattr(args, name) is None]
    if missing:
        parser.error("required unless --list-shelves: " + ", ".join(f"--{name}" for name in missing))

    result = CatalogHarvester(ROOT).stage(
        {
            "company": args.company,
            "shelf_id": args.shelf,
            "items": load_items(args.input),
            "source_kind": "file_import",
        },
        persist=not args.preview,
    )
    print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
