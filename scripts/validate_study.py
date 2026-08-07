#!/usr/bin/env python3
"""Validate a qualification-tunnel v0.2 study and its boundary invariants."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Iterator

from qualification_common import (
    FIT_DECISIONS,
    FIT_DIMENSION_WEIGHTS,
    gate_errors,
    normalized_decision,
    weighted_fit_score,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency failure path
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


REQUIRED = (
    "00_manifest.yaml",
    "01_strategy_evidence.yaml",
    "02_organization_evidence.yaml",
    "03_capability_signals.yaml",
    "04_newsflow_evidence.yaml",
    "05_enterprise_demand_profile.yaml",
    "06_product_fit_matrix.yaml",
    "07_engagement_hypothesis.md",
    "08_validation_log.yaml",
)
EVIDENCE_FILES = REQUIRED[1:5]
FORBIDDEN_ENTERPRISE_FIELDS = {"recommended_offer", "offer_score", "astraforge_fit"}
DIMENSIONS = set(FIT_DIMENSION_WEIGHTS)
DECISIONS = FIT_DECISIONS


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def validate_match(match: dict[str, Any], known_snapshots: dict[str, dict[str, Any]], errors: list[str]) -> None:
    offer_id = match.get("offer_id")
    label = str(offer_id or "<missing offer_id>")
    if offer_id not in known_snapshots:
        errors.append(f"Match references unknown snapshot: {label}")
    elif match.get("product_profile_version") != known_snapshots[offer_id].get("profile_version"):
        errors.append(f"Match profile version mismatch: {label}")

    for field in DIMENSIONS:
        value = match.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
            errors.append(f"{label}: {field} must be an integer from 0 to 5")
    score = match.get("score")
    if score is not None and (not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100):
        errors.append(f"{label}: score must be null or between 0 and 100")
    decision = str(match.get("decision", "")).lower()
    if decision not in DECISIONS:
        errors.append(f"{label}: invalid decision {decision!r}")
    for problem in gate_errors(match):
        errors.append(f"{label}: {problem}")
    expected_score = weighted_fit_score(match)
    if score is not None and expected_score is not None and abs(float(score) - expected_score) > 0.01:
        errors.append(f"{label}: score {score} does not equal weighted score {expected_score:g}")
    if decision in {"pursue", "validate"} and not match.get("invalidators"):
        errors.append(f"{label}: positive decision requires at least one invalidator")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study_dir", type=Path)
    args = parser.parse_args()
    root = args.study_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        parser.error(f"Not a study directory: {root}")
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"Missing {name}")
    if errors:
        for message in errors:
            print("ERROR:", message)
        print(f"RESULT: {len(errors)} error(s), 0 warning(s)")
        return 1

    try:
        manifest = load(root / "00_manifest.yaml")
        profile = load(root / "05_enterprise_demand_profile.yaml")
        fit = load(root / "06_product_fit_matrix.yaml")
        validation_log = load(root / "08_validation_log.yaml")
    except Exception as exc:
        print("ERROR:", exc)
        print("RESULT: 1 error(s), 0 warning(s)")
        return 1

    study_id = manifest.get("study_id")
    if not study_id or study_id != profile.get("study_id") or study_id != fit.get("study_id"):
        errors.append("study_id mismatch across manifest, enterprise profile, and fit matrix")
    if not manifest.get("company") or manifest.get("company") != profile.get("company"):
        errors.append("company mismatch across manifest and enterprise profile")
    for label, data in (("manifest", manifest), ("enterprise profile", profile), ("fit matrix", fit), ("validation log", validation_log)):
        if data.get("schema_version") != "0.2":
            errors.append(f"{label}: schema_version must be 0.2")

    required_profile = {
        "study_id",
        "profile_version",
        "company",
        "evidence_claims",
        "strategic_priorities",
        "capability_gaps",
        "buying_context",
        "constraints",
        "unknowns",
        "confidence",
    }
    missing_profile = required_profile - set(profile)
    if missing_profile:
        errors.append(f"Enterprise profile missing fields: {sorted(missing_profile)}")
    leaked = FORBIDDEN_ENTERPRISE_FIELDS.intersection(walk_keys(profile))
    if leaked:
        errors.append(f"Enterprise profile contains forbidden product-fit fields: {sorted(leaked)}")
    if fit.get("enterprise_profile_version") != profile.get("profile_version"):
        errors.append("enterprise_profile_version mismatch")

    for name in EVIDENCE_FILES:
        try:
            evidence = load(root / name)
            if evidence.get("schema_version") != "0.2" or not isinstance(evidence.get("claims"), list):
                errors.append(f"{name}: expected schema_version 0.2 and a claims list")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    manifest_snapshots = manifest.get("product_snapshots", [])
    if not isinstance(manifest_snapshots, list):
        errors.append("manifest.product_snapshots must be a list")
        manifest_snapshots = []
    snapshot_by_offer: dict[str, dict[str, Any]] = {}
    for snapshot in manifest_snapshots:
        if not isinstance(snapshot, dict) or not snapshot.get("offer_id"):
            errors.append("Invalid product snapshot record")
            continue
        offer_id = snapshot["offer_id"]
        if offer_id in snapshot_by_offer:
            errors.append(f"Duplicate snapshot for {offer_id}")
        snapshot_by_offer[offer_id] = snapshot
        relative = snapshot.get("path")
        if not isinstance(relative, str):
            errors.append(f"No snapshot path for {offer_id}")
            continue
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"Snapshot path escapes study directory: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Snapshot missing: {relative}")
            continue
        try:
            offer = load(path).get("offer", {})
        except Exception as exc:
            errors.append(f"Invalid snapshot {relative}: {exc}")
            continue
        if offer.get("offer_id") != offer_id:
            errors.append(f"Snapshot offer mismatch: {offer_id}")
        if offer.get("profile_version") != snapshot.get("profile_version"):
            errors.append(f"Snapshot version mismatch: {offer_id}")
        expected_hash = snapshot.get("sha256")
        if not expected_hash or sha256(path) != expected_hash:
            errors.append(f"Snapshot checksum mismatch: {offer_id}")

    candidates = manifest.get("candidate_offers", [])
    if not isinstance(candidates, list) or set(candidates) != set(snapshot_by_offer):
        errors.append("candidate_offers and product_snapshots must contain the same offer IDs")
    elif len(candidates) != len(set(candidates)):
        errors.append("candidate_offers contains duplicate offer IDs")
    if fit.get("product_snapshots") != manifest_snapshots:
        errors.append("Fit matrix product snapshot metadata differs from manifest")

    matches = fit.get("matches", [])
    if not isinstance(matches, list):
        errors.append("fit.matches must be a list")
        matches = []
    for match in matches:
        if not isinstance(match, dict):
            errors.append("Invalid match record")
            continue
        validate_match(match, snapshot_by_offer, errors)

    top_decision = normalized_decision(fit.get("decision"))
    if top_decision is not None and top_decision not in DECISIONS:
        errors.append(f"Invalid top-level decision: {top_decision!r}")
    recommended = fit.get("recommended_offer_id")
    if recommended is not None and recommended not in snapshot_by_offer:
        errors.append("recommended_offer_id is not a candidate snapshot")
    selected = [match for match in matches if isinstance(match, dict) and match.get("offer_id") == recommended]
    if recommended:
        if len(selected) != 1:
            errors.append("recommended_offer_id must resolve to exactly one match record")
        elif top_decision != normalized_decision(selected[0].get("decision")):
            errors.append("Top-level decision must equal the recommended match decision")
    elif top_decision is not None:
        errors.append("A non-null top-level decision requires recommended_offer_id")

    stage = str(manifest.get("study_stage", "enterprise_research"))
    if not matches and stage in {"matching", "engagement", "complete"}:
        warnings.append("Study stage requires product matching, but no match is present")
    if not profile.get("evidence_claims") and stage not in {"enterprise_research", "initialized"}:
        warnings.append("Study stage requires an enterprise profile, but no evidence claims are present")
    if not isinstance(validation_log.get("events"), list):
        errors.append("Validation log events must be a list")

    for message in warnings:
        print("WARN:", message)
    for message in errors:
        print("ERROR:", message)
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
