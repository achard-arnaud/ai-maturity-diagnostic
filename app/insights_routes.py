"""Epic 13 S05: workspace-safe analytics and governed-learning API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.event_journal import EventJournal, EventJournalIntegrityError
from app.insights_metrics import CohortPolicy, MetricPolicyError, metric_catalog
from app.insights_projection import build_projection
from app.learning_proposals import LearningProposalError, LearningProposalStore


MINIMUM_COHORT_SIZE = 3


def create_v1_insights_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/metrics/catalog")
    def catalog_route(workspace_id: str, _ctx: RequestContext = Depends(require_workspace_access())):
        return {"items": metric_catalog(), "projection_only": True}

    @router.get("/insights")
    def insights_route(
        workspace_id: str,
        start_at: str = Query("2000-01-01T00:00:00Z"),
        end_at: str = Query("2100-01-01T00:00:00Z"),
        source: str | None = None,
        sector: str | None = None,
        product: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        dimensions = tuple((key, value) for key, value in (("source", source), ("sector", sector), ("product", product)) if value)
        try:
            policy = CohortPolicy("api-cohort", workspace_id, start_at, end_at, dimensions)
            projection = build_projection(EventJournal(root).replay(), policy)
        except (MetricPolicyError, EventJournalIntegrityError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        suppressed = projection["source_event_count"] < MINIMUM_COHORT_SIZE
        if suppressed:
            projection["metrics"] = []
        projection["privacy"] = {"minimum_cohort_size": MINIMUM_COHORT_SIZE, "suppressed": suppressed}
        projection["available_dimensions"] = ["source", "sector", "product"]
        return projection

    @router.get("/learning-proposals")
    def list_proposals_route(workspace_id: str, limit: int = Query(50, ge=1, le=100), _ctx: RequestContext = Depends(require_workspace_access())):
        return {"items": LearningProposalStore(root, workspace_id).list()[:limit]}

    @router.post("/learning-proposals", status_code=status.HTTP_201_CREATED)
    def create_proposal_route(workspace_id: str, payload: dict[str, Any] = Body(...), ctx: RequestContext = Depends(require_workspace_access())):
        try:
            return LearningProposalStore(root, workspace_id).create(
                origin=str(payload.get("origin", "")), target_kind=str(payload.get("target_kind", "")),
                target_ref=str(payload.get("target_ref", "")), hypothesis=str(payload.get("hypothesis", "")),
                evidence_refs=list(payload.get("evidence_refs") or []), actor_id=ctx.user_id,
            )
        except LearningProposalError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    @router.post("/learning-proposals/{proposal_id}/transitions")
    def transition_proposal_route(workspace_id: str, proposal_id: str, payload: dict[str, Any] = Body(...), ctx: RequestContext = Depends(require_workspace_access())):
        try:
            return LearningProposalStore(root, workspace_id).transition(
                proposal_id, to_status=str(payload.get("to_status", "")), actor_id=ctx.user_id,
                rationale=str(payload.get("rationale", "")), experiment_id=payload.get("experiment_id"), result_ref=payload.get("result_ref"),
            )
        except LearningProposalError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return router
