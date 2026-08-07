#!/usr/bin/env python3
"""Initialize an account qualification study with immutable product snapshots."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency failure path
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized.lower().strip())
    return normalized.strip("-") or "company"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def dump_yaml(path: Path, data: Any) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: str, parser: argparse.ArgumentParser) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        parser.error("--date must be a valid ISO date in YYYY-MM-DD format")
        raise AssertionError("unreachable")


def select_offers(raw: str, catalog: dict[str, dict[str, Any]], parser: argparse.ArgumentParser) -> list[str]:
    requested = list(catalog) if raw == "all" else [item.strip() for item in raw.split(",") if item.strip()]
    if not requested:
        parser.error("--offers must select at least one offer")
    if len(requested) != len(set(requested)):
        parser.error("--offers contains duplicate offer IDs")
    unknown = [item for item in requested if item not in catalog]
    if unknown:
        parser.error(f"Unknown offer IDs: {', '.join(unknown)}")
    return requested


def build_study(stage: Path, pkg: Path, company: str, company_id: str | None, study_date: str, study_name: str, requested: list[str], catalog_index: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> None:
    snapshots_dir = stage / "inputs" / "product_snapshots"
    snapshots_dir.mkdir(parents=True)
    (stage / "sources").mkdir()

    manifest = load_yaml(pkg / "templates" / "study_manifest.yaml")
    manifest.update(
        {
            "study_id": study_name,
            "company_id": company_id,
            "company": company,
            "created_at": study_date,
            "updated_at": study_date,
            "catalog_version": catalog_index["catalog_version"],
            "candidate_offers": requested,
            "product_snapshots": [],
        }
    )

    for offer_id in requested:
        source = pkg / "product_catalog" / catalog[offer_id]["file"]
        profile = load_yaml(source)
        offer = profile.get("offer", {})
        version = offer.get("profile_version")
        if offer.get("offer_id") != offer_id or not version:
            raise ValueError(f"Invalid catalog profile for {offer_id}")
        target_name = f"{offer_id}__{version}.yaml"
        target = snapshots_dir / target_name
        shutil.copy2(source, target)
        manifest["product_snapshots"].append(
            {
                "offer_id": offer_id,
                "profile_version": version,
                "path": f"inputs/product_snapshots/{target_name}",
                "sha256": sha256(target),
            }
        )

    dump_yaml(stage / "00_manifest.yaml", manifest)
    for name in (
        "01_strategy_evidence.yaml",
        "02_organization_evidence.yaml",
        "03_capability_signals.yaml",
        "04_newsflow_evidence.yaml",
    ):
        dump_yaml(stage / name, {"schema_version": "0.2", "sources": [], "claims": []})

    profile = load_yaml(pkg / "templates" / "enterprise_demand_profile.yaml")
    profile["study_id"] = study_name
    profile["company"] = company
    dump_yaml(stage / "05_enterprise_demand_profile.yaml", profile)

    fit = load_yaml(pkg / "templates" / "product_fit_matrix.yaml")
    fit["study_id"] = study_name
    fit["enterprise_profile_version"] = profile["profile_version"]
    fit["product_snapshots"] = manifest["product_snapshots"]
    dump_yaml(stage / "06_product_fit_matrix.yaml", fit)

    shutil.copy2(pkg / "templates" / "engagement_hypothesis.md", stage / "07_engagement_hypothesis.md")
    dump_yaml(
        stage / "08_validation_log.yaml",
        {
            "schema_version": "0.2",
            "events": [
                {
                    "event": "study_initialized",
                    "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    "catalog_version": catalog_index["catalog_version"],
                }
            ],
        },
    )


def install_stage(stage: Path, study_dir: Path, force: bool, parser: argparse.ArgumentParser) -> Path | None:
    backup: Path | None = None
    if study_dir.exists():
        if not force:
            parser.error(f"Study already exists: {study_dir}")
        manifest_path = study_dir / "00_manifest.yaml"
        if not manifest_path.is_file():
            parser.error(f"Refusing --force: existing directory is not a managed study: {study_dir}")
        backup = study_dir.with_name(
            f"{study_dir.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        )
        if backup.exists():
            parser.error(f"Backup target already exists: {backup}")
        study_dir.rename(backup)
    try:
        stage.rename(study_dir)
    except Exception:
        if backup is not None and not study_dir.exists():
            backup.rename(study_dir)
        raise
    return backup


def main() -> int:
    pkg = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("company")
    parser.add_argument("--company-id", default=None)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--root", type=Path, default=pkg / "studies")
    parser.add_argument("--offers", default="all", help="Comma-separated offer IDs or 'all'")
    parser.add_argument("--force", action="store_true", help="Replace a managed study and keep a timestamped backup")
    args = parser.parse_args()

    company = args.company.strip()
    if not company:
        parser.error("company must not be blank")
    study_date = parse_date(args.date, parser)

    catalog_index = load_yaml(pkg / "product_catalog" / "index.yaml")
    entries = catalog_index.get("offers", [])
    catalog = {item["offer_id"]: item for item in entries}
    requested = select_offers(args.offers, catalog, parser)

    study_name = f"{slugify(company)}-{study_date.replace('-', '')}"
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    study_dir = root / study_name
    stage = Path(tempfile.mkdtemp(prefix=f".{study_name}.tmp-", dir=root))
    try:
        build_study(stage, pkg, company, args.company_id, study_date, study_name, requested, catalog_index, catalog)
        backup = install_stage(stage, study_dir, args.force, parser)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    print(study_dir)
    if backup is not None:
        print(f"BACKUP: {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
