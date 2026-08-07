from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.blockers import attach_resolution, blocker, human_review_blocker
from app.core import ControlPlaneError, _read_yaml
from app.demand import DemandCatalog
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit
from app.reach import ReachMatchmaker
from app.value_chain import ValueChainCatalog


@dataclass(frozen=True)
class WorkflowPlanner:
    root: Path

    def plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(payload.get("kind") or "").strip()
        if kind == "demand":
            return self._demand(str(payload.get("sector_code") or "").strip())
        if kind == "company":
            return self._company(str(payload.get("study_id") or "").strip())
        if kind == "offer":
            return self._offer(str(payload.get("offer_id") or "").strip())
        if kind == "qualification":
            return self._qualification(str(payload.get("study_id") or "").strip())
        if kind == "reach":
            return self._reach(str(payload.get("study_id") or "").strip())
        if kind == "value_chain":
            return self._value_chain(str(payload.get("study_id") or "").strip(), str(payload.get("use_case_id") or "").strip())
        if kind == "nudging":
            return self._nudging(str(payload.get("study_id") or "").strip())
        raise ControlPlaneError("workflow kind must be demand, company, offer, qualification, reach, value_chain or nudging")

    def _demand(self, sector_code: str) -> dict[str, Any]:
        if not sector_code:
            raise ControlPlaneError("sector_code is required for demand workflow")
        sector = next((row for row in DemandCatalog(self.root).snapshot()["sectors"] if row["sector_code"] == sector_code), None)
        if sector is None:
            raise ControlPlaneError(f"unknown ICB sector: {sector_code}")
        if sector["benchmark_enabled"]:
            benchmark_status, benchmark_resolution = "ready", None
        else:
            benchmark_status = "blocked"
            if sector["eligible_study_count"] == 2:
                benchmark_resolution = blocker(
                    category="sector",
                    key=f"{sector_code}:third-company",
                    message="Sector benchmark needs a third current complete company study.",
                    required_state="At least 3 current complete studies in the same defensible ICB sector",
                    owner_skill="network-contact-intake",
                    cta_label="Ajouter une 3e entreprise",
                    cta_input=f"Ajoute une nouvelle source de contact/entreprise pour développer le secteur ICB {sector_code}; ne présume pas de la classification ou de la demande.",
                    postcondition="new company can enter ICB mapping/screening/study workflow",
                )
            else:
                benchmark_resolution = blocker(
                    category="sector",
                    key=f"{sector_code}:benchmark-coverage",
                    message=f"Only {sector['eligible_study_count']} / 3 eligible studies are available.",
                    required_state="At least 3 current complete studies in the sector",
                    owner_skill="network-study-orchestration",
                    cta_label="Compléter la couverture",
                    cta_input=f"Identifie les études à créer/rafraîchir pour le secteur ICB {sector_code}; le secteur ne prouve jamais la demande d'un compte.",
                    postcondition="study queue exposes the next company studies needed for benchmark readiness",
                )
        return {
            "schema_version": "0.7",
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
                {"id": "value_chain", "skill": "enterprise-value-chain-causal-analysis", "status": "conditional", "gate": "Known UC exists; Porter/Ishikawa remains analytical"},
                attach_resolution({"id": "benchmark", "skill": "sector-intelligence-consolidation", "status": benchmark_status, "gate": f"{sector['eligible_study_count']} / 3 eligible studies"}, benchmark_resolution),
            ],
            "current": {
                "eligible_studies": sector["eligible_study_count"],
                "use_cases": sector["use_case_count"],
                "benchmark_state": sector["benchmark_state"],
            },
        }

    def _company(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for company workflow")
        qualification = QualificationCockpit(self.root).study(study_id)
        if qualification is None:
            raise ControlPlaneError(f"unknown study: {study_id}")
        value_study = None
        try:
            value_study = ValueChainCatalog(self.root).study(study_id)
        except ControlPlaneError:
            value_study = None
        uc_count = len(value_study["use_cases"]) if value_study else 0
        analysed = sum(1 for row in value_study["use_cases"] if row["analysis_status"] == "completed") if value_study else 0
        inventory_blocker = blocker(
            category="use_case",
            key=f"{study_id}:inventory",
            message="No product-blind company use-case inventory is available.",
            required_state="Evidence-backed 05b_use_case_inventory.yaml",
            owner_skill="enterprise-use-case-intelligence",
            cta_label="Récolter les use cases",
            cta_input=f"Construis l'inventaire use cases du study {study_id} depuis les preuves entreprise sans charger les offres.",
            context_paths=[qualification["study_path"]],
            postcondition="05b_use_case_inventory.yaml exists with canonical UC IDs",
        )
        value_blocker = blocker(
            category="value_chain",
            key=f"{study_id}:value-chain",
            message="One or more canonical use cases have no Porter/Ishikawa analysis yet.",
            required_state="05c contains evidence-bounded analysis for selected relevant UCs",
            owner_skill="enterprise-value-chain-causal-analysis",
            cta_label="Analyser la chaîne de valeur",
            cta_input=f"Analyse les UC prioritaires du study {study_id} via Porter/Ishikawa sans promouvoir automatiquement les workflows adjacents.",
            context_paths=[qualification["study_path"]],
            postcondition="selected UCs have 05c analyses and validation questions",
        )
        return {
            "schema_version": "0.7",
            "kind": "company",
            "target": study_id,
            "label": qualification["company"],
            "steps": [
                {"id": "demand", "skill": "enterprise-demand-intelligence", "status": "completed" if qualification["artifacts"]["demand_ready"] else "blocked", "gate": "Product-blind enterprise demand"},
                {"id": "organization", "skill": "tech-leadership-org-intelligence", "status": "conditional", "gate": "Org/decision evidence supports later stakeholder validation"},
                attach_resolution({"id": "use_cases", "skill": "enterprise-use-case-intelligence", "status": "completed" if uc_count else "blocked", "gate": "Canonical product-blind use-case inventory"}, None if uc_count else inventory_blocker),
                attach_resolution({"id": "value_chain", "skill": "enterprise-value-chain-causal-analysis", "status": "completed" if uc_count and analysed == uc_count else ("blocked" if uc_count else "locked"), "gate": f"{analysed}/{uc_count} UCs analysed"}, value_blocker if uc_count and analysed < uc_count else None),
                {"id": "qualification", "skill": "qualification-tunnel-router", "status": "ready", "gate": "Only matching crosses account and product truth"},
            ],
            "current": {"use_cases": uc_count, "value_chain_analyses": analysed, "qualification_stage": qualification["stage"]},
        }

    def _offer(self, offer_id: str) -> dict[str, Any]:
        if not offer_id:
            raise ControlPlaneError("offer_id is required for offer workflow")
        index = _read_yaml(self.root / "product_catalog" / "index.yaml")
        entry = next((item for item in index.get("offers", []) or [] if isinstance(item, dict) and item.get("offer_id") == offer_id), None)
        if entry is None:
            raise ControlPlaneError(f"unknown offer: {offer_id}")
        profile_path = self.root / "product_catalog" / str(entry.get("file") or "")
        profile = _read_yaml(profile_path).get("offer", {}) if profile_path.is_file() else {}
        proof = profile.get("proof") or {}
        unknowns = profile.get("unknowns") or []
        owner_review = profile.get("status") not in {"draft", "reconstructed"} and not unknowns
        evidence_status = "completed" if proof.get("evidence_grade") not in {None, "U1", "N0"} else "review"
        review_blocker = human_review_blocker(
            key=f"{offer_id}:owner-review",
            message="Canonical offer still has draft/reconstructed status or unresolved product unknowns.",
            required_state="Product owner validates packaging, proof, delivery capacity and material unknowns",
            cta_label="Valider l'offre",
            postcondition="canonical profile is owner-reviewed or unresolved unknowns remain explicit",
        )
        return {
            "schema_version": "0.7",
            "kind": "offer",
            "target": offer_id,
            "label": profile.get("name") or entry.get("name") or offer_id,
            "profile_version": profile.get("profile_version"),
            "steps": [
                {"id": "source_evidence", "skill": "product-icp-intelligence", "status": evidence_status, "gate": "Harvest/import sources remain candidates until product review"},
                {"id": "canonical_profile", "skill": "product-icp-intelligence", "status": "completed" if profile else "ready", "gate": "Versioned problem, ICP, hard gates, proof and unknowns"},
                attach_resolution({"id": "owner_review", "skill": None, "status": "completed" if owner_review else "blocked", "gate": "Owner validates packaging, proof, delivery capacity and unresolved unknowns"}, None if owner_review else review_blocker),
                {"id": "qualification_ready", "skill": "qualification-tunnel-router", "status": "ready" if profile else "blocked", "gate": "Snapshot only when a qualification workflow explicitly needs this offer"},
            ],
        }

    def _qualification(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for qualification workflow")
        study = QualificationCockpit(self.root).study(study_id)
        if study is None:
            raise ControlPlaneError(f"unknown study: {study_id}")
        return {
            "schema_version": "0.7",
            "kind": "qualification",
            "target": study_id,
            "label": study["company"],
            "stage": study["stage"],
            "decision": study["decision"],
            "steps": study["steps"],
            "current_blocker": study.get("current_blocker"),
        }

    def _reach(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for reach workflow")
        qualification = QualificationCockpit(self.root).study(study_id)
        if qualification is None:
            raise ControlPlaneError(f"unknown study: {study_id}")
        try:
            preview = ReachMatchmaker(self.root).preview(study_id)
        except ControlPlaneError as exc:
            resolution = qualification.get("current_blocker")
            if resolution is None:
                resolution = blocker(
                    category="organization",
                    key=f"{study_id}:reach-prerequisite",
                    message=str(exc),
                    required_state="Qualification prerequisites for reach are valid and current",
                    owner_skill="qualification-tunnel-router",
                    cta_label="Résoudre les prérequis",
                    cta_input=f"Inspecte le study {study_id} et route vers le prérequis manquant avant de relancer le reach.",
                    context_paths=[qualification["study_path"]],
                    postcondition="qualification exposes a valid positive fit and current company contact handoff",
                )
            fit_done = bool(qualification["artifacts"].get("fit_progression_allowed"))
            contacts_done = bool(qualification["artifacts"].get("contacts_ready"))
            return {
                "schema_version": "0.7",
                "kind": "reach",
                "target": study_id,
                "label": qualification["company"],
                "steps": [
                    {"id": "fit", "skill": "opportunity-fit-matching", "status": "completed" if fit_done else "blocked", "gate": "Valid positive fit with hard gates respected"},
                    {"id": "contacts", "skill": "person-opportunity-targeting", "status": "completed" if contacts_done else ("blocked" if fit_done else "locked"), "gate": "Current company-linked targets for the selected offer"},
                    {"id": "org_newsflow", "skill": "tech-leadership-org-intelligence", "status": "conditional" if contacts_done else "locked", "gate": "Organization/decision evidence and role validation; newsflow only informs why-now"},
                    attach_resolution({"id": "reach", "skill": "iterative-reach-matchmaking", "status": "blocked", "gate": "Resolve qualification/contact prerequisites before stakeholder sequencing"}, resolution),
                    {"id": "pilot", "skill": "engagement-pilot-design", "status": "locked", "gate": "Resolved reach before pilot/proof"},
                ],
                "current": {"stakeholders": 0, "blockers": 1, "prerequisite_error": str(exc)},
            }
        blockers = preview.get("blockers", []) or []
        steps = [
            {"id": "fit", "skill": "opportunity-fit-matching", "status": "completed", "gate": f"Valid {preview['fit_decision']} fit"},
            {"id": "contacts", "skill": "person-opportunity-targeting", "status": "completed" if preview["stakeholders"] else "blocked", "gate": "Company-linked contact targets"},
            {"id": "org_newsflow", "skill": "tech-leadership-org-intelligence", "status": "conditional", "gate": "Organization/decision evidence and role validation; newsflow only informs why-now"},
            attach_resolution({"id": "reach", "skill": "iterative-reach-matchmaking", "status": "blocked" if blockers else "ready", "gate": "Promoter/prescriber/user/technical/veto lanes with first/second wave"}, blockers[0] if blockers else None),
            {"id": "pilot", "skill": "engagement-pilot-design", "status": "locked" if blockers else "ready", "gate": "Resolved reach before pilot/proof"},
        ]
        return {"schema_version": "0.7", "kind": "reach", "target": study_id, "label": preview.get("company") or study_id, "steps": steps, "current": {"stakeholders": len(preview["stakeholders"]), "blockers": len(blockers)}}

    def _value_chain(self, study_id: str, use_case_id: str) -> dict[str, Any]:
        if not study_id or not use_case_id:
            raise ControlPlaneError("study_id and use_case_id are required for value-chain workflow")
        study = ValueChainCatalog(self.root).study(study_id)
        uc = next((item for item in study["use_cases"] if item["use_case_id"] == use_case_id), None)
        if uc is None:
            raise ControlPlaneError(f"unknown use case {use_case_id} in study {study_id}")
        analysis_exists = uc["analysis_status"] == "completed"
        analysis_blocker = blocker(
            category="value_chain",
            key=f"{study_id}:{use_case_id}:analysis",
            message="Porter/Ishikawa analysis has not been produced for this canonical UC.",
            required_state="Evidence-bounded 05c analysis",
            owner_skill="enterprise-value-chain-causal-analysis",
            cta_label="Analyser la chaîne de valeur",
            cta_input=f"Analyse {use_case_id} du study {study_id} avec Porter/Ishikawa et garde les workflows adjacents au statut hypothèse.",
            context_paths=[study["inventory_path"]],
            postcondition="05c contains analysis for the target UC",
        )
        return {
            "schema_version": "0.7",
            "kind": "value_chain",
            "target": f"{study_id}:{use_case_id}",
            "label": uc["name"],
            "steps": [
                {"id": "canonical_uc", "skill": "enterprise-use-case-intelligence", "status": "completed", "gate": "UC exists in company inventory"},
                attach_resolution({"id": "porter_ishikawa", "skill": "enterprise-value-chain-causal-analysis", "status": "completed" if analysis_exists else "blocked", "gate": "Analysis is evidence-bounded and product-blind"}, None if analysis_exists else analysis_blocker),
                {"id": "graph", "skill": None, "status": "ready" if analysis_exists else "locked", "gate": "Derived typed links only"},
                {"id": "validate_adjacent", "skill": "enterprise-use-case-intelligence", "status": "conditional", "gate": "Adjacent workflow must be validated before canonical UC promotion"},
            ],
        }

    def _nudging(self, study_id: str) -> dict[str, Any]:
        if not study_id:
            raise ControlPlaneError("study_id is required for nudging workflow")
        inventories = UseCaseNudger(self.root).list_inventories()
        inventory = next((row for row in inventories if row["study_id"] == study_id), None)
        inventory_ready = bool(inventory and inventory["use_case_count"])
        inventory_blocker = blocker(
            category="use_case",
            key=f"{study_id}:nudging-inventory",
            message="Nudging requires an existing company use-case inventory.",
            required_state="At least one canonical company UC in 05b",
            owner_skill="enterprise-use-case-intelligence",
            cta_label="Construire l'inventaire UC",
            cta_input=f"Construis ou complète l'inventaire UC du study {study_id} sans charger ICB ou product fit.",
            postcondition="nudging can read the company UC inventory",
        )
        review_blocker = human_review_blocker(
            key=f"{study_id}:nudge-review",
            message="Nudges remain hypotheses until reviewed against company evidence and falsifier.",
            required_state="Human review accepts/rejects nudge and records feedback when observed",
            cta_label="Revoir les nudges",
            postcondition="nudge is accepted/rejected and future feedback route is explicit",
        )
        return {
            "schema_version": "0.7",
            "kind": "nudging",
            "target": study_id,
            "label": inventory["company"] if inventory else study_id,
            "steps": [
                attach_resolution({"id": "inventory", "skill": "enterprise-use-case-intelligence", "status": "completed" if inventory_ready else "blocked", "gate": "Product-blind company use-case inventory"}, None if inventory_ready else inventory_blocker),
                {"id": "graph_context", "skill": None, "status": "ready" if inventory_ready else "locked", "gate": "Same-company derived UC graph only"},
                {"id": "nudge", "skill": "use-case-nudging", "status": "ready" if inventory_ready else "locked", "gate": "Use-case inventory only; no ICB or product-fit context"},
                attach_resolution({"id": "review", "skill": None, "status": "blocked" if inventory_ready else "locked", "gate": "Human review + falsifier before reuse"}, review_blocker if inventory_ready else None),
                {"id": "feedback", "skill": "enterprise-use-case-intelligence", "status": "conditional", "gate": "Record observed feedback/outcome before strengthening future nudges"},
            ],
        }
