from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core import ControlPlaneError, _read_yaml

_ALLOWED_MODES = {"productivization", "upsell_dependency", "cross_sell_package", "all"}
_FORBIDDEN_REQUEST_FIELDS = {
    "icb",
    "sector_code",
    "sector_rollup",
    "enterprise_demand_profile",
    "product_fit",
    "offer_id",
    "product_catalog",
}


@dataclass(frozen=True)
class UseCaseNudger:
    root: Path

    def _inventory_path(self, study_id: str) -> Path:
        candidates = list((self.root / "studies").glob(f"*/05b_use_case_inventory.yaml")) if (self.root / "studies").is_dir() else []
        for path in candidates:
            doc = _read_yaml(path)
            if (doc.get("study_id") or path.parent.name) == study_id:
                return path
        raise ControlPlaneError(f"unknown use-case inventory study: {study_id}")

    def list_inventories(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            return result
        for path in sorted(studies_root.glob("*/05b_use_case_inventory.yaml")):
            doc = _read_yaml(path)
            result.append(
                {
                    "study_id": doc.get("study_id") or path.parent.name,
                    "company": doc.get("company") or path.parent.name,
                    "inventory_version": doc.get("inventory_version"),
                    "use_case_count": len(doc.get("use_cases", []) or []),
                    "path": path.relative_to(self.root).as_posix(),
                }
            )
        return result

    @staticmethod
    def _feedback(use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for use_case in use_cases:
            for item in use_case.get("feedback", []) or []:
                if isinstance(item, dict):
                    result.append({"use_case_id": use_case.get("use_case_id"), **item})
        return result

    def _productivization(self, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        nudges: list[dict[str, Any]] = []
        for use_case in use_cases:
            if use_case.get("maturity") == "retired":
                continue
            signals = []
            if use_case.get("repeatability") in {"medium", "high"}:
                signals.append(f"repeatability={use_case.get('repeatability')}")
            if use_case.get("variant_axes"):
                signals.append("variant axes already identified")
            if use_case.get("reusable_assets"):
                signals.append("reusable assets already identified")
            if not signals:
                continue
            uc_id = str(use_case.get("use_case_id"))
            nudges.append(
                {
                    "nudge_id": f"NUD-{uuid.uuid4().hex[:10]}",
                    "mode": "productivization",
                    "source_use_case_ids": [uc_id],
                    "target_use_case_ids": [uc_id],
                    "rationale": "Industrialize the existing use case because " + ", ".join(signals) + ".",
                    "evidence_feedback": self._feedback([use_case]),
                    "prerequisites": ["Confirm stable workflow and acceptance criteria before serializing variants."],
                    "unknowns": list(use_case.get("unknowns", []) or []),
                    "falsifier": "Stop if reuse/variant demand is not recurrent or marginal cost does not improve after standardization.",
                    "confidence": "medium" if use_case.get("confidence") in {"medium", "high"} else "low",
                    "status": "hypothesis",
                }
            )
        return nudges

    def _upsell(self, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id = {str(item.get("use_case_id")): item for item in use_cases if item.get("use_case_id")}
        nudges: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for source in use_cases:
            source_id = str(source.get("use_case_id") or "")
            dependencies = source.get("dependencies") or {}
            targets = list(dependencies.get("enables", []) or [])
            for candidate_id, candidate in by_id.items():
                candidate_deps = candidate.get("dependencies") or {}
                if source_id in (candidate_deps.get("depends_on", []) or []):
                    targets.append(candidate_id)
            for target_id in targets:
                target_id = str(target_id)
                if target_id not in by_id or target_id == source_id or (source_id, target_id) in seen:
                    continue
                seen.add((source_id, target_id))
                target = by_id[target_id]
                nudges.append(
                    {
                        "nudge_id": f"NUD-{uuid.uuid4().hex[:10]}",
                        "mode": "upsell_dependency",
                        "source_use_case_ids": [source_id],
                        "target_use_case_ids": [target_id],
                        "rationale": f"Explicit use-case graph links {source_id} to dependent/enabled use case {target_id}.",
                        "evidence_feedback": self._feedback([source, target]),
                        "prerequisites": ["Validate that the dependency edge still reflects the current workflow."],
                        "unknowns": list(target.get("unknowns", []) or []),
                        "falsifier": "Reject if the target use case can operate independently or the dependency no longer exists.",
                        "confidence": "medium" if source.get("confidence") in {"medium", "high"} and target.get("confidence") in {"medium", "high"} else "low",
                        "status": "hypothesis",
                    }
                )
        return nudges

    def _cross_sell(self, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for use_case in use_cases:
            # Cross-sell requires an explicit shared outcome family. A broad line-of-business
            # match is not enough to manufacture a package narrative.
            key = str(use_case.get("outcome_family") or "").strip()
            if not key:
                continue
            groups.setdefault(key, []).append(use_case)
        nudges: list[dict[str, Any]] = []
        for group, items in groups.items():
            active = [item for item in items if item.get("maturity") != "retired"]
            if len(active) < 2:
                continue
            ids = [str(item.get("use_case_id")) for item in active if item.get("use_case_id")]
            if len(ids) < 2:
                continue
            feedback = self._feedback(active)
            # The user-facing story must be levered by this company's recorded experience.
            # No feedback means no cross-sell hypothesis yet.
            if not feedback:
                continue
            nudges.append(
                {
                    "nudge_id": f"NUD-{uuid.uuid4().hex[:10]}",
                    "mode": "cross_sell_package",
                    "source_use_case_ids": ids,
                    "target_use_case_ids": ids,
                    "rationale": f"Package already-catalogued company use cases around shared outcome family '{group}', anchored in recorded company feedback.",
                    "evidence_feedback": feedback,
                    "prerequisites": ["Keep the package narrative anchored in the company’s recorded use-case evidence and feedback."],
                    "unknowns": [],
                    "falsifier": "Reject the package if the recorded experience does not support a coherent combined value story for this company.",
                    "confidence": "medium",
                    "status": "hypothesis",
                }
            )
        return nudges

    def generate(self, study_id: str, mode: str = "all") -> dict[str, Any]:
        if mode not in _ALLOWED_MODES:
            raise ControlPlaneError(f"invalid nudging mode: {mode}")
        path = self._inventory_path(study_id)
        inventory = _read_yaml(path)
        use_cases = [item for item in inventory.get("use_cases", []) or [] if isinstance(item, dict)]
        nudges: list[dict[str, Any]] = []
        if mode in {"productivization", "all"}:
            nudges.extend(self._productivization(use_cases))
        if mode in {"upsell_dependency", "all"}:
            nudges.extend(self._upsell(use_cases))
        if mode in {"cross_sell_package", "all"}:
            nudges.extend(self._cross_sell(use_cases))
        return {
            "schema_version": "0.6",
            "company": inventory.get("company"),
            "study_id": study_id,
            "inventory_version": inventory.get("inventory_version"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_boundary": {
                "use_case_inventory_only": True,
                "icb_loaded": False,
                "sector_rollup_loaded": False,
                "product_fit_loaded": False,
            },
            "mode": mode,
            "nudges": nudges,
        }

    def generate_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        forbidden = sorted(field for field in _FORBIDDEN_REQUEST_FIELDS if field in payload)
        if forbidden:
            raise ControlPlaneError("nudging request contains forbidden context: " + ", ".join(forbidden))
        study_id = str(payload.get("study_id") or "").strip()
        if not study_id:
            raise ControlPlaneError("study_id is required")
        mode = str(payload.get("mode") or "all").strip()
        return self.generate(study_id, mode)
