"""Epic 15 S03: Artifact index -- rebuildable discovery over the existing
canonical stores, never a second source of truth.

Every list_artifacts()/get_artifact() call recomputes its answer live from
the underlying stores (app.signal_store, app.evidence_store, ...) --
there is no persisted index file to go stale or need an explicit
"rebuild" step. The only thing this module persists on its own is the
archive/restore flag (app.artifact_archive_store), because "hidden from
default listing" has no backing field on any canonical object and is
the one genuinely index-only piece of state (Epic 15's own "Don't":
never let the library mutate domain truth, and never build a second
document store for the objects themselves).

Coverage: signal, evidence, research_case, claim, demand, fit_assessment,
target_plan, stakeholder_role, sequence, opportunity, learning_proposal.
Not yet covered: touchpoint (no workspace-wide list helper exists --
only per-step) and product_snapshot (no workspace_id field at all, per
ADR-008's shared-core-plus-overlay model -- doesn't fit this per-
workspace index without a separate design decision). Both are left out
rather than half-implemented; adding either is a small, isolated follow-up
once/if a workspace-wide list helper is added for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.artifact_archive_store import list_archived_ids
from app.artifact_policy import ArtifactPolicyError, KNOWN_KINDS, build_artifact
from app.claim_store import list_claims
from app.demand_store import list_demands
from app.evidence_store import list_evidence
from app.fit_store import list_fits
from app.learning_proposals import LearningProposalStore
from app.opportunity_store import list_opportunities
from app.reach_store import list_sequences
from app.research_case_store import get_case, list_cases
from app.signal_store import list_signals
from app.target_plan_store import list_all_stakeholders, list_plans


def _trim(text: str | None, length: int = 80) -> str:
    text = (text or "").strip()
    return text if len(text) <= length else text[: length - 1] + "…"


def _drain(list_fn: Callable[..., Any], root: Path, workspace_id: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Exhaust a cursor-paginated list_*() store function regardless of
    its own page-size cap (app.opportunity_store caps at 100; others only
    require >0), so every adapter below sees the whole workspace."""
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        page = list_fn(root, workspace_id, limit=100, cursor=cursor, **kwargs)
        items.extend(page.items)
        if page.next_cursor is None:
            return items
        cursor = page.next_cursor


def _signals(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_signals, root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:signal:{r['signal_id']}",
            kind="signal",
            title=f"Signal via {r['source']['kind']}",
            workspace_id=workspace_id,
            created_at=r["observed_at"],
            created_by=r["source"].get("ref") or "unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/signals/{r['signal_id']}",
            related_ids=(r["company_entity_id"],) if r.get("company_entity_id") else (),
        )
        for r in records
    ]


def _evidence(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = list_evidence(root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:evidence:{r['evidence_id']}",
            kind="evidence",
            title=f"Evidence: {_trim(r['excerpt'])}",
            workspace_id=workspace_id,
            created_at=r["dated_at"],
            created_by=r["source"].get("ref") or "unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/evidence/{r['evidence_id']}",
            related_ids=tuple(r.get("entity_refs") or ()),
        )
        for r in records
    ]


def _research_cases(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_cases, root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:research_case:{r['research_case_id']}",
            kind="research_case",
            title=f"Research case for {r['company_entity_id']}",
            workspace_id=workspace_id,
            created_at=r["created_at"],
            created_by=r.get("owner") or "unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/research-cases/{r['research_case_id']}",
            related_ids=(r["company_entity_id"],),
        )
        for r in records
    ]


