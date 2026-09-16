#!/usr/bin/env python3
"""Rebuild the derived SQLite search index over the private network JSONL layer.

Thin CLI wrapper over app.network_index.rebuild(). The JSONL files under
--data-root/network remain the canonical, versioned source of truth; this
index is read-side only, fully rebuilt (never incrementally patched) each
run, and safe to run against a repository with no private data yet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from network_common import ROOT

sys.path.insert(0, str(ROOT))

from app.network_index import rebuild  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=None,
        help="Defaults to <data-root>/network/network_index.sqlite",
    )
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    network_dir = data_root / "network"
    index_path = (args.index_path or (network_dir / "network_index.sqlite")).resolve()
    counts = rebuild(network_dir, index_path)
    print(f"people={counts['people']} companies={counts['companies']} relationships={counts['relationships']}")
    print(f"index_path={index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
