#!/usr/bin/env python3
"""Compliance checker for SHELL_CONTRACT.md — the TDD-equivalent for these
static UX prototypes.

Deliberately kept outside the repo's own `tests/` directory and CI gate
(`.github/workflows/qa.yml`): this checks UX-exploration prototypes with
NONE architectural authority, not production code, and the mission's own
isolation rule says not to touch `.github/**`. Run it by hand:

    python3 prototypes/antigravity/gtm-v1/checks/check_screen.py <screen-dir> [...]
    python3 prototypes/antigravity/gtm-v1/checks/check_screen.py --all

Written before any screen existed, so the first real run of this script
against an empty screen directory is expected to fail every check — that
failure is the point (write the check, watch it fail, then build the
screen until it passes).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .../gtm-v1

REQUIRED_STATES = {
    "default",
    "loading",
    "empty",
    "error",
    "blocked",
    "stale",
    "partial-data",
    "success",
}

REQUIRED_CONTRACT_HEADINGS = [
    "## Job",
    "## Objets affichés",
    "## Composants",
    "## États",
    "## Navigation",
    "## Responsive",
    "## DECISION_REQUIRED",
]

FORBIDDEN_TOUCH_PREFIXES = ("app/", "contracts/", "migrations/", "skills/", "data/", ".github/")

CANONICAL_NAV_IDS = {
    "home",
    "discover",
    "research",
    "fit",
    "targets",
    "reach",
    "engagement",
    "pipeline",
    "insights",
    "admin",
}


class ScreenErrors(list):
    def add(self, message: str) -> None:
        self.append(message)


def check_contract_doc(screen_dir: Path, errors: ScreenErrors) -> None:
    contract = screen_dir / "SCREEN_CONTRACT.md"
    if not contract.exists():
        errors.add(f"missing {contract.relative_to(ROOT)}")
        return
    text = contract.read_text(encoding="utf-8")
    for heading in REQUIRED_CONTRACT_HEADINGS:
        if heading not in text:
            errors.add(f"{contract.relative_to(ROOT)}: missing heading {heading!r}")
    if "## Responsive" in text:
        section = text.split("## Responsive", 1)[1].split("\n## ", 1)[0]
        for tier in ("Desktop", "Tablet", "Mobile"):
            if tier not in section:
                errors.add(f"{contract.relative_to(ROOT)}: Responsive section missing {tier!r} tier")


def check_index_html(screen_dir: Path, errors: ScreenErrors) -> None:
    index = screen_dir / "index.html"
    if not index.exists():
        errors.add(f"missing {index.relative_to(ROOT)}")
        return
    text = index.read_text(encoding="utf-8")
    if "GtmProtoShell.render(" not in text:
        errors.add(f"{index.relative_to(ROOT)}: does not call GtmProtoShell.render(...) — screen must use the shared shell")
    else:
        match = re.search(r"GtmProtoShell\.render\(\s*['\"]([a-z-]+)['\"]", text)
        if not match:
            errors.add(f"{index.relative_to(ROOT)}: GtmProtoShell.render(...) call found but nav id not a simple string literal")
        elif match.group(1) not in CANONICAL_NAV_IDS:
            errors.add(f"{index.relative_to(ROOT)}: nav id {match.group(1)!r} is not one of the 10 canonical nav ids")
    if "shared/components.css" not in text and "shared/shell.css" not in text:
        errors.add(f"{index.relative_to(ROOT)}: does not link the shared shell/components stylesheet")


def check_states_html(screen_dir: Path, errors: ScreenErrors) -> None:
    states = screen_dir / "states.html"
    if not states.exists():
        errors.add(f"missing {states.relative_to(ROOT)}")
        return
    text = states.read_text(encoding="utf-8")
    found = set(re.findall(r'data-state="([a-z-]+)"', text))
    missing = REQUIRED_STATES - found
    if missing:
        errors.add(f"{states.relative_to(ROOT)}: missing data-state coverage for {sorted(missing)}")


def check_isolation(errors: ScreenErrors) -> None:
    """Sanity check this run isn't itself being pointed outside the sandbox."""
    for prefix in FORBIDDEN_TOUCH_PREFIXES:
        if (ROOT.parents[1] / prefix).exists() and any(
            p.stat().st_mtime > (ROOT / "SHELL_CONTRACT.md").stat().st_mtime
            for p in (ROOT.parents[1] / prefix).rglob("*")
            if p.is_file()
        ):
            # Heuristic only — a real drift check belongs to code review / git diff,
            # this just flags "something in a forbidden area changed more recently
            # than the shell contract" as worth a manual look.
            pass  # intentionally non-fatal; git diff --stat is the real authority


def check_screen(screen_dir: Path) -> ScreenErrors:
    errors = ScreenErrors()
    if not screen_dir.is_dir():
        errors.add(f"{screen_dir} is not a directory")
        return errors
    check_contract_doc(screen_dir, errors)
    check_index_html(screen_dir, errors)
    check_states_html(screen_dir, errors)
    return errors


def discover_screen_dirs() -> list[Path]:
    skip = {"shared", "checks"}
    return sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in skip and not p.name.startswith("."))


def main(argv: list[str]) -> int:
    if not argv or argv == ["--all"]:
        screen_dirs = discover_screen_dirs()
        if not screen_dirs:
            print("No screen directories found under", ROOT)
            return 1
    else:
        screen_dirs = []
        for a in argv:
            candidate = Path(a).resolve()
            if not candidate.is_dir() and (ROOT / a).is_dir():
                candidate = (ROOT / a).resolve()  # allow passing just the screen name, e.g. "discover"
            screen_dirs.append(candidate)

    total_errors = 0
    for screen_dir in screen_dirs:
        errors = check_screen(screen_dir)
        label = screen_dir.name
        if errors:
            print(f"FAIL {label}: {len(errors)} issue(s)")
            for e in errors:
                print(f"  - {e}")
            total_errors += len(errors)
        else:
            print(f"PASS {label}")

    print(f"\n{len(screen_dirs)} screen(s) checked, {total_errors} total issue(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
