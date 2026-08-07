#!/usr/bin/env python3
"""Validate the deferred LinkedIn design without implying runtime readiness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REQUIREMENTS = {f"LI-FR-{index:03d}" for index in range(1, 16)}
EXPECTED_GATES = {f"LI-G{index}" for index in range(7)}


def load_yaml(relative: str) -> Any:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


def nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        trace = load_yaml("artifacts/linkedin_prd_traceability.yaml")
        items = trace.get("items", [])
        ids = [item.get("id") for item in items]
        if set(ids) != EXPECTED_REQUIREMENTS or len(ids) != len(set(ids)):
            errors.append("Traceability must contain each LI-FR-001..015 exactly once")
        if trace.get("status") != "deferred" or nested(trace, "policy", "runtime_status") != "not_implemented":
            errors.append("Traceability must preserve deferred/not_implemented runtime status")
        for item in items:
            for field in ("requirement", "component", "contract_or_artifact", "verification", "verification_stage"):
                if not item.get(field):
                    errors.append(f"{item.get('id')}: missing {field}")
    except Exception as exc:
        errors.append(f"Invalid traceability artifact: {exc}")

    try:
        backlog = load_yaml("artifacts/TODO_linkedin_plugin.yaml")
        backlog_items = backlog.get("items", [])
        gates = {item.get("gate") for item in backlog_items}
        if backlog.get("status") != "deferred":
            errors.append("LinkedIn backlog must remain deferred")
        if not EXPECTED_GATES.issubset(gates):
            errors.append(f"LinkedIn backlog does not cover all gates: {sorted(EXPECTED_GATES - gates)}")
        if any(item.get("status") != "todo_later" for item in backlog_items):
            errors.append("No LinkedIn backlog item may be active before the gates are approved")
    except Exception as exc:
        errors.append(f"Invalid LinkedIn backlog: {exc}")

    try:
        evidence = load_yaml("contracts/linkedin_connector_evidence.schema.yaml")
        required = set(evidence.get("required", []))
        expected = {
            "connector_evidence_id",
            "request_id",
            "provider",
            "capability",
            "acquisition_method",
            "authorization_program",
            "retrieved_at",
            "canonical_entity_candidate",
            "match_status",
            "confidence",
            "limitations",
            "policy",
        }
        if not expected.issubset(required):
            errors.append("Connector evidence is missing required provenance or identity fields")
        if nested(evidence, "properties", "provider", "const") != "linkedin":
            errors.append("Connector evidence provider must be linkedin")
        if nested(evidence, "properties", "policy", "properties", "action_class", "const") != "read":
            errors.append("LinkedIn connector action_class must be read")
        storage = set(nested(evidence, "properties", "policy", "properties", "storage_permission", "enum") or [])
        if "unknown" not in storage or "transient_only" not in storage:
            errors.append("Connector evidence must model unknown and transient storage")
        policy_all_of = nested(evidence, "properties", "policy", "allOf") or []
        serialized_conditions = yaml.safe_dump(policy_all_of)
        if "allowed_with_retention" not in serialized_conditions or "retention_until" not in serialized_conditions:
            errors.append("allowed_with_retention must require a retention_until timestamp")
    except Exception as exc:
        errors.append(f"Invalid connector evidence contract: {exc}")

    try:
        request = load_yaml("contracts/role_validation_request.schema.yaml")
        if nested(request, "properties", "purpose", "const") != "current_role_validation":
            errors.append("Role validation request purpose is not constrained")
        if not {"request_id", "person_id", "purpose", "requested_at"}.issubset(set(request.get("required", []))):
            errors.append("Role validation request lacks canonical request fields")
    except Exception as exc:
        errors.append(f"Invalid role validation request contract: {exc}")

    try:
        audit = load_yaml("contracts/private_integration_audit.schema.yaml")
        if nested(audit, "properties", "action_class", "const") != "read":
            errors.append("Private integration audit must constrain action_class to read")
        for field in ("provider", "request_id", "capability", "occurred_at", "result_class", "policy_version"):
            if field not in set(audit.get("required", [])):
                errors.append(f"Private integration audit is missing {field}")
    except Exception as exc:
        errors.append(f"Invalid integration audit contract: {exc}")

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for policy_id in (f"LI-POL-{index:03d}" for index in range(1, 9)):
        if policy_id not in agents:
            errors.append(f"AGENTS.md is missing {policy_id}")

    deferred_runtime_paths = (
        ROOT / "plugins" / "linkedin-qualification-adapter" / ".codex-plugin" / "plugin.json",
        ROOT / "skills" / "linkedin-capability-routing" / "SKILL.md",
        ROOT / "skills" / "linkedin-role-validation" / "SKILL.md",
        ROOT / ".mcp.json",
    )
    for path in deferred_runtime_paths:
        if path.exists():
            errors.append(f"Deferred runtime artifact exists before gates pass: {path.relative_to(ROOT)}")

    eval_plan = load_yaml("evals/linkedin_role_validation_eval_plan.yaml")
    if eval_plan.get("status") != "deferred" or int(eval_plan.get("minimum_sample_size", 0)) < 30:
        errors.append("LinkedIn evaluation must remain deferred with a sample of at least 30")

    for message in warnings:
        print("WARN:", message)
    for message in errors:
        print("ERROR:", message)
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
