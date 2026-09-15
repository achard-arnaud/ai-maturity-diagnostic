from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.blockers import blocker
from app.core import RepoControlPlane
from app.demand import DemandCatalog
from app.qualification import QualificationCockpit
from app.uc_graph import UseCaseGraph
from app.value_chain import ValueChainCatalog


def _parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _age_fields(last_touched: Any, stale_after_months: int, *, as_of: date) -> dict[str, Any]:
    """Age/staleness computation for a follow-up item, reusing the same
    `stale_after_months` convention app.network_index._is_stale already uses
    for people/companies (a whole number of months == months * 30 days).

    `last_touched` is whatever timestamp already exists for that item's kind
    (a study manifest's `updated_at`, a sector's most-recently-updated study,
    or a backlog file's document-level `updated_at`) -- no new "last touched"
    field is invented here. When no such timestamp is available at all,
    `days_in_current_state` is None and the item is never flagged stale
    (silence, not a false "0 days fresh")."""
    parsed = _parse_iso_date(last_touched)
    if parsed is None:
        return {"days_in_current_state": None, "is_stale": False}
    days = max((as_of - parsed).days, 0)
    try:
        months = int(stale_after_months)
    except (TypeError, ValueError):
        months = 0
    is_stale = months >= 1 and days >= months * 30
    return {"days_in_current_state": days, "is_stale": is_stale}


@dataclass(frozen=True)
class FollowUpDashboard:
    root: Path
    # Same convention/name as app.network_index's per-record stale_after_months,
    # applied here as a single dashboard-wide default (see TODO(red-team-spec)
    # below for why this is flat rather than per-kind for now).
    stale_after_months: int = 1

    @classmethod
    def for_workspace(cls, workspace_id: str, repo_root: Path | None = None) -> "FollowUpDashboard":
        """Instantiate against a specific workspace (ADR-007 §5 step 1)."""
        from app.workspace_paths import resolve_workspace_root

        return cls(resolve_workspace_root(workspace_id, repo_root))

    def items(self, *, as_of: date | None = None) -> list[dict[str, Any]]:
        effective_date = as_of or date.today()
        items: list[dict[str, Any]] = []
        for row in QualificationCockpit(self.root).list_studies():
            current = row.get("current_blocker")
            if current:
                items.append(
                    {
                        "id": f"QUAL:{row['study_id']}:{current['blocker_id']}",
                        "priority": "P0" if current.get("severity") in {"blocker", "critical"} else "P1",
                        "kind": "qualification",
                        "label": row["company"],
                        "state": row["stage"],
                        "message": current["message"],
                        "resolver": current,
                        "navigation": {"menu": "qualification", "study_id": row["study_id"]},
                        **_age_fields(row.get("updated_at"), self.stale_after_months, as_of=effective_date),
                    }
                )

        for row in ValueChainCatalog(self.root).list_studies():
            if row["pending_count"] <= 0:
                continue
            resolution = blocker(
                category="value_chain",
                key=f"{row['study_id']}:pending:{row['pending_count']}",
                message=f"{row['pending_count']} canonical use case(s) have no Porter/Ishikawa analysis.",
                required_state="Relevant UCs have evidence-bounded 05c analyses",
                owner_skill="enterprise-value-chain-causal-analysis",
                cta_label="Analyser les UC pending",
                cta_input=f"Analyse les use cases prioritaires encore pending du study {row['study_id']} via Porter/Ishikawa sans inventer de demande.",
                context_paths=[row["inventory_path"]],
                postcondition="selected UCs have 05c analyses and validation questions",
            )
            items.append(
                {
                    "id": f"VALUE:{row['study_id']}",
                    "priority": "P1",
                    "kind": "value_chain",
                    "label": row["company"],
                    "state": "pending",
                    "message": resolution["message"],
                    "resolver": resolution,
                    "navigation": {"menu": "demand", "study_id": row["study_id"]},
                    **_age_fields(row.get("updated_at"), self.stale_after_months, as_of=effective_date),
                }
            )

        demand = DemandCatalog(self.root).snapshot()
        for sector in demand["sectors"]:
            if sector["benchmark_state"] == "benchmark_edge":
                resolution = blocker(
                    category="sector",
                    key=f"{sector['sector_code']}:third-company-dashboard",
                    message="One more current complete company study unlocks sector benchmarking.",
                    required_state="3 current complete studies",
                    owner_skill="network-contact-intake",
                    cta_label="Ajouter une 3e entreprise",
                    cta_input=f"Ajoute une entreprise/source candidate pour le secteur ICB {sector['sector_code']} puis passe par mapping, screening et étude.",
                    postcondition="third company can enter the governed demand workflow",
                )
                items.append(
                    {
                        "id": f"SECTOR:{sector['sector_code']}:third",
                        "priority": "P1",
                        "kind": "sector",
                        "label": sector["sector_name"],
                        "state": sector["benchmark_state"],
                        "message": resolution["message"],
                        "resolver": resolution,
                        "navigation": {"menu": "demand", "sector_code": sector["sector_code"]},
                        **_age_fields(sector.get("most_recent_study_update"), self.stale_after_months, as_of=effective_date),
                    }
                )
            elif sector["benchmark_state"] == "benchmark_ready":
                resolution = blocker(
                    category="sector",
                    key=f"{sector['sector_code']}:benchmark-ready-dashboard",
                    message="Sector has enough eligible studies; consolidation has not been run yet.",
                    required_state="Evidence-preserving sector rollup",
                    owner_skill="sector-intelligence-consolidation",
                    cta_label="Lancer le benchmark",
                    cta_input=f"Consolide le secteur ICB {sector['sector_code']} en préservant company/study/use-case provenance.",
                    postcondition="sector rollup exists and keeps evidence scope",
                    severity="warning",
                )
                items.append(
                    {
                        "id": f"SECTOR:{sector['sector_code']}:benchmark",
                        "priority": "P1",
                        "kind": "sector",
                        "label": sector["sector_name"],
                        "state": sector["benchmark_state"],
                        "message": resolution["message"],
                        "resolver": resolution,
                        "navigation": {"menu": "demand", "sector_code": sector["sector_code"]},
                        **_age_fields(sector.get("most_recent_study_update"), self.stale_after_months, as_of=effective_date),
                    }
                )

        for todo in RepoControlPlane(self.root).backlog():
            if todo.get("status") == "completed":
                continue
            items.append(
                {
                    "id": f"TODO:{todo.get('id')}",
                    "priority": todo.get("priority") or "P2",
                    "kind": "technical_todo",
                    "label": todo.get("area") or "project",
                    "state": todo.get("status"),
                    "message": todo.get("task"),
                    "resolver": None,
                    "navigation": {"menu": "followup"},
                    "source": todo.get("source"),
                    **_age_fields(todo.get("source_updated_at"), self.stale_after_months, as_of=effective_date),
                }
            )
        # TODO(red-team-spec): days_in_current_state/is_stale above are computed
        # from the most recent timestamp already available per item kind (study
        # manifest updated_at, sector's most-recently-updated study, or backlog
        # file updated_at) using a single flat stale_after_months threshold for
        # every kind. There is still no first-seen-in-*this exact stage*
        # tracking (a study sitting in "reach" for 3 months looks the same as
        # one that moved stages last week but whose manifest wasn't touched
        # since), and no per-kind threshold. Revisit once follow-up volume
        # exceeds a handful of open P0/P1 items per week and a real per-stage
        # triage view becomes necessary.
        return sorted(items, key=lambda item: (str(item.get("priority") or "P9"), item["kind"], item["label"]))