def _claims(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = list_claims(root, workspace_id)
    # claim_v1 has no timestamp/actor field of its own -- fall back to the
    # owning ResearchCase's created_at/owner, since every claim belongs to
    # exactly one (research_case_id is required on the claim).
    case_cache: dict[str, dict[str, Any]] = {}
    artifacts = []
    for r in records:
        case_id = r["research_case_id"]
        if case_id not in case_cache:
            try:
                case_cache[case_id] = get_case(root, workspace_id, case_id)
            except Exception:
                case_cache[case_id] = {}
        case = case_cache[case_id]
        artifacts.append(
            build_artifact(
                artifact_id=f"artifact:claim:{r['claim_id']}",
                kind="claim",
                title=f"Claim ({r['claim_type']}): {_trim(r['statement'])}",
                workspace_id=workspace_id,
                created_at=case.get("created_at") or "1970-01-01T00:00:00+00:00",
                created_by=case.get("owner") or "unknown",
                locator=f"/api/v1/workspaces/{workspace_id}/research-cases/{case_id}",
                related_ids=(r["company_entity_id"], case_id),
            )
        )
    return artifacts


def _demands(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    # list_demands() strips the store's internal _version field from every
    # record it returns (only get_demand()'s point lookup exposes it) --
    # the list adapter below always reports version=1 rather than doing a
    # get_demand() round trip per row just for this cosmetic field. Same
    # applies to _fits() below.
    records = _drain(list_demands, root, workspace_id)
    artifacts = []
    for r in records:
        problem = r.get("problem") or {}
        title = (
            f"Demand: {_trim(problem.get('value'))}"
            if problem.get("known") and problem.get("value")
            else f"Demand for {r['company_entity_id']}"
        )
        artifacts.append(
            build_artifact(
                artifact_id=f"artifact:demand:{r['demand_id']}",
                kind="demand",
                title=title,
                workspace_id=workspace_id,
                created_at=r["created_at"],
                created_by="unknown",
                locator=f"/api/v1/workspaces/{workspace_id}/demands/{r['demand_id']}",
                related_ids=(r["company_entity_id"],),
            )
        )
    return artifacts


def _fits(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_fits, root, workspace_id)
    artifacts = []
    for r in records:
        demand_id = (r.get("input_lock") or {}).get("demand_id")
        artifacts.append(
            build_artifact(
                artifact_id=f"artifact:fit_assessment:{r['fit_assessment_id']}",
                kind="fit_assessment",
                title=f"Fit assessment ({r.get('verdict') or r['status']})",
                workspace_id=workspace_id,
                created_at=r["created_at"],
                created_by="unknown",
                locator=f"/api/v1/workspaces/{workspace_id}/fit-assessments/{r['fit_assessment_id']}",
                related_ids=(demand_id,) if demand_id else (),
            )
        )
    return artifacts


def _target_plans(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_plans, root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:target_plan:{r['target_plan_id']}",
            kind="target_plan",
            title=f"Target plan for {r['company_entity_id']}",
            workspace_id=workspace_id,
            created_at=r["created_at"],
            created_by="unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/target-plans/{r['target_plan_id']}",
            related_ids=(r["company_entity_id"], r["fit_assessment_id"]),
        )
        for r in records
    ]


def _stakeholder_roles(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = list_all_stakeholders(root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:stakeholder_role:{r['stakeholder_role_id']}",
            kind="stakeholder_role",
            title=f"Stakeholder: {r.get('title') or r['role']}",
            workspace_id=workspace_id,
            created_at=r["assigned_at"],
            created_by=r.get("assigned_by") or "unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/target-plans/{r['target_plan_id']}/stakeholders",
            related_ids=(r["target_plan_id"], r["person_entity_id"]),
        )
        for r in records
    ]


def _sequences(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_sequences, root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:sequence:{r['sequence_id']}",
            kind="sequence",
            title=f"Sequence ({r['status']})",
            workspace_id=workspace_id,
            created_at=r["created_at"],
            created_by="unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/sequences/{r['sequence_id']}",
            related_ids=(r["target_plan_id"], r["stakeholder_role_id"]),
        )
        for r in records
    ]


