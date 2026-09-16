from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.blockers import blocker
from app.core import ControlPlaneError, _read_yaml
from app.qualification import QualificationCockpit
from scripts.network_common import utc_now


_TECH_PERSONAS = {"CIO", "CTO", "CDO", "CISO", "AI_Lead", "Architecture", "Head_of_Engineering", "Platform_Lead", "Product_Engineering_Lead"}
_PRESCRIBER_PERSONAS = {"CPO", "Transformation_Lead", "PMO_Director", "AI_Lead", "CDO", "Architecture", "Data_or_Security_Governance"}
_VETO_PERSONAS = {"CISO", "Data_or_Security_Governance"}


@dataclass(frozen=True)
class ReachMatchmaker:
    root: Path

    @classmethod
    def for_workspace(cls, workspace_id: str, repo_root: Path | None = None) -> "ReachMatchmaker":
        """Instantiate against a specific workspace (ADR-007 §5 step 1)."""
        from app.workspace_paths import resolve_workspace_root

        return cls(resolve_workspace_root(workspace_id, repo_root))

    def _study_dir(self, study_id: str) -> Path:
        studies = self.root / "studies"
        if not studies.is_dir():
            raise ControlPlaneError(f"unknown study: {study_id}")
        for manifest_path in studies.glob("*/00_manifest.yaml"):
            manifest = _read_yaml(manifest_path)
            if (manifest.get("study_id") or manifest_path.parent.name) == study_id:
                return manifest_path.parent
        raise ControlPlaneError(f"unknown study: {study_id}")

    @staticmethod
    def _claims(path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        doc = _read_yaml(path)
        return [item for item in doc.get("claims", []) or [] if isinstance(item, dict)]

    @staticmethod
    def _stakeholder_roles(target: dict[str, Any]) -> list[str]:
        roles = set(str(value) for value in target.get("role_hypotheses", []) or [])
        personas = set(str(value) for value in target.get("persona_matches", []) or [])
        result: set[str] = set()
        if "economic_sponsor" in roles:
            result.add("promoter")
        if "terrain_owner" in roles:
            result.add("terrain_user")
        if "technical_sponsor" in roles or personas & _TECH_PERSONAS:
            result.add("technical_sponsor")
        if "veto_player" in roles or personas & _VETO_PERSONAS:
            result.add("veto_control")
        if personas & _PRESCRIBER_PERSONAS or (roles and not result):
            result.add("prescriber")
        if not result and personas:
            result.add("prescriber")
        return sorted(result)

    @staticmethod
    def _target_score(target: dict[str, Any]) -> int:
        try:
            score = int(target.get("target_score") or 0)
        except (TypeError, ValueError):
            return 0
        return max(0, min(score, 100))

    @classmethod
    def _wave(cls, target: dict[str, Any], stakeholder_roles: list[str]) -> str:
        current = target.get("current_role_status") == "current"
        score = cls._target_score(target)
        if not current:
            return "validation_only"
        if score >= 60 and any(role in stakeholder_roles for role in ("promoter", "terrain_user", "prescriber", "technical_sponsor")):
            return "first"
        return "second"

    def list_ready(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for study in QualificationCockpit(self.root).list_studies():
            if study.get("decision") not in {"pursue", "validate"}:
                continue
            study_dir = self.root / str(study["study_path"])
            targets = _read_yaml(study_dir / "06b_contact_targets.yaml") if (study_dir / "06b_contact_targets.yaml").is_file() else {}
            reach_path = study_dir / "06c_reach_strategy.yaml"
            rows.append(
                {
                    "study_id": study["study_id"],
                    "company": study["company"],
                    "decision": study.get("decision"),
                    "target_count": len(targets.get("targets", []) or []),
                    "reach_artifact": reach_path.relative_to(self.root).as_posix() if reach_path.is_file() else None,
                    "status": "completed" if reach_path.is_file() else ("ready" if targets.get("targets") else "blocked"),
                }
            )
        return rows

    def preview(self, study_id: str) -> dict[str, Any]:
        study_dir = self._study_dir(study_id)
        manifest = _read_yaml(study_dir / "00_manifest.yaml")
        fit = _read_yaml(study_dir / "06_product_fit_matrix.yaml") if (study_dir / "06_product_fit_matrix.yaml").is_file() else {}
        decision = fit.get("decision")
        if decision not in {"pursue", "validate"}:
            raise ControlPlaneError("reach matchmaking requires PURSUE or VALIDATE fit")
        violation = QualificationCockpit._fit_violation(fit)
        if violation:
            raise ControlPlaneError(f"invalid selected fit: {violation}")
        offer_id = fit.get("recommended_offer_id")
        snapshot = next((item for item in manifest.get("product_snapshots", []) or [] if item.get("offer_id") == offer_id), None)
        if not snapshot:
            raise ControlPlaneError("selected product snapshot is missing")
        product = _read_yaml(study_dir / str(snapshot["path"])).get("offer", {})
        profile = _read_yaml(study_dir / "05_enterprise_demand_profile.yaml") if (study_dir / "05_enterprise_demand_profile.yaml").is_file() else {}
        targets_path = study_dir / "06b_contact_targets.yaml"
        targets_doc = _read_yaml(targets_path) if targets_path.is_file() else {}
        if targets_doc and (targets_doc.get("company_id") != manifest.get("company_id") or targets_doc.get("offer_id") != offer_id):
            raise ControlPlaneError("contact targets are stale or inconsistent with the selected opportunity")

        news_claims = self._claims(study_dir / "04_newsflow_evidence.yaml")
        newsflow_triggers = [
            {
                "claim_id": item.get("claim_id") or item.get("id"),
                "statement": item.get("statement") or item.get("title"),
                "epistemic_status": item.get("epistemic_status"),
            }
            for item in news_claims[:5]
            if item.get("statement") or item.get("title")
        ]
        why_now = newsflow_triggers[0]["statement"] if newsflow_triggers else None

        inventory_path = study_dir / "05b_use_case_inventory.yaml"
        inventory = _read_yaml(inventory_path) if inventory_path.is_file() else {}
        relevant_use_cases = [
            {
                "use_case_id": item.get("use_case_id"),
                "name": item.get("name") or item.get("workflow"),
                "line_of_business": item.get("line_of_business"),
                "outcome_family": item.get("outcome_family"),
                "evidence_status": item.get("evidence_status"),
            }
            for item in inventory.get("use_cases", []) or []
            if isinstance(item, dict) and item.get("use_case_id")
        ][:8]

        blockers: list[dict[str, Any]] = []
        stakeholders: list[dict[str, Any]] = []
        for target in targets_doc.get("targets", []) or []:
            if not isinstance(target, dict) or not target.get("person_id"):
                continue
            roles = self._stakeholder_roles(target)
            wave = self._wave(target, roles)
            validations = list(target.get("required_validations", []) or [])
            current = target.get("current_role_status") == "current"
            evidence_basis = [
                f"target_score={target.get('target_score')}",
                *[f"role_hypothesis:{value}" for value in target.get("role_hypotheses", []) or []],
                *[f"persona_match:{value}" for value in target.get("persona_matches", []) or []],
            ]
            if not current:
                role_blocker = blocker(
                    category="role",
                    key=f"{study_id}:{target['person_id']}:current-role",
                    message="Current role is not dated/validated; outreach cannot be marked ready.",
                    required_state="Dated current-role evidence or explicit human validation",
                    owner_skill="person-opportunity-targeting",
                    cta_label="Valider le rôle actuel",
                    cta_input=f"Valide le rôle actuel de {target['person_id']} pour le study {study_id} sans inférer l'autorité depuis le titre.",
                    context_paths=[targets_path.relative_to(self.root).as_posix()] if targets_path.is_file() else [],
                    postcondition="current_role_status becomes current or the target is rejected/stale",
                )
                blockers.append(role_blocker)
            stakeholders.append(
                {
                    "person_id": target["person_id"],
                    "target_id": target.get("target_id"),
                    "stakeholder_roles": roles,
                    "wave": wave,
                    "status": "blocked" if not current else ("ready" if wave == "first" else "validate"),
                    "why_person": "; ".join(evidence_basis[:4]) if evidence_basis else None,
                    "why_now": why_now,
                    "evidence_basis": evidence_basis,
                    "required_validations": validations,
                    "cta": {
                        "label": "Préparer la découverte" if current else "Valider le rôle actuel",
                        "owner_skill": "iterative-reach-matchmaking" if current else "person-opportunity-targeting",
                        "postcondition": "stakeholder lane and discovery objective reviewed" if current else "current role resolved",
                    },
                }
            )

        # TODO(red-team-spec): role-coverage blockers below are regenerated
        # fresh on every preview() call and are never persisted or
        # dismissable with a reason (unlike qualification's BlockerActionLog).
        # Revisit once a human repeatedly has to re-dismiss the same
        # missing-role blocker across multiple preview calls for one study.
        role_coverage = {role for item in stakeholders for role in item["stakeholder_roles"] if item["wave"] != "validation_only"}
        for role, label in (("promoter", "promoteur/sponsor"), ("prescriber", "prescripteur"), ("terrain_user", "utilisateur/terrain")):
            if role in role_coverage:
                continue
            blockers.append(
                blocker(
                    category="organization",
                    key=f"{study_id}:missing-{role}",
                    message=f"No current contact covers the {label} lane with sufficient evidence.",
                    required_state=f"At least one current candidate or explicit evidence that the {label} lane is not required",
                    owner_skill="tech-leadership-org-intelligence",
                    cta_label="Élargir le 2e tour",
                    cta_input=f"Complète la cartographie organisationnelle du study {study_id} pour identifier ou invalider le rôle {label}; préserve les niveaux de preuve et ne déduis pas l'autorité d'un titre.",
                    context_paths=[study_dir.relative_to(self.root).as_posix()],
                    postcondition=f"second-wave candidate/validation route exists for {role}",
                )
            )

        selected = QualificationCockpit._selected_match(fit) or {}
        for gate in selected.get("hard_gates", []) or []:
            if not isinstance(gate, dict) or gate.get("severity") not in {"blocker", "critical"}:
                continue
            if str(gate.get("status") or "").upper() != "OPEN":
                continue
            blockers.append(
                blocker(
                    category="fit_gate",
                    key=f"{study_id}:{gate.get('id')}:open",
                    message=f"Fit gate {gate.get('id') or 'unknown'} remains OPEN; reach can only support validation, not bypass the gate.",
                    required_state="Gate resolved to PASS or FAIL with evidence",
                    owner_skill="opportunity-fit-matching",
                    cta_label="Résoudre le gate",
                    cta_input=f"Résous le gate {gate.get('id')} du study {study_id} avec des preuves; ne change pas le score pour contourner le gate.",
                    context_paths=[(study_dir / "06_product_fit_matrix.yaml").relative_to(self.root).as_posix()],
                    postcondition="blocking/critical gate has an evidence-backed PASS or FAIL",
                    severity=str(gate.get("severity")),
                )
            )

        return {
            "schema_version": "0.7",
            "study_id": study_id,
            "company_id": manifest.get("company_id"),
            "company": manifest.get("company") or profile.get("company"),
            "offer_id": offer_id,
            "product_profile_version": selected.get("product_profile_version") or product.get("profile_version"),
            "fit_decision": decision,
            "icb_context": {"source": "company mapping/navigation only", "used_for_fit": False},
            "icp_personas": product.get("icp", {}).get("personas", {}),
            "newsflow_triggers": newsflow_triggers,
            "relevant_use_cases": relevant_use_cases,
            "stakeholders": sorted(stakeholders, key=lambda item: ({"first": 0, "second": 1, "validation_only": 2}[item["wave"]], item["person_id"])),
            "blockers": blockers,
            "boundaries": {"recomputes_fit": False, "sends_outbound": False, "title_proves_authority": False, "newsflow_changes_fit": False},
        }

    def write_strategy(self, study_id: str, preview: dict[str, Any] | None = None) -> dict[str, Any]:
        """Persist `06c_reach_strategy.yaml` for `study_id` from the
        already-computed preview() output -- every field written here is
        either something preview() actually derived from real evidence
        (fit decision, stakeholder waves/roles, blockers, newsflow/use-case
        excerpts) or an honest `None`; nothing here fabricates an
        evidence_status or hard-gate outcome that preview() did not compute.

        Re-running this (e.g. clicking "Préparer" again after new contact
        targets or fit data land) overwrites the previous artifact -- the
        skill-invocation text this same call still returns explicitly says
        "Construis ou rafraîchis" (build or refresh), and preview() itself
        is fully recomputed from source YAML on every call, so treating the
        written artifact as a refreshable projection of that same live state
        is consistent with the rest of this module, unlike
        catalog_promotion.promote_candidate's one-shot, never-overwrite
        semantics for a canonical catalog entry.
        """

        study_id = str(study_id or "").strip()
        if not study_id:
            raise ControlPlaneError("study_id is required")
        if preview is None:
            preview = self.preview(study_id)
        study_dir = self._study_dir(study_id)

        strategy: dict[str, Any] = {
            "schema_version": preview["schema_version"],
            "generated_at": utc_now(),
            "study_id": preview["study_id"],
            "company_id": preview["company_id"],
            "offer_id": preview["offer_id"],
            "product_profile_version": preview.get("product_profile_version"),
            "fit_decision": preview["fit_decision"],
            "icb_context": preview.get("icb_context", {}),
            "newsflow_triggers": preview.get("newsflow_triggers", []),
            "relevant_use_cases": preview.get("relevant_use_cases", []),
            "stakeholders": preview.get("stakeholders", []),
            "blockers": preview.get("blockers", []),
            "boundaries": preview.get("boundaries", {}),
        }

        strategy_path = study_dir / "06c_reach_strategy.yaml"
        strategy_path.parent.mkdir(parents=True, exist_ok=True)
        strategy_path.write_text(yaml.safe_dump(strategy, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return strategy

    def prepare_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Write `06c_reach_strategy.yaml` from the current preview() state
        and, in the same call, hand back a skill-invocation request an
        operator can still use to ask an agent to enrich/refresh it further
        (e.g. once new organization intelligence lands). The write is not a
        side effect of a read-only preview -- it only happens on this
        explicit "Préparer" action, mirroring how candidate promotion
        requires its own explicit click after viewing detail (see
        app/catalog_promotion.py's promote_candidate) rather than firing on
        every read.
        """

        study_id = str(payload.get("study_id") or "").strip()
        if not study_id:
            raise ControlPlaneError("study_id is required")
        preview = self.preview(study_id)
        strategy = self.write_strategy(study_id, preview=preview)
        study_dir = self._study_dir(study_id)
        context = []
        for name in (
            "00_manifest.yaml",
            "05_enterprise_demand_profile.yaml",
            "05b_use_case_inventory.yaml",
            "05c_value_chain_causal_map.yaml",
            "06_product_fit_matrix.yaml",
            "06b_contact_targets.yaml",
            "02_organization_evidence.yaml",
            "04_newsflow_evidence.yaml",
            "06c_reach_strategy.yaml",
        ):
            path = study_dir / name
            if path.is_file():
                context.append(path.relative_to(self.root).as_posix())
        artifact_path = f"{study_dir.relative_to(self.root).as_posix()}/06c_reach_strategy.yaml"
        return {
            "schema_version": "0.7",
            "status": "prepared",
            "written": True,
            "artifact_path": artifact_path,
            "strategy": strategy,
            "skill": "iterative-reach-matchmaking",
            "input": (
                f"Construis ou rafraîchis la stratégie de reach du study {study_id} après le fit {preview['fit_decision']} "
                "en distinguant promoteur, prescripteur, utilisateur/terrain, sponsor technique et veto; organise first wave, second wave et validation-only. "
                "Utilise le newsflow uniquement pour le why-now et ne déduis jamais l'autorité depuis un titre. "
                f"Un brouillon a déjà été écrit dans {artifact_path} à partir de preview(); affine-le sans inventer de statut de preuve."
            ),
            "context_paths": context,
            "expected_artifact": artifact_path,
        }
