from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core import ControlPlaneError, _read_yaml
from scripts.network_common import read_jsonl, stable_id, utc_now, write_jsonl

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

# Statuses a persisted nudge can carry. "hypothesis" is the only status a
# freshly generated nudge is ever given; "accepted"/"rejected" only ever
# come from a human decision recorded via accept_nudge()/reject_nudge()
# below. This module never promotes an accepted nudge's content into a
# canonical fact anywhere else in the pipeline (mirrors the epistemic-status
# boundary app/blockers.py's issue() and app/catalog_promotion.py keep
# explicit) -- accepting a nudge only changes this record's own status.
_DECISION_STATUSES = {"accepted", "rejected"}


@dataclass(frozen=True)
class UseCaseNudger:
    root: Path

    @classmethod
    def for_workspace(cls, workspace_id: str, repo_root: Path | None = None) -> "UseCaseNudger":
        """Instantiate against a specific workspace (ADR-007 §5 step 1)."""
        from app.workspace_paths import resolve_workspace_root

        return cls(resolve_workspace_root(workspace_id, repo_root))

    def _nudges_path(self, study_id: str) -> Path:
        safe = "".join(ch for ch in study_id if ch.isalnum() or ch in "-_.") or "unknown"
        return self.root / "studies" / safe / "06e_nudges.jsonl"

    def _load_nudges(self, study_id: str) -> list[dict[str, Any]]:
        return read_jsonl(self._nudges_path(study_id))

    def _save_nudges(self, study_id: str, records: list[dict[str, Any]]) -> None:
        write_jsonl(self._nudges_path(study_id), records, sort_key="nudge_id")

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

    def _productivization(self, study_id: str, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "nudge_id": stable_id("NUD", "productivization", study_id, uc_id),
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

    def _upsell(self, study_id: str, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                        "nudge_id": stable_id("NUD", "upsell_dependency", study_id, source_id, target_id),
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

    def _cross_sell(self, study_id: str, use_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "nudge_id": stable_id("NUD", "cross_sell_package", study_id, group, *ids),
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

    def _merge_persisted(self, study_id: str, fresh: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge freshly computed nudges into the persisted per-study store.

        Nudge IDs are content-derived (stable_id over study_id + mode + the
        identity fields of the nudge -- see the three `_*()` generators
        above), so re-running generation on unchanged input reproduces the
        same nudge_id instead of minting a new one. A nudge already decided
        (status "accepted"/"rejected") keeps its decision and decision
        metadata even if its narrative content (rationale/evidence/etc.) is
        recomputed here; only a nudge still at "hypothesis" is replaced by
        the freshly computed version. Nudges already persisted but not
        recomputed by this call (a different mode, or a use case that no
        longer produces this nudge) are kept as-is -- this never deletes a
        past human decision.
        """
        existing = {item["nudge_id"]: item for item in self._load_nudges(study_id) if item.get("nudge_id")}
        merged = dict(existing)
        for nudge in fresh:
            current = existing.get(nudge["nudge_id"])
            if current is not None and current.get("status") in _DECISION_STATUSES:
                continue  # a human decision on this exact nudge already exists; keep it
            merged[nudge["nudge_id"]] = dict(nudge)
        records = sorted(merged.values(), key=lambda item: str(item.get("nudge_id") or ""))
        self._save_nudges(study_id, records)
        return [merged[nudge["nudge_id"]] for nudge in fresh]

    def generate(self, study_id: str, mode: str = "all") -> dict[str, Any]:
        if mode not in _ALLOWED_MODES:
            raise ControlPlaneError(f"invalid nudging mode: {mode}")
        path = self._inventory_path(study_id)
        inventory = _read_yaml(path)
        use_cases = [item for item in inventory.get("use_cases", []) or [] if isinstance(item, dict)]
        nudges: list[dict[str, Any]] = []
        if mode in {"productivization", "all"}:
            nudges.extend(self._productivization(study_id, use_cases))
        if mode in {"upsell_dependency", "all"}:
            nudges.extend(self._upsell(study_id, use_cases))
        if mode in {"cross_sell_package", "all"}:
            nudges.extend(self._cross_sell(study_id, use_cases))
        # Persisted per-study (studies/<id>/06e_nudges.jsonl, stable_id-keyed --
        # see _merge_persisted()) so a nudge_id is a durable object a human can
        # accept/reject against, and re-generating the same underlying nudge
        # does not mint a new, unstable id (red-team-side-story S4).
        nudges = self._merge_persisted(study_id, nudges)
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

    def list_nudges(self, study_id: str) -> list[dict[str, Any]]:
        """All persisted nudges for a study, across every mode/decision."""
        study_id = str(study_id or "").strip()
        if not study_id:
            raise ControlPlaneError("study_id is required")
        return sorted(self._load_nudges(study_id), key=lambda item: str(item.get("nudge_id") or ""))

    def _decide(self, study_id: str, nudge_id: str, *, decision: str, actor: str, reason: str | None = None) -> dict[str, Any]:
        """Transition a persisted nudge's status hypothesis -> accepted/rejected.

        First decision wins: calling this again with the *same* decision on an
        already-decided nudge is a no-op that returns the existing record
        unchanged (matches mark_campaign_sent's/BlockerActionLog-adjacent
        idempotency convention); calling it with the *other* decision on an
        already-decided nudge is rejected, so a human's first call can never
        be silently overwritten by a second click.

        This only ever changes this nudge record's own status field -- it
        never writes the decision anywhere else in the pipeline (a nudge
        remains a hypothesis about future GTM motion, not a promoted fact;
        mirrors the epistemic-status boundary app/blockers.py's issue() and
        app/catalog_promotion.py keep explicit).
        """
        study_id = str(study_id or "").strip()
        nudge_id = str(nudge_id or "").strip()
        actor = str(actor or "").strip()
        reason = (reason or "").strip() or None
        if not study_id:
            raise ControlPlaneError("study_id is required")
        if not nudge_id:
            raise ControlPlaneError("nudge_id is required")
        if not actor:
            raise ControlPlaneError(f"actor is required to {decision.rstrip('ed')} a nudge")
        records = self._load_nudges(study_id)
        record = next((item for item in records if item.get("nudge_id") == nudge_id), None)
        if record is None:
            raise ControlPlaneError(f"unknown nudge_id: {nudge_id}")
        if record.get("status") == decision:
            return record
        if record.get("status") in _DECISION_STATUSES:
            raise ControlPlaneError(
                f"nudge {nudge_id} cannot be {decision} from status {record.get('status')!r} "
                "(a human decision already exists for this nudge)"
            )
        updated = dict(record)
        updated["status"] = decision
        updated["decided_by"] = actor
        updated["decided_at"] = utc_now()
        updated["decision_reason"] = reason
        self._save_nudges(study_id, [updated if item.get("nudge_id") == nudge_id else item for item in records])
        return updated

    def accept_nudge(self, study_id: str, nudge_id: str, *, actor: str) -> dict[str, Any]:
        return self._decide(study_id, nudge_id, decision="accepted", actor=actor)

    def reject_nudge(self, study_id: str, nudge_id: str, *, actor: str, reason: str | None = None) -> dict[str, Any]:
        return self._decide(study_id, nudge_id, decision="rejected", actor=actor, reason=reason)
