#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from app.catalog import CatalogHarvester

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover public company/vendor offer sources and stage them as unreviewed catalog candidates."
    )
    parser.add_argument("--company", required=True)
    parser.add_argument("--shelf", required=True)
    parser.add_argument("--domain")
    parser.add_argument("--query")
    parser.add_argument("--source", choices=["web", "perplexity"], default="web")
    parser.add_argument("--days", type=int, default=3650)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    result = CatalogHarvester(ROOT).discover_public(
        {
            "company": args.company,
            "shelf_id": args.shelf,
            "domain": args.domain,
            "query": args.query,
            "source": args.source,
            "days": args.days,
            "limit": args.limit,
        },
        persist=not args.preview,
    )
    print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
