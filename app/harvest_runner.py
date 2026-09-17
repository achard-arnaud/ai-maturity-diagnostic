"""Epic 14 S02: harvest wrapper around scripts/social_search/'s vendored
source adapters (ADR-011: docs/ADR-011-evidence-acquisition-search.md).

Turns a SearchRequest plus one source's raw social_search.core.Result list
into EvidenceCandidate[] via app.acquisition_policy, adding per-source
failure isolation and a hard wall-clock timeout -- neither of which the
vendored adapters enforce themselves (their own internal per-stage
timeouts, e.g. youtube.py's yt-dlp subprocess calls, only bound one stage,
not the adapter's total wall time as seen by this caller).

Budget/correlation-ID/run-manager wiring (RunManager/BudgetLedger/
correlation_scope) is Epic 14 S03's job, layered on top of this module's
run_sources() -- kept separate here because S02's own acceptance criteria
(failure isolation, timeout, public/no-purchase baseline, optional
provider enrichment explicit, no authenticated browser scraping) do not
require it, and S03 explicitly owns "bounded budgets ... run/correlation
ID" per EPIC_14_RESEARCH_ACQUISITION_AND_SEARCH.md.

Sequential by design: run_sources() calls run_source() once per source,
one at a time, never via a thread pool across sources. This keeps S03's
future per-workspace budget ledger writes free of concurrent-version
conflicts without needing a lock, at the cost of the upstream CLI's
ThreadPoolExecutor-across-sources speed (an EXTRACT_PATTERN reference,
not a requirement -- see ADR-011 S1). Each individual source call still
runs in its own single-worker pool so a hard timeout can be enforced on
it specifically.

No authenticated browser scraping, no credential persistence: this module
never imports selenium/playwright or a cookie jar, and every optional
commercial-provider path stays exactly as gated as the vendored adapters
already gate it (SearchRequest.allow_commercial plus an existing
environment key -- see scripts/social_search/NOTICE.md).
"""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass

from app.acquisition_policy import EvidenceCandidate, SearchRequest, build_evidence_candidate
from scripts.social_search import SEARCHERS

DEFAULT_PER_SOURCE_TIMEOUT_SECONDS = 60.0

SOURCE_RUN_STATUSES = frozenset({"ok", "empty", "error", "timeout"})


@dataclass(frozen=True)
class SourceRunResult:
    source: str
    status: str
    candidates: tuple[EvidenceCandidate, ...]
    elapsed_ms: int
    error: str | None = None


def _normalize_dated_at(date_str: str | None) -> str | None:
    """Result.date is often a plain YYYY-MM-DD; evidence_v1's dated_at
    wants a full date-time (ADR-011 S2 mapping table)."""
    if not date_str:
        return None
    if len(date_str) == 10:
        return f"{date_str}T00:00:00+00:00"
    return date_str


def _map_result(result: object, *, workspace_id: str, space: str, entity_refs: tuple[str, ...]) -> EvidenceCandidate:
    return build_evidence_candidate(
        candidate_id=f"cand_{uuid.uuid4().hex}",
        workspace_id=workspace_id,
        space=space,
        source_name=result.source,  # type: ignore[attr-defined]
        locator=result.url,  # type: ignore[attr-defined]
        title=result.title,  # type: ignore[attr-defined]
        snippet=result.snippet,  # type: ignore[attr-defined]
        dated_at=_normalize_dated_at(result.date),  # type: ignore[attr-defined]
        entity_refs=entity_refs,
        metadata=dict(result.metadata),  # type: ignore[attr-defined]
    )


def run_source(
    source: str,
    request: SearchRequest,
    *,
    entity_refs: tuple[str, ...] = (),
    timeout_seconds: float = DEFAULT_PER_SOURCE_TIMEOUT_SECONDS,
) -> SourceRunResult:
    """Run exactly one source adapter with failure isolation and a hard
    wall-clock timeout, mapping every raw Result into an EvidenceCandidate.

    Never raises for a source-side failure -- a failed/timed-out source is
    a SourceRunResult with status="error"/"timeout", not an exception the
    caller must catch (mirrors upstream's own run_source()/SourceRun
    shape, EXTRACT_PATTERN per ADR-011 S1). An unknown source name is a
    caller programming error and does raise.

    Timeout caveat, stated plainly rather than glossed over: Python cannot
    forcibly kill a running thread. On timeout this function returns
    immediately with status="timeout" and abandons the pool without
    waiting for it (`shutdown(wait=False)`) -- the underlying call may
    still be running in the background until it finishes or hits its own
    internal timeout; only walltime for the *caller* is bounded here.
    """

    if source not in SEARCHERS:
        raise ValueError(f"unknown source: {source!r}")
    handler = SEARCHERS[source]
    start = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(
            handler, request.query, request.days, request.limit, request.enrich, request.allow_commercial
        )
        results = future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        pool.shutdown(wait=False)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return SourceRunResult(source, "timeout", (), elapsed_ms, f"source did not complete within {timeout_seconds}s")
    except Exception as exc:
        pool.shutdown(wait=False)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return SourceRunResult(source, "error", (), elapsed_ms, f"{type(exc).__name__}: {exc}")
    pool.shutdown(wait=False)

    elapsed_ms = int((time.monotonic() - start) * 1000)
    candidates = tuple(
        _map_result(result, workspace_id=request.workspace_id, space=request.space, entity_refs=entity_refs)
        for result in results
    )
    status = "ok" if candidates else "empty"
    return SourceRunResult(source, status, candidates, elapsed_ms)


def run_sources(
    request: SearchRequest,
    *,
    entity_refs: tuple[str, ...] = (),
    timeout_seconds: float = DEFAULT_PER_SOURCE_TIMEOUT_SECONDS,
) -> list[SourceRunResult]:
    """Run every source in request.sources, isolated from each other, one
    at a time (see module docstring for why this is sequential)."""

    return [
        run_source(source, request, entity_refs=entity_refs, timeout_seconds=timeout_seconds)
        for source in request.sources
    ]
