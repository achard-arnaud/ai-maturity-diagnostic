from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from app.core import ControlPlaneError, _read_yaml


def _stable(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts)
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12].upper()}"


def _strings(values: Any) -> set[str]:
    result: set[str] = set()
    for item in values or []:
        if isinstance(item, str) and item.strip():
            result.add(item.strip().lower())
        elif isinstance(item, dict):
            text = item.get("label") or item.get("statement") or item.get("cause") or item.get("name")
            if text:
                result.add(str(text).strip().lower())
    return result


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


@dataclass(frozen=True)
class UseCaseGraph:
    root: Path

    @staticmethod
    def _edge(source: str, target: str, relation: str, *, scope: str, basis: str, confidence: str, evidence_refs: list[str] | None = None) -> dict[str, Any]:
        return {
            "edge_id": _stable("EDGE", source, target, relation, scope, basis),
            "source": source,
            "target": target,
            "relation": relation,
            "scope": scope,
            "basis": basis,
            "confidence": confidence,
            "evidence_refs": list(evidence_refs or []),
            "demand_proof": False,
        }

    def _study_inventory(self, study_id: str) -> tuple[Path, dict[str, Any]]:
        studies = self.root / "studies"
        if not studies.is_dir():
            raise ControlPlaneError(f"unknown study: {study_id}")
        for path in studies.glob("*/05b_use_case_inventory.yaml"):
            doc = _read_yaml(path)
            if (doc.get("study_id") or path.parent.name) == study_id:
                return path, doc
        raise ControlPlaneError(f"unknown use-case inventory study: {study_id}")

    def company(self, study_id: str) -> dict[str, Any]:
        inventory_path, inventory = self._study_inventory(study_id)
        company = str(inventory.get("company") or inventory_path.parent.name)
        use_cases = [item for item in inventory.get("use_cases", []) or [] if isinstance(item, dict) and item.get("use_case_id")]
        by_id = {str(item["use_case_id"]): item for item in use_cases}
        nodes = [
            {
                "node_id": f"UC:{uc_id}",
                "node_type": "use_case",
                "label": item.get("name") or item.get("workflow") or uc_id,
                "company": company,
                "study_id": study_id,
                "use_case_id": uc_id,
                "line_of_business": item.get("line_of_business"),
                "workflow": item.get("workflow"),
                "outcome_family": item.get("outcome_family"),
                "maturity": item.get("maturity"),
                "provenance": {"path": inventory_path.relative_to(self.root).as_posix(), "evidence_status": item.get("evidence_status")},
            }
            for uc_id, item in sorted(by_id.items())
        ]
        edges: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        def add(source: str, target: str, relation: str, basis: str, confidence: str = "medium", evidence_refs: list[str] | None = None) -> None:
            if source not in by_id or target not in by_id or source == target:
                return
            key = (source, target, relation)
            if key in seen:
                return
            seen.add(key)
            edges.append(self._edge(f"UC:{source}", f"UC:{target}", relation, scope="same_company", basis=basis, confidence=confidence, evidence_refs=evidence_refs))

        for uc_id, item in by_id.items():
            dependencies = item.get("dependencies") or {}
            for target in dependencies.get("depends_on", []) or []:
                add(uc_id, str(target), "depends_on", "explicit use-case dependency", "high")
            for target in dependencies.get("enables", []) or []:
                add(uc_id, str(target), "enables", "explicit use-case enabler", "high")
            for target in item.get("variant_of", []) or []:
                add(uc_id, str(target), "variant_of", "explicit variant relation", "high")

        for left_id, right_id in combinations(sorted(by_id), 2):
            left, right = by_id[left_id], by_id[right_id]
            shared_assets = _strings(left.get("reusable_assets")) & _strings(right.get("reusable_assets"))
            if shared_assets:
                basis = "shared reusable assets: " + ", ".join(sorted(shared_assets))
                add(left_id, right_id, "shares_asset", basis)
                add(right_id, left_id, "shares_asset", basis)
            left_outcome = str(left.get("outcome_family") or "").strip().lower()
            right_outcome = str(right.get("outcome_family") or "").strip().lower()
            if left_outcome and left_outcome == right_outcome:
                basis = f"same outcome family: {left_outcome}"
                add(left_id, right_id, "same_outcome", basis)
                add(right_id, left_id, "same_outcome", basis)

        analysis_path = inventory_path.parent / "05c_value_chain_causal_map.yaml"
        analysis = _read_yaml(analysis_path) if analysis_path.is_file() else {}
        cause_sets: dict[str, set[str]] = {}
        for row in analysis.get("analyses", []) or []:
            if not isinstance(row, dict) or str(row.get("use_case_id")) not in by_id:
                continue
            source_id = str(row["use_case_id"])
            refs = [str(x) for x in row.get("evidence_refs", []) or []]
            for hypothesis in row.get("adjacent_workflow_hypotheses", []) or []:
                if not isinstance(hypothesis, dict):
                    continue
                candidate = str(hypothesis.get("candidate_use_case_id") or "").strip()
                if candidate in by_id:
                    add(source_id, candidate, "value_chain_neighbor", str(hypothesis.get("basis") or "value-chain adjacency"), "medium", refs)
                else:
                    label = str(hypothesis.get("label") or "").strip()
                    if not label:
                        continue
                    node_id = _stable("HYP", study_id, source_id, label)
                    if not any(node["node_id"] == node_id for node in nodes):
                        nodes.append({
                            "node_id": node_id,
                            "node_type": "workflow_hypothesis",
                            "label": label,
                            "company": company,
                            "study_id": study_id,
                            "use_case_id": None,
                            "provenance": {"path": analysis_path.relative_to(self.root).as_posix(), "status": "hypothesis"},
                        })
                    edges.append(self._edge(f"UC:{source_id}", node_id, "value_chain_neighbor", scope="same_company", basis=str(hypothesis.get("basis") or "value-chain adjacency hypothesis"), confidence="low", evidence_refs=refs))
            causes: set[str] = set()
            ishikawa = row.get("ishikawa") or {}
            for branch in ("people", "process", "technology", "data", "governance_control", "environment_external"):
                causes |= _strings(ishikawa.get(branch))
            cause_sets[source_id] = causes

        for left_id, right_id in combinations(sorted(cause_sets), 2):
            shared = cause_sets[left_id] & cause_sets[right_id]
            if shared:
                basis = "shared causal constraints: " + ", ".join(sorted(shared)[:5])
                add(left_id, right_id, "causal_neighbor", basis, "medium")
                add(right_id, left_id, "causal_neighbor", basis, "medium")

        return {
            "schema_version": "0.7",
            "scope": {"kind": "company", "study_id": study_id, "company": company, "sector_code": None},
            "nodes": nodes,
            "edges": edges,
            "persistence": "derived_on_read",
        }

    def sector(self, sector_code: str) -> dict[str, Any]:
        sector_code = str(sector_code).strip()
        if not sector_code:
            raise ControlPlaneError("sector_code is required")
        mappings = {
            str(item.get("company_id")): item
            for item in _read_jsonl(self.root / "data" / "private" / "network" / "company_icb_mappings.jsonl")
            if item.get("company_id")
        }
        studies_root = self.root / "studies"
        nodes: list[dict[str, Any]] = []
        records: list[dict[str, Any]] = []
        if studies_root.is_dir():
            for inventory_path in studies_root.glob("*/05b_use_case_inventory.yaml"):
                inventory = _read_yaml(inventory_path)
                company_id = str(inventory.get("company_id") or "")
                mapping = mappings.get(company_id) or {}
                sector = mapping.get("sector") or {}
                if str(sector.get("code") or "") != sector_code:
                    continue
                study_id = str(inventory.get("study_id") or inventory_path.parent.name)
                company = str(inventory.get("company") or company_id or inventory_path.parent.name)
                for item in inventory.get("use_cases", []) or []:
                    if not isinstance(item, dict) or not item.get("use_case_id"):
                        continue
                    uc_id = str(item["use_case_id"])
                    node_id = f"{study_id}:UC:{uc_id}"
                    record = {"node_id": node_id, "study_id": study_id, "company": company, "company_id": company_id, "use_case": item, "path": inventory_path}
                    records.append(record)
                    nodes.append({
                        "node_id": node_id,
                        "node_type": "use_case",
                        "label": item.get("name") or item.get("workflow") or uc_id,
                        "company": company,
                        "study_id": study_id,
                        "use_case_id": uc_id,
                        "outcome_family": item.get("outcome_family"),
                        "line_of_business": item.get("line_of_business"),
                        "provenance": {"path": inventory_path.relative_to(self.root).as_posix(), "mapping_status": mapping.get("mapping_status")},
                    })
        if not records:
            return {"schema_version": "0.7", "scope": {"kind": "sector", "study_id": None, "company": None, "sector_code": sector_code}, "nodes": [], "edges": [], "persistence": "derived_on_read"}
        edges: list[dict[str, Any]] = []
        for left, right in combinations(records, 2):
            if left["company_id"] == right["company_id"]:
                continue
            left_outcome = str(left["use_case"].get("outcome_family") or "").strip().lower()
            right_outcome = str(right["use_case"].get("outcome_family") or "").strip().lower()
            if left_outcome and left_outcome == right_outcome:
                edges.append(self._edge(left["node_id"], right["node_id"], "similar_pattern", scope="sector", basis=f"cross-company same outcome family: {left_outcome}", confidence="low"))
        return {
            "schema_version": "0.7",
            "scope": {"kind": "sector", "study_id": None, "company": None, "sector_code": sector_code},
            "nodes": nodes,
            "edges": edges,
            "persistence": "derived_on_read",
            "warning": "Cross-company graph edges are hypotheses and never prove company demand.",
        }
