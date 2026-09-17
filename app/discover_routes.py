"""/api/v1/workspaces/{workspace_id}/discover/search (Epic 14 S04).

Discover-space search: runs a bounded harvest (app.harvest_orchestration,
S02/S03) across the caller-chosen sources, maps each resulting
EvidenceCandidate onto a signal (app.acquisition_policy.candidate_to_signal,
S01) and persists it via app.signal_store -- deduped against any signal
this workspace already has for the same dedup_key, so re-running the same
search never creates duplicate signals.

No automatic qualification: this route only ever creates status="new"
signals (app.signal_store's own contract) -- a signal always needs its
own existing reviewed -> linked/dismissed lifecycle (app.signal_policy)
before it can inform anything else. Reading persisted signals back with
filters/sort/pagination is GET /signals (app.signal_routes, unchanged);
this router does not duplicate that read path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.acquisition_policy import AcquisitionPolicyError, SearchRequest, candidate_to_signal
from app.authruntime.deps import RequestContext, require_workspace_access
from app.harvest_orchestration import recommended_sources_for_space, run_harvest
from app.signal_store import find_by_dedup_key, put_signal


def create_v1_discover_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.post("/discover/search")
    def discover_search_route(
        workspace_id: str,
        payload: dict[str, Any] = Body(...),
        ctx: RequestContext = Depends(require_workspace_access()),
    ):
        query = str(payload.get("query") or "").strip()
        sources = payload.get("sources")
        if not sources:
            sources = list(recommended_sources_for_space("discover"))
        try:
            request = SearchRequest(
                workspace_id=workspace_id,
                query=query,
                sources=tuple(sources),
                space="discover",
                requested_by=ctx.email,
                days=int(payload.get("days") or 30),
                limit=int(payload.get("limit") or 10),
                enrich=bool(payload.get("enrich", True)),
                allow_commercial=bool(payload.get("allow_commercial", False)),
            )
        except AcquisitionPolicyError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

        entity_refs = tuple(payload.get("entity_refs") or ())
        harvest = run_harvest(root, workspace_id, ctx.email, request, entity_refs=entity_refs)

        # Dedupe within this run's own candidates first (same dedup_key
        # observed via two sources/lanes in one search), then against
        # every signal the workspace already has.
        seen_dedup_keys: set[str] = set()
        signals: list[dict[str, Any]] = []
        for candidate in harvest.candidates:
            if candidate.dedup_key in seen_dedup_keys:
                continue
            seen_dedup_keys.add(candidate.dedup_key)

            existing = find_by_dedup_key(root, workspace_id, candidate.dedup_key)
            if existing is not None:
                signal = existing
            else:
                signal = candidate_to_signal(candidate)
                put_signal(root, workspace_id, signal)

            signals.append(
                {
                    "signal": signal,
                    "why_matched": {
                        "query": request.query,
                        "acquisition_source": candidate.acquisition_source,
                        "excerpt": candidate.excerpt,
                    },
                }
            )

        return {
            "run_id": harvest.run_id,
            "status": harvest.status,
            "correlation_id": harvest.correlation_id,
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
            "signals": signals,
        }

    return router
