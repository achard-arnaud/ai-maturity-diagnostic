#!/usr/bin/env python3
"""Validate qualification-tunnel skills, contracts, catalog, templates, and evals."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency failure path
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[1]
TUNNEL_SKILLS = {
    "qualification-tunnel-router",
    "enterprise-demand-intelligence",
    "product-icp-intelligence",
    "opportunity-fit-matching",
    "engagement-pilot-design",
}
NETWORK_SKILLS = {
    "network-contact-intake",
    "enterprise-icb-mapping",
    "network-account-screening",
    "network-study-orchestration",
    "person-opportunity-targeting",
    "sector-intelligence-consolidation",
}
EXPECTED_SKILLS = TUNNEL_SKILLS | NETWORK_SKILLS
REQUIRED_CONTRACTS = {
    "account_screening.schema.yaml",
    "claim.schema.yaml",
    "company.schema.yaml",
    "contact_opportunity.schema.yaml",
    "enterprise_demand_profile.schema.yaml",
    "external_identity_mapping.schema.yaml",
    "icb_mapping.schema.yaml",
    "intake_batch.schema.yaml",
    "linkedin_connector_evidence.schema.yaml",
    "manual_validation_result.schema.yaml",
    "person.schema.yaml",
    "private_integration_audit.schema.yaml",
    "product_fit.schema.yaml",
    "product_profile.schema.yaml",
    "reach_hypothesis.schema.yaml",
    "relationship.schema.yaml",
    "relationship_observation.schema.yaml",
    "role_validation_request.schema.yaml",
    "sector_summary.schema.yaml",
    "study_queue.schema.yaml",
}
REQUIRED_TEMPLATES = {
    "study_manifest.yaml",
    "enterprise_demand_profile.yaml",
    "product_fit_matrix.yaml",
    "engagement_hypothesis.md",
}
REQUIRED_LINKEDIN_DESIGN = {
    "AGENTS.md",
    "artifacts/TODO_linkedin_plugin.yaml",
    "artifacts/linkedin_prd_traceability.yaml",
    "docs/ADR_linkedin_external_adapter.md",
    "docs/PRD_linkedin_qualification_plugin_v0_1.md",
    "docs/linkedin_capability_matrix.md",
    "docs/linkedin_connector_data_policy.md",
    "docs/linkedin_integration_architecture.md",
    "docs/linkedin_prd_traceability_matrix.md",
    "evals/linkedin_deferred_design_cases.yaml",
    "evals/linkedin_role_validation_eval_plan.yaml",
    "scripts/validate_linkedin_design.py",
}
REQUIRED_RELEASE_RESOURCES = {
    ".python-version",
    "pyproject.toml",
    ".gitlab-ci.yml",
    "data/network_release_manifest.yaml",
    "scripts/check_release.py",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def frontmatter(text: str) -> dict[str, Any]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data


def check_skills(errors: list[str], warnings: list[str]) -> None:
    names: set[str] = set()
    found_tunnel: set[str] = set()
    for skill_file in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        try:
            meta = frontmatter(text)
        except Exception as exc:
            errors.append(f"{skill_file.relative_to(ROOT)}: {exc}")
            continue

        unknown_meta = set(meta) - {"name", "description"}
        if unknown_meta:
            errors.append(f"{skill_file.relative_to(ROOT)}: unsupported frontmatter keys {sorted(unknown_meta)}")
        name = meta.get("name")
        description = meta.get("description")
        if not isinstance(name, str) or not name:
            errors.append(f"{skill_file.relative_to(ROOT)}: name is required")
            continue
        if name != skill_file.parent.name:
            errors.append(f"{name}: folder name does not match skill name")
        if not re.fullmatch(r"[a-z0-9-]{1,63}", name):
            errors.append(f"{name}: invalid skill name")
        if name in names:
            errors.append(f"Duplicate skill name: {name}")
        names.add(name)
        if name in EXPECTED_SKILLS:
            found_tunnel.add(name)
        if not isinstance(description, str) or len(description.strip()) < 80:
            warnings.append(f"{name}: description may be too weak for stable triggering")
        if len(text.splitlines()) > 500:
            warnings.append(f"{name}: SKILL.md exceeds 500 lines")
        if "TODO" in text or "[TODO" in text:
            errors.append(f"{name}: unresolved TODO placeholder")

        for rel in re.findall(r"\]\((references/[^)#]+)(?:#[^)]+)?\)", text):
            if not (skill_file.parent / rel).is_file():
                errors.append(f"{name}: missing referenced resource {rel}")

        agent_file = skill_file.parent / "agents" / "openai.yaml"
        if not agent_file.is_file():
            warnings.append(f"{name}: missing agents/openai.yaml")
        else:
            try:
                agent = load_yaml(agent_file)
                interface = agent.get("interface", {}) if isinstance(agent, dict) else {}
                for field in ("display_name", "short_description", "default_prompt"):
                    if not isinstance(interface.get(field), str) or not interface[field].strip():
                        errors.append(f"{name}: missing interface.{field}")
                prompt = interface.get("default_prompt", "")
                if f"${name}" not in prompt:
                    errors.append(f"{name}: default_prompt must mention ${name}")
            except Exception as exc:
                errors.append(f"{name}: invalid agents/openai.yaml: {exc}")

    missing = EXPECTED_SKILLS - found_tunnel
    if missing:
        errors.append(f"Missing qualification or network skills: {sorted(missing)}")

    enterprise_path = ROOT / "skills" / "enterprise-demand-intelligence" / "SKILL.md"
    if enterprise_path.is_file():
        enterprise = enterprise_path.read_text(encoding="utf-8").lower()
        if re.search(r"^\s*(recommended_offer|offer_score|astraforge_fit)\s*:", enterprise, flags=re.M):
            errors.append("Enterprise skill defines product-fit output fields")


def check_contracts_and_templates(errors: list[str]) -> None:
    contracts = ROOT / "contracts"
    templates = ROOT / "templates"
    for name in sorted(REQUIRED_CONTRACTS):
        path = contracts / name
        if not path.is_file():
            errors.append(f"Missing contract: {name}")
            continue
        try:
            data = load_yaml(path)
            if str(data.get("schema_version")) not in {"0.2", "0.3"}:
                errors.append(f"{name}: schema_version must be 0.2 or 0.3")
            if not data.get("required"):
                errors.append(f"{name}: required list is missing")
        except Exception as exc:
            errors.append(f"{name}: invalid YAML: {exc}")

    for name in sorted(REQUIRED_TEMPLATES):
        path = templates / name
        if not path.is_file():
            errors.append(f"Missing template: {name}")
        elif path.suffix == ".yaml":
            try:
                data = load_yaml(path)
                if not isinstance(data, dict):
                    errors.append(f"{name}: template must be a mapping")
            except Exception as exc:
                errors.append(f"{name}: invalid YAML: {exc}")


def check_catalog(errors: list[str], warnings: list[str]) -> None:
    index_path = ROOT / "product_catalog" / "index.yaml"
    try:
        catalog_index = load_yaml(index_path)
    except Exception as exc:
        errors.append(f"product_catalog/index.yaml: {exc}")
        return
    if catalog_index.get("schema_version") != "0.2":
        errors.append("Catalog schema_version must be 0.2")
    if not catalog_index.get("catalog_version"):
        errors.append("Catalog version is required")

    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for item in catalog_index.get("offers", []):
        if not isinstance(item, dict):
            errors.append("Catalog offer entry must be a mapping")
            continue
        offer_id = item.get("offer_id")
        filename = item.get("file")
        if not isinstance(offer_id, str) or not isinstance(filename, str):
            errors.append("Catalog entries require offer_id and file")
            continue
        if offer_id in seen_ids:
            errors.append(f"Duplicate offer_id: {offer_id}")
        if filename in seen_files:
            errors.append(f"Duplicate offer file: {filename}")
        seen_ids.add(offer_id)
        seen_files.add(filename)
        path = ROOT / "product_catalog" / filename
        if not path.is_file():
            errors.append(f"Missing offer file: {filename}")
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:
            errors.append(f"{filename}: invalid YAML: {exc}")
            continue
        offer = data.get("offer", {}) if isinstance(data, dict) else {}
        if data.get("schema_version") != "0.2":
            errors.append(f"{filename}: schema_version must be 0.2")
        if offer.get("offer_id") != offer_id:
            errors.append(f"Offer ID mismatch in {filename}")
        for field in ("profile_version", "positioning", "problem", "outcomes", "icp", "hard_gates", "proof"):
            if not offer.get(field):
                errors.append(f"{filename}: missing offer.{field}")
        gate_ids: set[str] = set()
        for gate in offer.get("hard_gates", []):
            if not isinstance(gate, dict) or not all(gate.get(x) for x in ("id", "test", "severity")):
                errors.append(f"{filename}: invalid hard gate")
                continue
            if gate["id"] in gate_ids:
                errors.append(f"{filename}: duplicate gate {gate['id']}")
            gate_ids.add(gate["id"])
            if gate["severity"] not in {"blocker", "critical"}:
                errors.append(f"{filename}: invalid gate severity {gate['severity']}")
        if offer.get("status") in {"draft", "reconstructed"} and not offer.get("unknowns"):
            warnings.append(f"{filename}: non-final offer has no explicit unknowns")

    if len(seen_ids) != 4:
        errors.append(f"Catalog must contain four independent offers, found {len(seen_ids)}")


def check_evals(errors: list[str]) -> None:
    eval_dir = ROOT / "evals"
    expected = {f"trigger_eval_{name}.json" for name in EXPECTED_SKILLS}
    actual = {path.name for path in eval_dir.glob("trigger_eval_*.json")}
    missing = expected - actual
    if missing:
        errors.append(f"Missing trigger evals: {sorted(missing)}")
    for eval_file in sorted(eval_dir.glob("trigger_eval_*.json")):
        try:
            items = json.loads(eval_file.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{eval_file.name}: invalid JSON: {exc}")
            continue
        if not isinstance(items, list):
            errors.append(f"{eval_file.name}: root must be a list")
            continue
        positives = sum(1 for item in items if item.get("should_trigger") is True)
        negatives = sum(1 for item in items if item.get("should_trigger") is False)
        queries = [item.get("query") for item in items]
        if len(items) != 20 or positives != 10 or negatives != 10:
            errors.append(f"{eval_file.name}: expected exactly 20 cases split 10/10")
        if any(not isinstance(query, str) or not query.strip() for query in queries):
            errors.append(f"{eval_file.name}: every query must be a non-empty string")
        if len(set(queries)) != len(queries):
            errors.append(f"{eval_file.name}: duplicate queries")

    reasoning_path = eval_dir / "reasoning_cases.yaml"
    try:
        reasoning = load_yaml(reasoning_path)
        cases = reasoning.get("cases", [])
        if reasoning.get("schema_version") != "0.2" or len(cases) < 9:
            errors.append("reasoning_cases.yaml: expected schema 0.2 and at least nine cases")
        case_ids = [case.get("id") for case in cases]
        if len(case_ids) != len(set(case_ids)):
            errors.append("reasoning_cases.yaml: duplicate case IDs")
    except Exception as exc:
        errors.append(f"reasoning_cases.yaml: {exc}")


def check_network_layer(errors: list[str]) -> None:
    for relative in (
        "data/taxonomies/icb_v5_2026.yaml",
        "data/taxonomies/company_icb_candidate_rules.yaml",
        "scripts/import_contacts.py",
        "scripts/migrate_person_identity_v0_3.py",
        "scripts/map_companies_icb.py",
        "scripts/screen_network_accounts.py",
        "scripts/sync_study_queue.py",
        "scripts/target_study_contacts.py",
        "scripts/build_reach_hypotheses.py",
        "scripts/build_sector_rollups.py",
        "scripts/validate_network.py",
    ):
        if not (ROOT / relative).is_file():
            errors.append(f"Missing network-layer resource: {relative}")
    try:
        taxonomy = load_yaml(ROOT / "data" / "taxonomies" / "icb_v5_2026.yaml")
        industries = taxonomy.get("industries", [])
        supersectors = [item for industry in industries for item in industry.get("supersectors", [])]
        sectors = [item for supersector in supersectors for item in supersector.get("sectors", [])]
        if (len(industries), len(supersectors), len(sectors)) != (11, 20, 45):
            errors.append(
                f"ICB structure must contain 11 industries, 20 supersectors, and 45 sectors; found {len(industries)}/{len(supersectors)}/{len(sectors)}"
            )
    except Exception as exc:
        errors.append(f"Invalid ICB taxonomy: {exc}")


def check_linkedin_design_resources(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_LINKEDIN_DESIGN):
        if not (ROOT / relative).is_file():
            errors.append(f"Missing deferred LinkedIn design resource: {relative}")

    forbidden_runtime_paths = (
        ROOT / "plugins" / "linkedin-qualification-adapter" / ".codex-plugin" / "plugin.json",
        ROOT / "skills" / "linkedin-capability-routing" / "SKILL.md",
        ROOT / "skills" / "linkedin-role-validation" / "SKILL.md",
    )
    for path in forbidden_runtime_paths:
        if path.exists():
            errors.append(f"Deferred LinkedIn runtime must not exist before gates pass: {path.relative_to(ROOT)}")


def check_release_resources(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_RELEASE_RESOURCES):
        if not (ROOT / relative).is_file():
            errors.append(f"Missing release resource: {relative}")
    if (ROOT / "skills" / "tech-leadership-org-intelligence" / "scripts" / "requirements.txt").exists():
        errors.append("Skill-local requirements.txt duplicates the root dependency configuration")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    check_skills(errors, warnings)
    check_contracts_and_templates(errors)
    check_catalog(errors, warnings)
    check_evals(errors)
    check_network_layer(errors)
    check_linkedin_design_resources(errors)
    check_release_resources(errors)

    for message in warnings:
        print("WARN:", message)
    for message in errors:
        print("ERROR:", message)
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
