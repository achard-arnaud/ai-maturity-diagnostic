#!/usr/bin/env python3
"""Run the reproducible release gate for the public repository snapshot."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "data/private"}


def excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    return any(relative == part or relative.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def files_with_suffixes(*suffixes: str) -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and not excluded(path) and path.suffix in suffixes)


def run(label: str, command: list[str], errors: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        errors.append(f"{label} failed:\n{result.stdout}{result.stderr}".rstrip())
    else:
        print(f"PASS: {label}")


def parse_structured_files(errors: list[str]) -> None:
    for path in files_with_suffixes(".yaml", ".yml", ".json"):
        try:
            text = path.read_text(encoding="utf-8")
            data: Any = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
            if isinstance(data, dict) and data.get("$schema") == "https://json-schema.org/draft/2020-12/schema":
                Draft202012Validator.check_schema(data)
        except Exception as exc:
            errors.append(f"Invalid structured file {path.relative_to(ROOT)}: {exc}")
    if not any(message.startswith("Invalid structured file") for message in errors):
        print("PASS: YAML/JSON parsing and JSON Schema meta-validation")


def markdown_links(errors: list[str]) -> None:
    pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for path in files_with_suffixes(".md"):
        text = path.read_text(encoding="utf-8")
        for raw in pattern.findall(text):
            target = raw.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = target.split("#", 1)[0]
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"Markdown link escapes repository: {path.relative_to(ROOT)} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"Missing Markdown link: {path.relative_to(ROOT)} -> {target}")
    if not any("Markdown link" in message for message in errors):
        print("PASS: local Markdown links")


def privacy_and_portability(errors: list[str]) -> None:
    private_key = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")
    home_path = re.compile("/" + "home/coder/")
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file() and not excluded(item)):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if private_key.search(text):
            errors.append(f"Private key material detected in {path.relative_to(ROOT)}")
        if home_path.search(text):
            errors.append(f"Non-portable absolute home path detected in {path.relative_to(ROOT)}")
    if not any("Private key" in message or "home path" in message for message in errors):
        print("PASS: private-key and absolute-home-path scan")


def main() -> int:
    errors: list[str] = []
    run("package validator", [sys.executable, "scripts/validate_package.py"], errors)
    run("LinkedIn deferred-design validator", [sys.executable, "scripts/validate_linkedin_design.py"], errors)
    run("unit and integration tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], errors)
    parse_structured_files(errors)
    markdown_links(errors)
    privacy_and_portability(errors)

    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "example.docx"
        run(
            "DOCX example configuration",
            [
                sys.executable,
                "skills/tech-leadership-org-intelligence/scripts/build_org_tech_note.py",
                "--config",
                "skills/tech-leadership-org-intelligence/assets/examples/isagri_config.json",
                "--validate-only",
            ],
            errors,
        )
        run(
            "DOCX example generation",
            [
                sys.executable,
                "skills/tech-leadership-org-intelligence/scripts/build_org_tech_note.py",
                "--config",
                "skills/tech-leadership-org-intelligence/assets/examples/isagri_config.json",
                "--output",
                str(output),
            ],
            errors,
        )

    private_network = ROOT / "data" / "private" / "network" / "people.jsonl"
    if private_network.is_file():
        run("private network validator", [sys.executable, "scripts/validate_network.py"], errors)
    else:
        print("SKIP: private network validator (private data not present in clone)")

    for message in errors:
        print(f"ERROR: {message}")
    print(f"RESULT: {len(errors)} release error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
