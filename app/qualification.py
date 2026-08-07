from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import _read_yaml


@dataclass(frozen=True)
class QualificationCockpit:
    root: Path

    @staticmethod
    def _demand_ready(profile: dict[str, Any]) -> bool:
        return bool(profile.get("evidence_claims") and profile.get("capability_gaps")) and profile.get("confidence") in {"medium", "high"}

    @staticmethod
    def _engagement_ready(path: Path) -> bool:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8")
        return "Non établi" not in text and "Recommended offer: Non établi" not in text

    @staticmethod
    def _selected_match(fit: dict[str, Any]) -> dict[str, Any] | None:
        matches = [item for item in fit.get("matches", []) or [] if isinstance(item, dict)]
        recommended = fit.get("recommended_offer_id")
        if recommended:
            selected = next((item for item in matches if item.get("offer_id") == recommended), None)
            if selected is not None:
                return selected
        decision = fit.get("decision")
        selected = next((item for item in matches if item.get("decision") == decision), None)
        return selected or (matches[0] if len(matches) == 1 else None)

    @classmethod
    def _fit_violation(cls, fit: dict[str, Any]) -> str | None:
        decision = fit.get("decision")
        if decision not in {"pursue", "validate"}:
            return None
        selected = cls._selected_match(fit)
        if selected is None:
            return "No selected match can be reconciled with the top-level decision."
        if selected.get("decision") != decision:
            return "Top-level decision differs from the selected match decision."
        for gate in selected.get("hard_gates", []) or []:
            if not isinstance(gate, dict) or gate.get("severity") not in {"blocker", "critical"}:
                continue
            status = str(gate.get("status") or "").upper()
            if status == "FAIL":
                return f"Blocking gate {gate.get('id') or 'unknown'} is FAIL."
            if status == "OPEN" and decision == "pursue":
                return f"Blocking gate {gate.get('id') or 'unknown'} is OPEN; PURSUE is forbidden."
        return None

    def list_studies(self) -> list[dict[str, Any]]:
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for manifest_path in sorted(studies_root.glob("*/00_manifest.yaml")):
            study_dir = manifest_path.parent
            manifest = _read_yaml(manifest_path)
            demand_path = study_dir / "05_enterprise_demand_profile.yaml"
            profile = _read_yaml(demand_path) if demand_path.is_file() else {}
            fit_path = study_dir / "06_product_fit_matrix.yaml"
            fit = _read_yaml(fit_path) if fit_path.is_file() else {}
            snapshots = manifest.get("product_snapshots", []) or []
            demand_ready = self._demand_ready(profile)
            snapshots_ready = bool(snapshots)
            matching_ready = bool(fit.get("matches") and fit.get("decision"))
            fit_violation = self._fit_violation(fit) if matching_ready else None
            fit_progression_allowed = matching_ready and fit_violation is None and fit.get("decision") in {"pursue", "validate"}
            contact_path = study_dir / "06b_contact_targets.yaml"
            contacts_ready = contact_path.is_file()
            engagement_path = study_dir / "07_engagement_hypothesis.md"
            engagement_ready = self._engagement_ready(engagement_path)
            decision = fit.get("decision")

            if not demand_ready:
                stage = "demand"
                next_skill = "enterprise-demand-intelligence"
                next_action = "Refresh demand"
                blocked_reason = None
            elif not snapshots_ready:
                stage = "product_snapshot"
                next_skill = "product-icp-intelligence"
                next_action = "Refresh offer truth / snapshots"
                blocked_reason = "Matching requires immutable product snapshots."
            elif not matching_ready:
                stage = "matching"
                next_skill = "opportunity-fit-matching"
                next_action = "Run matching"
                blocked_reason = None
            elif fit_violation:
                stage = "matching_invalid"
                next_skill = "opportunity-fit-matching"
                next_action = "Repair matching"
                blocked_reason = fit_violation
            elif decision in {"nurture", "disqualify"}:
                stage = "stopped"
                next_skill = None
                next_action = "Review decision"
                blocked_reason = f"Current matching decision is {decision}."
            elif not contacts_ready:
                stage = "contact_targeting"
                next_skill = "person-opportunity-targeting"
                next_action = "Target contacts"
                blocked_reason = None
            elif not engagement_ready:
                stage = "pilot"
                next_skill = "engagement-pilot-design"
                next_action = "Design proof / pilot"
                blocked_reason = None
            else:
                stage = "completed"
                next_skill = None
                next_action = "Review / refresh"
                blocked_reason = None

            steps = [
                {"id": "demand", "skill": "enterprise-demand-intelligence", "status": "completed" if demand_ready else "ready"},
                {"id": "snapshots", "skill": "product-icp-intelligence", "status": "completed" if snapshots_ready else ("ready" if demand_ready else "blocked")},
                {"id": "matching", "skill": "opportunity-fit-matching", "status": "review" if fit_violation else ("completed" if matching_ready else ("ready" if demand_ready and snapshots_ready else "blocked"))},
                {"id": "contacts", "skill": "person-opportunity-targeting", "status": "completed" if contacts_ready and fit_progression_allowed else ("ready" if fit_progression_allowed else "blocked")},
                {"id": "pilot", "skill": "engagement-pilot-design", "status": "completed" if engagement_ready and fit_progression_allowed else ("ready" if fit_progression_allowed else "blocked")},
            ]
            rows.append(
                {
                    "study_id": manifest.get("study_id") or study_dir.name,
                    "company": manifest.get("company") or profile.get("company") or study_dir.name,
                    "company_id": manifest.get("company_id"),
                    "study_path": study_dir.relative_to(self.root).as_posix(),
                    "stage": stage,
                    "decision": decision,
                    "fit_violation": fit_violation,
                    "next_skill": next_skill,
                    "next_action": next_action,
                    "blocked_reason": blocked_reason,
                    "artifacts": {
                        "demand_ready": demand_ready,
                        "snapshots_ready": snapshots_ready,
                        "matching_ready": matching_ready,
                        "fit_progression_allowed": fit_progression_allowed,
                        "contacts_ready": contacts_ready,
                        "engagement_ready": engagement_ready,
                    },
                    "steps": steps,
                }
            )
        return rows

    def study(self, study_id: str) -> dict[str, Any] | None:
        return next((row for row in self.list_studies() if row["study_id"] == study_id), None)
