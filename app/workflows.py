from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import ControlPlaneError
from app.demand import DemandCatalog
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit


@dataclass(frozen=True)
class WorkflowPlanner:
    root: Path

    def plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(payload.get("kind") or "").strip()
        if kind == "demand":
            return self._demand(str(payload.get("sector_code") or "").strip())
        if kind == "qualification":
            return self._qualification(str(payload.get("study_id") or "").strip())
        if kind == "nudging":
            return self._nudging(str(payload.get("study_id") or "").strip())
        raise ControlPlaneError("workflow kind must be demand, qualification or nudging")

    def _demand(self, sector_code: str) -> dict[str, Any]:
        if not sector_code:
            raise ControlPlaneError("sector_code is required for demand workflow")
        sector = next((row for row in DemandCatalog(self.root).snapshot()["sectors"] if row["sector_code"] == sector_code), None)
        if sector is None:
            raise ControlPlaneError(f"unknown ICB sector: {sector_code}")
        benchmark_status = "ready" if sector["benchmark_enabled"] else "blocked"
        return {
            "schema_version": "0.6",
            "kind": "demand",
            "target": sector_code,
            "label": sector["sector_name"],
            "steps": [
                {"id": "intake", "skill": "network-contact-intake", "status": "ready", "gate": "Private source/contact available"},
                {"id": "icb", "skill": "enterprise-icb-mapping", "status": "conditional", "gate": "Company created; classify from revenue evidence"},
                {"id": "screen", "skill": "network-account-screening", "status": "conditional", "gate": "ICB mapping does not prove demand"},
                {"id": "study", "skill": "network-study-orchestration", "status": "conditional", "gate": "Eligible account requires study create/refresh"},
                {"id": "demand", "skill": "enterprise-demand-intelligence", "status": "conditional", "gate": "Managed study exists"},
                {"id": "use_cases", "skill": "enterprise-use-case-intelligence", "status": "conditional", "gate": "Company evidence supports use-case extraction"},
                {"id": "benchmark", "skill": "sector-intelligence-consolidation", "status": benchmark_status, "gate": f"{sector['eligible_study_count']} / 3 eligible studies"},
            ],
            "current": {
                "eligible_studies": sector["eligible_study_count"],
                "use_cases": sector["use_case_count"],
                "benchmark_state": sector["benchmark_state"],
            },
        }

    def _qualification(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for qualification workflow")
        study = QualificationCockpit(self.root).study(study_id)
        if study is None:
            raise ControlPlaneError(f"unknown study: {study_id}")
        return {
            "schema_version": "0.6",
            "kind": "qualification",
            "target": study_id,
            "label": study["company"],
            "stage": study["stage"],
            "decision": study["decision"],
            "steps": study["steps"],
        }

    def _nudging(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for nudging workflow")
        inventories = UseCaseNudger(self.root).list_inventories()
        inventory = next((row for row in inventories if row["study_id"] == study_id), None)
        return {
            "schema_version": "0.6",
            "kind": "nudging",
            "target": study_id,
            "label": inventory["company"] if inventory else study_id,
            "steps": [
                {"id": "inventory", "skill": "enterprise-use-case-intelligence", "status": "completed" if inventory and inventory["use_case_count"] else "ready", "gate": "Product-blind company use-case inventory"},
                {"id": "nudge", "skill": "use-case-nudging", "status": "ready" if inventory and inventory["use_case_count"] else "blocked", "gate": "Use-case inventory only; no ICB or product-fit context"},
                {"id": "review", "skill": None, "status": "review", "gate": "Human review + falsifier before reuse"},
                {"id": "feedback", "skill": "enterprise-use-case-intelligence", "status": "conditional", "gate": "Record observed feedback/outcome before strengthening future nudges"},
            ],
        }