@dataclass(frozen=True)
class UseCaseHeritage:
    root: Path

    @classmethod
    def for_workspace(cls, workspace_id: str, repo_root: Path | None = None) -> "UseCaseHeritage":
        """Instantiate against a specific workspace (ADR-007 §5 step 1)."""
        from app.workspace_paths import resolve_workspace_root

        return cls(resolve_workspace_root(workspace_id, repo_root))

    def company(self, study_id: str) -> dict[str, Any]:
        graph = UseCaseGraph(self.root).company(study_id)
        relations: dict[str, int] = {}
        for edge in graph["edges"]:
            relations[edge["relation"]] = relations.get(edge["relation"], 0) + 1
        return {
            "schema_version": "0.7",
            "scope": graph["scope"],
            "use_case_count": sum(1 for node in graph["nodes"] if node["node_type"] == "use_case"),
            "hypothesis_count": sum(1 for node in graph["nodes"] if node["node_type"] == "workflow_hypothesis"),
            "edge_count": len(graph["edges"]),
            "relations": relations,
            "graph": graph,
        }

    def sector(self, sector_code: str) -> dict[str, Any]:
        graph = UseCaseGraph(self.root).sector(sector_code)
        companies = sorted({node.get("company") for node in graph["nodes"] if node.get("company")})
        outcomes: dict[str, int] = {}
        for node in graph["nodes"]:
            outcome = str(node.get("outcome_family") or "").strip()
            if outcome:
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
        return {
            "schema_version": "0.7",
            "scope": graph["scope"],
            "companies": companies,
            "company_count": len(companies),
            "use_case_count": len(graph["nodes"]),
            "similarity_hypotheses": len(graph["edges"]),
            "outcome_families": outcomes,
            "graph": graph,
            "warning": "Sector heritage is comparative evidence; it never populates a company use-case inventory automatically.",
        }
