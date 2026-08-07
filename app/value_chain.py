from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import ControlPlaneError, _read_yaml


@dataclass(frozen=True)
class ValueChainCatalog:
    root: Path

    def _study_dir(self, study_id: str) -> Path:
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            raise ControlPlaneError(f"unknown study: {study_id}")
        for manifest_path in studies_root.glob("*/00_manifest.yaml"):
            manifest = _read_yaml(manifest_path)
            if (manifest.get("study_id") or manifest_path.parent.name) == study_id:
                return manifest_path.parent
        raise ControlPlaneError(f"unknown study: {study_id}")

    def list_studies(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            return result
        for inventory_path in sorted(studies_root.glob("*/05b_use_case_inventory.yaml")):
            study_dir = inventory_path.parent
            inventory = _read_yaml(inventory_path)
            analysis_path = study_dir / "05c_value_chain_causal_map.yaml"
            analysis = _read_yaml(analysis_path) if analysis_path.is_file() else {}
            analysed_ids = {
                str(item.get("use_case_id"))
                for item in analysis.get("analyses", []) or []
                if isinstance(item, dict) and item.get("use_case_id")
            }
            use_cases = [item for item in inventory.get("use_cases", []) or [] if isinstance(item, dict)]
            result.append(
                {
                    "study_id": inventory.get("study_id") or study_dir.name,
                    "company": inventory.get("company") or study_dir.name,
                    "inventory_path": inventory_path.relative_to(self.root).as_posix(),
                    "analysis_path": analysis_path.relative_to(self.root).as_posix() if analysis_path.is_file() else None,
                    "use_case_count": len(use_cases),
                    "analysis_count": len(analysed_ids),
                    "pending_count": sum(1 for item in use_cases if str(item.get("use_case_id")) not in analysed_ids),
                }
            )
        return result

    def study(self, study_id: str) -> dict[str, Any]:
        study_dir = self._study_dir(study_id)
        inventory_path = study_dir / "05b_use_case_inventory.yaml"
        if not inventory_path.is_file():
            raise ControlPlaneError(f"study has no use-case inventory: {study_id}")
        inventory = _read_yaml(inventory_path)
        analysis_path = study_dir / "05c_value_chain_causal_map.yaml"
        doc = _read_yaml(analysis_path) if analysis_path.is_file() else {"analyses": []}
        analyses = {
            str(item.get("use_case_id")): item
            for item in doc.get("analyses", []) or []
            if isinstance(item, dict) and item.get("use_case_id")
        }
        use_cases: list[dict[str, Any]] = []
        for item in inventory.get("use_cases", []) or []:
            if not isinstance(item, dict) or not item.get("use_case_id"):
                continue
            uc_id = str(item["use_case_id"])
            use_cases.append(
                {
                    "use_case_id": uc_id,
                    "name": item.get("name") or item.get("workflow") or uc_id,
                    "line_of_business": item.get("line_of_business"),
                    "workflow": item.get("workflow"),
                    "outcome_family": item.get("outcome_family"),
                    "evidence_status": item.get("evidence_status"),
                    "confidence": item.get("confidence"),
                    "analysis_status": "completed" if uc_id in analyses else "pending",
                    "analysis": analyses.get(uc_id),
                }
            )
        return {
            "schema_version": "0.7",
            "study_id": study_id,
            "company": inventory.get("company") or study_dir.name,
            "inventory_path": inventory_path.relative_to(self.root).as_posix(),
            "analysis_path": analysis_path.relative_to(self.root).as_posix() if analysis_path.is_file() else None,
            "use_cases": use_cases,
        }

    def prepare_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        study_id = str(payload.get("study_id") or "").strip()
        use_case_id = str(payload.get("use_case_id") or "").strip()
        if not study_id or not use_case_id:
            raise ControlPlaneError("study_id and use_case_id are required")
        study = self.study(study_id)
        use_case = next((item for item in study["use_cases"] if item["use_case_id"] == use_case_id), None)
        if use_case is None:
            raise ControlPlaneError(f"unknown use case {use_case_id} in study {study_id}")
        context = [study["inventory_path"]]
        study_dir = self._study_dir(study_id)
        for name in (
            "01_strategy_evidence.yaml",
            "02_organization_evidence.yaml",
            "03_capability_signals.yaml",
            "04_newsflow_evidence.yaml",
            "05_enterprise_demand_profile.yaml",
        ):
            path = study_dir / name
            if path.is_file():
                context.append(path.relative_to(self.root).as_posix())
        if study["analysis_path"]:
            context.append(study["analysis_path"])
        return {
            "schema_version": "0.7",
            "status": "prepared",
            "skill": "enterprise-value-chain-causal-analysis",
            "input": (
                f"Analyse le use case {use_case_id} ({use_case['name']}) dans le study {study_id}. "
                "Décompose la chaîne opérationnelle avec une lecture Porter pragmatique et les causes Ishikawa, "
                "préserve les preuves et inconnues, et garde tout workflow adjacent au statut hypothèse tant qu'il n'est pas validé."
            ),
            "context_paths": context,
            "expected_artifact": f"{study_dir.relative_to(self.root).as_posix()}/05c_value_chain_causal_map.yaml",
            "automatic_use_case_promotion": False,
        }
