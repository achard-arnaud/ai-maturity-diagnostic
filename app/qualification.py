from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.blockers import attach_resolution, blocker, human_review_blocker
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

    @staticmethod
    def _reach_progression(reach: dict[str, Any]) -> tuple[bool, str | None]:
        if not reach:
            return False, None
        blockers = [item for item in reach.get("blockers", []) or [] if isinstance(item, dict) and item.get("severity") in {"blocker", "critical"}]
        if blockers:
            return False, str(blockers[0].get("message") or "Reach strategy has unresolved blockers.")
        ready_people = [item for item in reach.get("stakeholders", []) or [] if isinstance(item, dict) and item.get("status") == "ready"]
        if not ready_people:
            return False, "Reach strategy has no ready first-wave stakeholder."
        return True, None

    def list_studies(self) -> list[dict[str, Any]]:
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for manifest_path in sorted(studies_root.glob("*/00_manifest.yaml")):
            study_dir = manifest_path.parent
            study_rel = study_dir.relative_to(self.root).as_posix()
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
            contacts_doc = _read_yaml(contact_path) if contact_path.is_file() else {}
            contacts_artifact = contact_path.is_file()
            contacts_ready = bool(contacts_doc.get("targets")) and fit_progression_allowed

            reach_path = study_dir / "06c_reach_strategy.yaml"
            reach_doc = _read_yaml(reach_path) if reach_path.is_file() else {}
            reach_ready, reach_blocked_reason = self._reach_progression(reach_doc)
            reach_artifact = reach_path.is_file()

            engagement_path = study_dir / "07_engagement_hypothesis.md"
            engagement_ready = self._engagement_ready(engagement_path)
            decision = fit.get("decision")

            demand_blocker = blocker(
                category="demand",
                key=f"{manifest.get('study_id') or study_dir.name}:demand",
                message="Enterprise demand profile is missing or not sufficiently evidenced.",
                required_state="Evidence claims + capability gaps with medium/high confidence",
                owner_skill="enterprise-demand-intelligence",
                cta_label="Compléter la demande",
                cta_input=f"Complète le profil de demande product-blind du study {manifest.get('study_id') or study_dir.name}.",
                context_paths=[study_rel],
                postcondition="05_enterprise_demand_profile.yaml is decision-usable",
            )
            snapshot_blocker = blocker(
                category="product",
                key=f"{manifest.get('study_id') or study_dir.name}:snapshot",
                message="Matching requires at least one immutable product snapshot.",
                required_state="Versioned product snapshot in the study manifest",
                owner_skill="product-icp-intelligence",
                cta_label="Préparer les snapshots",
                cta_input="Valide la vérité produit nécessaire puis prépare les snapshots immuables sans ajouter de faits compte au catalogue.",
                context_paths=["product_catalog/index.yaml", study_rel],
                postcondition="study manifest references immutable candidate-offer snapshots",
            )
            matching_blocker = blocker(
                category="fit_gate",
                key=f"{manifest.get('study_id') or study_dir.name}:matching",
                message=fit_violation or "No completed product-fit decision exists.",
                required_state="Valid product-fit matrix with hard gates applied before score",
                owner_skill="opportunity-fit-matching",
                cta_label="Résoudre le matching",
                cta_input=f"Exécute ou répare le matching du study {manifest.get('study_id') or study_dir.name}; les hard gates priment sur le score.",
                context_paths=[study_rel],
                postcondition="06_product_fit_matrix.yaml contains a valid decision or explicit stop",
            )
            contacts_blocker = blocker(
                category="role",
                key=f"{manifest.get('study_id') or study_dir.name}:contacts",
                message="No usable company contact targets exist after the positive fit." if contacts_artifact else "Contact targeting has not been run after the positive fit.",
                required_state="At least one company-linked target with explicit role currency/validation needs",
                owner_skill="person-opportunity-targeting" if not contacts_artifact else "tech-leadership-org-intelligence",
                cta_label="Cibler les contacts" if not contacts_artifact else "Élargir le 2e tour",
                cta_input=(
                    f"Cible les contacts du study {manifest.get('study_id') or study_dir.name} après le fit sans inférer l'autorité depuis le titre."
                    if not contacts_artifact
                    else f"Complète l'organigramme et les rôles pertinents du study {manifest.get('study_id') or study_dir.name} pour élargir le second tour de contacts."
                ),
                context_paths=[study_rel],
                postcondition="06b_contact_targets.yaml contains evidence-bounded candidates",
            )
            reach_blocker = blocker(
                category="organization",
                key=f"{manifest.get('study_id') or study_dir.name}:reach",
                message=reach_blocked_reason or "Reach strategy has not been built from contacts, ICP, org and newsflow.",
                required_state="Reviewed first/second-wave stakeholder map with role-currentness and lane coverage",
                owner_skill="iterative-reach-matchmaking",
                cta_label="Construire / résoudre le reach",
                cta_input=f"Construis ou corrige la stratégie de reach du study {manifest.get('study_id') or study_dir.name} en first wave / second wave / validation-only.",
                context_paths=[study_rel],
                postcondition="06c_reach_strategy.yaml has at least one ready stakeholder and no unresolved blocking reach gate",
            )
            pilot_blocker = blocker(
                category="human_review",
                key=f"{manifest.get('study_id') or study_dir.name}:pilot",
                message="Engagement/pilot hypothesis is incomplete.",
                required_state="Falsifiable proof/discovery design with sponsor/terrain and measurable workflow",
                owner_skill="engagement-pilot-design",
                cta_label="Designer la preuve / pilote",
                cta_input=f"Transforme le fit et le reach validés du study {manifest.get('study_id') or study_dir.name} en preuve falsifiable.",
                context_paths=[study_rel],
                postcondition="07_engagement_hypothesis.md is complete and reviewable",
            )

            if not demand_ready:
                stage, next_skill, next_action, blocked_reason, current_blocker = "demand", "enterprise-demand-intelligence", "Refresh demand", demand_blocker["message"], demand_blocker
            elif not snapshots_ready:
                stage, next_skill, next_action, blocked_reason, current_blocker = "product_snapshot", "product-icp-intelligence", "Refresh offer truth / snapshots", snapshot_blocker["message"], snapshot_blocker
            elif not matching_ready or fit_violation:
                stage, next_skill, next_action, blocked_reason, current_blocker = "matching" if not fit_violation else "matching_invalid", "opportunity-fit-matching", "Run / repair matching", matching_blocker["message"], matching_blocker
            elif decision in {"nurture", "disqualify"}:
                stage, next_skill, next_action, blocked_reason = "stopped", None, "Review decision", f"Current matching decision is {decision}."
                current_blocker = human_review_blocker(
                    key=f"{manifest.get('study_id') or study_dir.name}:stopped:{decision}",
                    message=blocked_reason,
                    required_state="Human decision to keep stopped, refresh evidence or restart qualification",
                    cta_label="Revoir la décision",
                    postcondition="decision remains stopped or qualification is explicitly reopened",
                )
            elif not contacts_ready:
                stage, next_skill, next_action, blocked_reason, current_blocker = "contact_targeting", contacts_blocker["owner_skill"], contacts_blocker["cta_label"], contacts_blocker["message"], contacts_blocker
            elif not reach_artifact or not reach_ready:
                stage, next_skill, next_action, blocked_reason, current_blocker = "reach", "iterative-reach-matchmaking", "Build / resolve reach", reach_blocker["message"], reach_blocker
            elif not engagement_ready:
                stage, next_skill, next_action, blocked_reason, current_blocker = "pilot", "engagement-pilot-design", "Design proof / pilot", pilot_blocker["message"], pilot_blocker
            else:
                stage, next_skill, next_action, blocked_reason, current_blocker = "completed", None, "Review / refresh", None, None

            steps = [
                attach_resolution({"id": "demand", "skill": "enterprise-demand-intelligence", "status": "completed" if demand_ready else "blocked", "gate": "Evidence-backed product-blind demand"}, None if demand_ready else demand_blocker),
                attach_resolution({"id": "snapshots", "skill": "product-icp-intelligence", "status": "completed" if snapshots_ready else ("blocked" if demand_ready else "locked"), "gate": "Immutable versioned product snapshots"}, None if snapshots_ready or not demand_ready else snapshot_blocker),
                attach_resolution({"id": "matching", "skill": "opportunity-fit-matching", "status": "review" if fit_violation else ("completed" if matching_ready else ("blocked" if demand_ready and snapshots_ready else "locked")), "gate": "Hard gates before scoring"}, matching_blocker if (demand_ready and snapshots_ready and (not matching_ready or fit_violation)) else None),
                attach_resolution({"id": "contacts", "skill": "person-opportunity-targeting", "status": "completed" if contacts_ready else ("blocked" if fit_progression_allowed else "locked"), "gate": "Positive valid fit before person targeting"}, contacts_blocker if fit_progression_allowed and not contacts_ready else None),
                attach_resolution({"id": "reach", "skill": "iterative-reach-matchmaking", "status": "completed" if reach_ready else ("blocked" if contacts_ready else "locked"), "gate": "Stakeholder lanes, role currency, first/second wave"}, reach_blocker if contacts_ready and not reach_ready else None),
                attach_resolution({"id": "pilot", "skill": "engagement-pilot-design", "status": "completed" if engagement_ready and reach_ready else ("blocked" if reach_ready else "locked"), "gate": "Reach + measurable workflow before proof design"}, pilot_blocker if reach_ready and not engagement_ready else None),
            ]
            rows.append(
                {
                    "study_id": manifest.get("study_id") or study_dir.name,
                    "company": manifest.get("company") or profile.get("company") or study_dir.name,
                    "company_id": manifest.get("company_id"),
                    "study_path": study_rel,
                    "stage": stage,
                    "decision": decision,
                    "fit_violation": fit_violation,
                    "next_skill": next_skill,
                    "next_action": next_action,
                    "blocked_reason": blocked_reason,
                    "current_blocker": current_blocker,
                    "artifacts": {
                        "demand_ready": demand_ready,
                        "snapshots_ready": snapshots_ready,
                        "matching_ready": matching_ready,
                        "fit_progression_allowed": fit_progression_allowed,
                        "contacts_artifact": contacts_artifact,
                        "contacts_ready": contacts_ready,
                        "reach_artifact": reach_artifact,
                        "reach_ready": reach_ready,
                        "engagement_ready": engagement_ready,
                    },
                    "steps": steps,
                }
            )
        return rows

    def study(self, study_id: str) -> dict[str, Any] | None:
        return next((row for row in self.list_studies() if row["study_id"] == study_id), None)
