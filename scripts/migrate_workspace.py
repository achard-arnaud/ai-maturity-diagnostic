#!/usr/bin/env python3
"""Plan, apply or roll back a workspace migration. Dry-run is the default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.workspace_migrator import WorkspaceMigrator


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--rollback", type=Path)
    parser.add_argument("--plan", type=Path, help="Apply an existing dry-run plan JSON instead of regenerating it")
    args = parser.parse_args()

    migrator = WorkspaceMigrator(ROOT, args.workspace_id)
    if args.rollback:
        print(json.dumps(migrator.rollback(args.rollback), ensure_ascii=False, indent=2))
        return 0
    plan = json.loads(args.plan.read_text(encoding="utf-8")) if args.plan else migrator.plan()
    if args.apply:
        print(json.dumps({"manifest": str(migrator.apply(plan))}, indent=2))
    else:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
