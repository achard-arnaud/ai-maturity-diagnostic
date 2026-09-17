"""/api/v1/workspaces/{workspace_id}/target-plans read/write model
(Epic 08 S05). Stop condition: "accès borné" (bounded access) --
IDOR-safe cross-workspace 404s (same convention as every other v1
route), and pagination is always bounded (1-100), never unbounded.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.acquisition_policy import (
    AcquisitionPolicyError,
    SearchRequest,
    candidate_to_evidence,
    candidate_to_external_identity_mapping,
)
from app.authruntime.deps import RequestContext, require_workspace_access
from app.buying_committee_view import build_committee_graph
from app.evidence_store import put_evidence
from app.external_identity_store import find_by_external_subject_ref, list_mappings_for_entity, put_mapping
from app.harvest_orchestration import run_harvest
from app.target_plan_store import (
    TargetPlanNotFound,
    get_plan,
    list_plans,
    list_stakeholders_for_plan,
)


def create_v1_target_plan_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/target-plans")
    def list_plans_route(
        workspace_id: str,
        status_filter: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_plans(root, workspace_id, status=status_filter, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/target-plans/{target_plan_id}")
    def get_plan_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            plan = get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return plan

    @router.get("/target-plans/{target_plan_id}/stakeholders")
    def list_stakeholders_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        stakeholders = list_stakeholders_for_plan(root, workspace_id, target_plan_id)
        return {"items": stakeholders}

    @router.get("/target-plans/{target_plan_id}/committee-graph")
    def get_committee_graph_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        stakeholders = list_stakeholders_for_plan(root, workspace_id, target_plan_id)
        active = [s for s in stakeholders if s["status"] == "active"]
        return build_committee_graph(active, {})

    @router.post("/target-plans/{target_plan_id}/stakeholders/{stakeholder_role_id}/acquire-linkedin")
    def acquire_linkedin_route(
        workspace_id: str,
        target_plan_id: str,
        stakeholder_role_id: str,
        payload: dict[str, Any] = Body(default={}),
        ctx: RequestContext = Depends(require_workspace_access()),
    ):
        """Epic 14 S06: LinkedIn/person hardening. A TargetPlan's own
        existence already proves Fit (target_plan_v1.schema.yaml requires
        fit_assessment_id), so a valid plan + stakeholder is this route's
        entire "post-Fit" gate -- ADR-011 S6 restricts linkedin to
        space="targets" only, and SearchRequest itself refuses linkedin
        from any other space.

        Every resulting candidate becomes evidence for the stakeholder's
        person_entity_id, then an ExternalIdentityMapping with
        status="candidate" only (candidate_to_external_identity_mapping
        has no parameter that could produce anything else) -- current
        role/authority stay unconfirmed until a separate, existing human/
        primary role-validation step resolves them; this route never
        writes a person's current_role or flips a mapping to "validated".
        """
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

        stakeholder = next(
            (
                s
                for s in list_stakeholders_for_plan(root, workspace_id, target_plan_id)
                if s["stakeholder_role_id"] == stakeholder_role_id
            ),
            None,
        )
        if stakeholder is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        person_entity_id = stakeholder["person_entity_id"]

        query = str(payload.get("query") or stakeholder.get("title") or person_entity_id).strip()
        try:
            request = SearchRequest(
                workspace_id=workspace_id,
                query=query,
                sources=("linkedin",),
                space="targets",
                requested_by=ctx.email,
                days=int(payload.get("days") or 30),
                limit=int(payload.get("limit") or 10),
                enrich=bool(payload.get("enrich", True)),
                allow_commercial=bool(payload.get("allow_commercial", False)),
            )
        except AcquisitionPolicyError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

        harvest = run_harvest(root, workspace_id, ctx.email, request, entity_refs=(person_entity_id,))

        mappings: list[dict[str, Any]] = []
        for candidate in harvest.candidates:
            existing = find_by_external_subject_ref(
                root, workspace_id, provider="linkedin", external_subject_ref=candidate.locator
            )
            if existing is not None:
                mappings.append(existing)
                continue
            try:
                evidence = candidate_to_evidence(candidate)
            except AcquisitionPolicyError:
                continue
            put_evidence(root, workspace_id, evidence)
            mapping = candidate_to_external_identity_mapping(
                candidate,
                provider="linkedin",
                internal_entity_type="person",
                internal_entity_id=person_entity_id,
                source_evidence_id=evidence["evidence_id"],
            )
            put_mapping(root, workspace_id, mapping)
            mappings.append(mapping)

        return {
            "run_id": harvest.run_id,
            "status": harvest.status,
            "correlation_id": harvest.correlation_id,
            "target_plan_id": target_plan_id,
            "stakeholder_role_id": stakeholder_role_id,
            "source_runs": [
                {
                    "source": r.source,
                    "status": r.status,
                    "count": len(r.candidates),
                    "elapsed_ms": r.elapsed_ms,
                    "error": r.error,
                }
                for r in harvest.source_runs
            ],
            "identity_mappings": mappings,
        }

    @router.get("/target-plans/{target_plan_id}/stakeholders/{stakeholder_role_id}/identity-mappings")
    def list_identity_mappings_route(
        workspace_id: str,
        target_plan_id: str,
        stakeholder_role_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        stakeholder = next(
            (
                s
                for s in list_stakeholders_for_plan(root, workspace_id, target_plan_id)
                if s["stakeholder_role_id"] == stakeholder_role_id
            ),
            None,
        )
        if stakeholder is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        mappings = list_mappings_for_entity(
            root, workspace_id, internal_entity_type="person", internal_entity_id=stakeholder["person_entity_id"]
        )
        return {"items": mappings}

    return router
