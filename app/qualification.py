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
                {"id": "matching", "skill": "opportunity-fit-matching", "status": "completed" if matching_ready else ("ready" if demand_ready and snapshots_ready else "blocked")},
                {"id": "contacts", "skill": "person-opportunity-targeting", "status": "completed" if contacts_ready else ("ready" if matching_ready and decision in {"pursue", "validate"} else "blocked")},
                {"id": "pilot", "skill": "engagement-pilot-design", "status": "completed" if engagement_ready else ("ready" if matching_ready and decision in {"pursue", "validate"} else "blocked")},
            ]
            rows.append(
                {
                    "study_id": manifest.get("study_id") or study_dir.name,
                    "company": manifest.get("company") or profile.get("company") or study_dir.name,
                    "company_id": manifest.get("company_id"),
                    "study_path": study_dir.relative_to(self.root).as_posix(),
                    "stage": stage,
                    "decision": decision,
                    "next_skill": next_skill,
                    "next_action": next_action,
                    "blocked_reason": blocked_reason,
                    "artifacts": {
                        "demand_ready": demand_ready,
                        "snapshots_ready": snapshots_ready,
                        "matching_ready": matching_ready,
                        "contacts_ready": contacts_ready,
                        "engagement_ready": engagement_ready,
                    },
                    "steps": steps,
                }
            )
        return rows

    def study(self, study_id: str) -> dict[str, Any] | None:
        return next((row for row in self.list_studies() if row["study_id"] == study_id), None)