def _opportunities(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = _drain(list_opportunities, root, workspace_id)
    return [
        build_artifact(
            artifact_id=f"artifact:opportunity:{r['opportunity_id']}",
            kind="opportunity",
            title=f"Opportunity ({r['status']})",
            workspace_id=workspace_id,
            created_at=r["created_at"],
            created_by="unknown",
            locator=f"/api/v1/workspaces/{workspace_id}/opportunities/{r['opportunity_id']}",
            related_ids=tuple(
                v for v in (r.get("demand_id"), r.get("fit_assessment_id"), r.get("target_plan_id")) if v
            ),
        )
        for r in records
    ]


def _learning_proposals(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    records = LearningProposalStore(root, workspace_id).list()
    return [
        build_artifact(
            artifact_id=f"artifact:learning_proposal:{r['proposal_id']}",
            kind="learning_proposal",
            title=f"Learning proposal: {_trim(r['hypothesis'])}",
            workspace_id=workspace_id,
            created_at=r["created_at"],
            created_by=r["created_by"],
            locator=f"/api/v1/workspaces/{workspace_id}/learning-proposals/{r['proposal_id']}",
            related_ids=(r["target"]["ref"],),
        )
        for r in records
    ]


_ADAPTERS: dict[str, Callable[[Path, str], list[dict[str, Any]]]] = {
    "signal": _signals,
    "evidence": _evidence,
    "research_case": _research_cases,
    "claim": _claims,
    "demand": _demands,
    "fit_assessment": _fits,
    "target_plan": _target_plans,
    "stakeholder_role": _stakeholder_roles,
    "sequence": _sequences,
    "opportunity": _opportunities,
    "learning_proposal": _learning_proposals,
}

assert set(_ADAPTERS) <= KNOWN_KINDS  # every adapter's kind must be registered in the policy layer


@dataclass(frozen=True)
class ArtifactPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def _apply_archive_state(root: Path, workspace_id: str, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    archived_ids = list_archived_ids(root, workspace_id)
    if not archived_ids:
        return artifacts
    return [
        {**a, "status": "archived"} if a["artifact_id"] in archived_ids else a
        for a in artifacts
    ]


def list_artifacts(
    root: Path,
    workspace_id: str,
    *,
    kind: str | None = None,
    related_to: str | None = None,
    run_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> ArtifactPage:
    """Metadata search is a case-insensitive substring match on `title`
    only (`q`) -- no vector/semantic engine, per this Epic's own "Don't":
    the title is the one free-text field every kind actually has (many
    canonical objects, e.g. TargetPlan/Sequence/Opportunity, have no body
    text of their own to index -- see app.artifact_index's per-kind
    adapters), so content search beyond title is not offered rather than
    faked."""
    if limit <= 0:
        raise ArtifactPolicyError("limit must be positive")
    if kind is not None and kind not in _ADAPTERS:
        raise ArtifactPolicyError(f"unknown or unsupported kind: {kind!r}")

    kinds = [kind] if kind else list(_ADAPTERS)
    artifacts: list[dict[str, Any]] = []
    for k in kinds:
        artifacts.extend(_ADAPTERS[k](root, workspace_id))

    artifacts = _apply_archive_state(root, workspace_id, artifacts)

    if related_to is not None:
        artifacts = [a for a in artifacts if related_to in a["related_ids"]]
    if run_id is not None:
        artifacts = [a for a in artifacts if a.get("run_id") == run_id]
    if status is not None:
        artifacts = [a for a in artifacts if a["status"] == status]
    if q is not None and q.strip():
        needle = q.strip().lower()
        artifacts = [a for a in artifacts if needle in a["title"].lower()]

    artifacts.sort(key=lambda a: a["artifact_id"])
    if cursor is not None:
        artifacts = [a for a in artifacts if a["artifact_id"] > cursor]
    page = artifacts[:limit]
    next_cursor = page[-1]["artifact_id"] if len(artifacts) > limit else None
    return ArtifactPage(items=page, next_cursor=next_cursor)


class ArtifactNotFound(ArtifactPolicyError):
    pass


def get_artifact(root: Path, workspace_id: str, artifact_id: str) -> dict[str, Any]:
    """Point lookup by artifact_id. Materializes only the one kind the id
    names (artifact_id is always "artifact:{kind}:{underlying_id}"),
    never a full-catalog scan."""
    parts = artifact_id.split(":", 2)
    if len(parts) != 3 or parts[0] != "artifact" or parts[1] not in _ADAPTERS:
        raise ArtifactNotFound(f"unknown artifact_id: {artifact_id!r}")
    kind = parts[1]
    for artifact in _apply_archive_state(root, workspace_id, _ADAPTERS[kind](root, workspace_id)):
        if artifact["artifact_id"] == artifact_id:
            return artifact
    raise ArtifactNotFound(f"artifact {artifact_id!r} not found in workspace {workspace_id}")
