"""Epic 14 S03: query orchestration and budgets on top of app.harvest_runner.

Wires app.harvest_runner.run_source() into this repo's own durable/bounded
execution primitives (ADR-011 S3), rather than re-implementing run state,
budgeting or retry logic:

- app.execution_context.correlation_scope() -- one correlation ID per
  harvest run.
- app.execution_policy.BudgetLedger/BudgetEnvelope/Usage -- one workspace-
  scoped call charged per source; BudgetExceeded stops the run (a stop
  condition) rather than silently continuing over budget.
- app.execution_policy.RetryPolicy -- bounded retries for a source that
  timed out (RetryPolicy.decide's own retryable set is timeouts and a
  fixed list of HTTP status codes this layer cannot see inside a generic
  adapter exception; a plain "error" status is therefore surfaced
  immediately rather than retried, since a permanently-broken call would
  otherwise be retried forever with nothing gained). "ok"/"empty" are
  never retried either way -- they are not failures.
- app.run_manager.RunManager -- prepare/start/checkpoint/complete/block/
  fail, so a harvest run is a durable, auditable record, not an
  in-memory-only result.

RunManager.checkpoint() may only be called once per run (started ->
checkpointed is a one-way transition in RUN_STATES) -- this module
checkpoints once, after every source has run, with the full per-source
breakdown, rather than attempting the incremental per-source checkpoint
an earlier design sketch (see docs/research/next-wave/
HARVEST_SEARCH_SOCIAL_NETWORKS.md S4) assumed was possible.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.acquisition_policy import EvidenceCandidate, SearchRequest
from app.execution_context import correlation_scope
from app.execution_policy import BudgetEnvelope, BudgetExceeded, BudgetLedger, RetryPolicy, Usage
from app.harvest_runner import DEFAULT_PER_SOURCE_TIMEOUT_SECONDS, SourceRunResult, run_source
from app.run_manager import RunManager

# Harvest calls carry no LLM token/cost usage of their own -- only calls
# and wall time are metered. max_calls/max_wall_seconds are the only
# dimensions a caller should ever need to tune.
HARVEST_BUDGET_ENVELOPE = BudgetEnvelope(
    max_calls=20,
    max_input_tokens=0,
    max_output_tokens=0,
    max_cost_units=0.0,
    max_wall_seconds=600.0,
)

# ADR-011 S6: one shared wrapper, parameterized by space, not per-space
# copies. This is a recommendation for callers building a SearchRequest,
# not enforced by SearchRequest itself (which only enforces the harder
# "linkedin only from targets" rule).
RECOMMENDED_SOURCES_BY_SPACE: dict[str, tuple[str, ...]] = {
    "discover": ("hackernews", "arxiv", "github", "web", "x"),
    "research": ("youtube", "reddit", "perplexity"),
    "targets": ("linkedin",),
}


def recommended_sources_for_space(space: str) -> tuple[str, ...]:
    try:
        return RECOMMENDED_SOURCES_BY_SPACE[space]
    except KeyError as exc:
        raise ValueError(f"unknown space: {space!r}") from exc


@dataclass(frozen=True)
class HarvestRun:
    run_id: str
    status: str  # "completed" | "blocked" | "failed"
    correlation_id: str
    source_runs: tuple[SourceRunResult, ...]
    candidates: tuple[EvidenceCandidate, ...]


def _checkpoint_payload(source_runs: list[SourceRunResult]) -> dict:
    return {
        "sources": [
            {
                "source": r.source,
                "status": r.status,
                "count": len(r.candidates),
                "elapsed_ms": r.elapsed_ms,
                "error": r.error,
            }
            for r in source_runs
        ]
    }


def run_harvest(
    root: Path,
    workspace_id: str,
    actor_id: str,
    request: SearchRequest,
    *,
    entity_refs: tuple[str, ...] = (),
    envelope: BudgetEnvelope = HARVEST_BUDGET_ENVELOPE,
    retry_policy: RetryPolicy | None = None,
    timeout_seconds: float = DEFAULT_PER_SOURCE_TIMEOUT_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> HarvestRun:
    """Run a bounded, budgeted, retried, durable harvest across
    request.sources for one workspace. Never fans out beyond
    request.sources (SearchRequest already rejects an empty source list --
    S01/S3's "do not fan out to all sources by default")."""

    if request.workspace_id != workspace_id:
        raise ValueError("request.workspace_id must match the caller's workspace_id")
    retry_policy = retry_policy or RetryPolicy()
    run_mgr = RunManager(root=root, workspace_id=workspace_id, actor_id=actor_id)
    ledger = BudgetLedger(root, workspace_id, envelope)

    with correlation_scope() as correlation_id:
        prepared = run_mgr.prepare(
            "harvest.search_social_networks",
            input_ref=request.query,
            metadata={"space": request.space, "sources": list(request.sources), "correlation_id": correlation_id},
        )
        run_id = prepared.run["run_id"]
        run_mgr.start(run_id)

        source_runs: list[SourceRunResult] = []
        blocked_reason: str | None = None

        for source in request.sources:
            try:
                ledger.consume(Usage(calls=1))
            except BudgetExceeded as exc:
                blocked_reason = str(exc)
                break

            attempt = 0
            result: SourceRunResult
            while True:
                attempt += 1
                result = run_source(source, request, entity_refs=entity_refs, timeout_seconds=timeout_seconds)
                if result.status in ("ok", "empty"):
                    break
                decision = retry_policy.decide(attempt=attempt, timed_out=(result.status == "timeout"))
                if not decision.retry:
                    break
                sleep_fn(decision.delay_seconds)
            source_runs.append(result)

        if source_runs:
            run_mgr.checkpoint(run_id, _checkpoint_payload(source_runs))

        candidates = tuple(candidate for r in source_runs for candidate in r.candidates)

        if blocked_reason is not None:
            run_mgr.block(run_id, blocked_reason)
            status = "blocked"
        elif source_runs and all(r.status == "error" for r in source_runs):
            # Every requested source errored -- a systemic acquisition
            # problem (e.g. web_index markup drift), not a legitimately
            # empty result set. Surface as failed, not a quiet "completed"
            # with zero output_refs (ADR-011 S5 blocker mapping).
            run_mgr.fail(run_id, "all_sources_failed", "every requested source returned an error", retryable=True)
            status = "failed"
        else:
            run_mgr.complete(run_id, [candidate.candidate_id for candidate in candidates])
            status = "completed"

        return HarvestRun(
            run_id=run_id,
            status=status,
            correlation_id=correlation_id,
            source_runs=tuple(source_runs),
            candidates=candidates,
        )
