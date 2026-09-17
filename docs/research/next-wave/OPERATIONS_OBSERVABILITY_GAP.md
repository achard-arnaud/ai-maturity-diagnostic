# Operations / observability gap audit — candidate Epic E20

Status: **research and proposal only**. No runtime code was written or
modified to produce this document.

Source read in full: `app/event_journal.py`, `app/execution_context.py`,
`app/run_manager.py`, `app/execution_policy.py`, `app/insights_routes.py`,
`app/insights_metrics.py`/`app/insights_projection.py` (read for the
metric-catalog/projection shape), the `_log_requests` middleware and the
exception handlers in `app/server.py`. Cross-checked with a repo-wide grep
for third-party observability tooling (Prometheus/Sentry/OpenTelemetry/
StatsD/Datadog) and for every call site of `RunManager` and `EventJournal`.

The brief requires these to be treated as **separate concepts**:
ApplicationLog, SecurityLog, AuditEvent, BusinessEvent, AgentTrace,
RunTrace, Metric, Error. Section headers below map to those terms directly
so the mapping (and the gaps) are unambiguous.

---

## 1. What already exists, mapped onto the eight concepts

| Concept | What plays this role today | File | Verdict |
| --- | --- | --- | --- |
| **BusinessEvent** | `EventJournal` — append-only, hash-chained JSONL (`events/platform.jsonl`), free-form `event_type`, `workspace_id`, `actor_id`, `correlation_id`, `object_ref`, `data` | `app/event_journal.py` | **Exists, and is good.** Used by `run_manager.py`, `insights_routes.py` (via projection), `learning_proposals.py`, `fit_lifecycle.py`, `product_workflow.py`, `research_review.py`, `signal_handoff.py`. This is the E01-S03 primitive and it is genuinely the right shape for BusinessEvent: idempotent, hash-chained (tamper-evident), correlation-ID-tagged. |
| **AuditEvent** | **Split across two unrelated stores — see §2.** | `app/event_journal.py` (business-object events) and `app/authruntime/db.py`'s `audit_events` SQLite table (auth/admin actions) | **Partial, and fragmented.** Neither store alone is "the" audit log; see §2 for why this matters. |
| **SecurityLog** | Nothing distinct exists. `authruntime.db.record_audit` captures `login`, `create_workspace`, `set_membership`, `qualification_override`, `resolve_override` — but there is no record of *denied* access (401/403), no record of a cross-workspace probe being blocked, no record of a session being revoked, no record of a failed login attempt. | — | **Gap.** ADR-007's own security invariants list "Cross-workspace access attempts are observable security events" as a requirement; nothing currently emits an event when `require_workspace_access` returns 404 for a mismatched workspace, or when `require_role` returns 403. Today those events are *observable only in the generic HTTP access log* (`_log_requests`, §3) as a bare status code with no security semantics attached — indistinguishable from a client typo. |
| **RunTrace** | `RunManager` — durable, resumable per-run state machine (`prepared → started → checkpointed → completed/blocked/failed/cancelled`), YAML-persisted under `runtime/runs/<run_id>.yaml`, every transition also appended to `EventJournal` as `run.<status>` | `app/run_manager.py` | **Exists and is well-designed** (resume tokens, idempotency keys, retryable-vs-not failure classification) but **is currently used only by `app/research_orchestration.py`** — confirmed by grepping every call site of `RunManager(` in `app/`. No other business module (catalog harvest, nudging, campaigns, skill invocation) goes through it, so most of the platform's actual execution has no RunTrace coverage at all. |
| **AgentTrace** | Nothing distinct exists. `RunManager` traces a *run* (a business capability invocation), not the individual tool/skill calls an agent makes within it — there is no per-tool-call record (which skill, which model/executor, input/output size, latency, retry count) anywhere in the codebase. `POST /api/skills/{skill_id}/invoke` (`server.py`) calls into `CONTROL`'s skill executor with no tracing wrapper visible in `app/core.py`'s skill-invocation path beyond whatever the generic request log captures. | — | **Gap.** This is the one concept from the brief's list with no code-level candidate at all, not even a partial one. |
| **ApplicationLog** | `_log_requests` middleware — one structured JSON line per HTTP request to stdout | `app/server.py:124-150` | **Exists, but thin.** See §3 for exactly what it does and does not capture. |
| **Metric** | `BudgetLedger`/`Usage` (calls, tokens, cost_units, wall_seconds) per workspace, persisted to YAML under `runtime/budgets/<workspace_id>.yaml`; separately, `app/insights_metrics.py`'s `metric_catalog()` + `build_projection()` compute funnel/quality/cost aggregates **from BusinessEvents**, not from BudgetLedger. | `app/execution_policy.py`, `app/insights_metrics.py`/`insights_projection.py` | **Two disjoint metric systems, neither operator-facing.** See §4 and §5. |
| **Error** | Only Python's standard `logging.exception(...)` inside the global FastAPI exception handler, to whatever the default (unconfigured) root logger does — see §6. No structured error record, no correlation to `EventJournal`, no error store, no admin page. | `app/server.py:218-221` | **Gap.** |

## 2. AuditEvent is fragmented across two independent stores

`app/authruntime/db.py`'s `audit_events` table (SQLite, `record_audit`/
`list_audit`, surfaced at `/admin/audit`) and `app/event_journal.py`'s
hash-chained JSONL are **both plausible "AuditEvent" candidates and neither
subsumes the other**:

- The SQLite table captures auth/admin-plane actions (`login`,
  `create_workspace`, `set_membership`, `qualification_override`,
  `resolve_override`) with a simple `(actor, action, target, reason,
  timestamp)` shape, no hash chain, no tamper-evidence, no
  `correlation_id`.
- `EventJournal` captures business-plane state transitions (run lifecycle,
  fit/product/research/signal handoffs, learning-proposal transitions) with
  a hash chain, idempotency keys and correlation IDs — a materially
  stronger integrity guarantee, but it never records auth/admin actions.

An admin resolving a qualification override, for instance, is written only
to the SQLite `audit_events` table via `record_audit` — it is *not* a
hash-chained, tamper-evident record, unlike a `fit.decided` or
`demand.created` event next door in `EventJournal`. Whether that asymmetry
is acceptable (auth-plane audit doesn't need hash-chaining; business-plane
does) or an oversight (both should have the same integrity guarantee) is
exactly the kind of question E20 should settle explicitly rather than
leave as an accident of which module a given action happened to be
implemented in.

## 3. ApplicationLog: what `_log_requests` actually logs, and where it goes

`app/server.py:124-150` is FastAPI HTTP middleware wrapping every request in
`correlation_scope(request_id)` and emitting one JSON line **to stdout**
via a dedicated `logging.getLogger("app.request")` with `propagate=False`
(so it never reaches the root logger or the exception handler's logger —
these are two independent logging paths that never merge). The line
contains exactly: `timestamp`, `request_id`, `method`, `path`, `status`,
`duration_ms`. It is genuinely structured (real JSON, not printf), and the
comment above it is explicit and correct that it deliberately excludes
body, cookies, `Authorization`, and query string, per ADR-007's
"tokens/cookies/secrets ... redacted from logs" invariant.

What it does **not** capture, which matters for an operator: the
authenticated `user_id`/`workspace_id` for the request (so a log line
cannot be tied to "which workspace was this for" without cross-referencing
something else), the response body size, and — critically — it has **no
sink beyond stdout**. There is no log rotation, no shipping to a log
aggregator, no retention policy, and no query interface; "where does it go"
is answered literally as "wherever the process's stdout is captured by
whatever supervises it," which today means an operator's only way to see
these lines is to already have shell/log access to the running process.
There is no `/admin/*` page that surfaces even this minimal request log.

## 4. Metric, part 1: `BudgetLedger` (cost/usage governance) has no operator-facing surface

`app/execution_policy.py`'s `BudgetLedger` tracks `Usage(calls,
input_tokens, output_tokens, cost_units, wall_seconds)` per workspace
against a `BudgetEnvelope`, computing a `BudgetStatus.mode ∈ {normal,
checkpoint_required, blocked}` once utilization crosses configured
thresholds. This is a real, working cost/rate-governance mechanism. **But
its state (`runtime/budgets/<workspace_id>.yaml`) is never read by any
route, admin page, or the Insights space.** There is no way for an operator
or a workspace's own product_owner to see "how much of this workspace's
budget has been consumed this period" without opening the raw YAML file on
disk. This is precisely the brief's "buried in raw JSONL/YAML files nobody
has a UI for" pattern, confirmed at the code level: the enforcement exists,
the visibility does not.

## 5. Metric, part 2: Insights (E13) is a *different, business-metric* concern from operational observability — and that distinction matters for scoping E20

`app/insights_routes.py`'s `GET /api/v1/workspaces/{workspace_id}/insights`
builds a `CohortPolicy`-scoped projection **over `EventJournal.replay()`**
(`insights_routes.py:38-40`) — i.e., it aggregates *BusinessEvents*
(funnel stage transitions, fit/demand/product events) into cohort metrics
like conversion and quality, with an explicit privacy floor (`MINIMUM_COHORT_SIZE
= 3`, results suppressed below it). This is GTM/product analytics:
"how is the funnel performing," "what does this cohort's fit-to-pipeline
conversion look like" — a business-outcome question.

**Operational observability asks a structurally different question:** "is
the system itself healthy" — request error rates, run failure/retry counts,
budget exhaustion events, which sources/skills are degrading, p50/p95
latency, how many `BudgetExceeded` or `RunStateError` occurrences happened
in the last hour. Nothing in `app/insights_routes.py` or
`app/insights_metrics.py` computes any of this, and nothing should be added
there to do so — Insights' event source (`EventJournal`, business events
only), its privacy-suppression floor (designed for cohort analytics, not
operational alerting, where you *want* to see a single failing run
immediately, not suppress it below a cohort-size-3 threshold), and its
audience (product/GTM decision-makers) are all wrong for an ops surface.

**Scoping guidance for E20 vs E13:** E20 should be scoped as its own
surface reading from `_log_requests`' output, `RunManager`'s run records,
`BudgetLedger`'s per-workspace usage, and (once built) the SecurityLog/
AgentTrace/Error gaps above — never by extending
`insights_routes.py`/`insights_projection.py`, and never by lowering or
removing the privacy-suppression floor those business metrics correctly
apply. If a single admin-facing page ends up showing both, it should
compose two independently-owned data sources, not merge them into one
query — matching this codebase's own repeated architectural rule (seen
throughout `docs/gtm-transformation/02_DOMAIN_AND_TRUTH_MODEL.md`) that
each bounded context owns one truth and other contexts consume it, never
re-derive it.

## 6. Error: no structured error record, and a real gap in where exceptions actually go

`app/server.py:218-221`'s catch-all exception handler calls
`logging.getLogger(__name__).exception(...)` — this uses the **default,
unconfigured root logger** (no `logging.basicConfig()` call was found
anywhere in `app/`), which means the traceback goes wherever Python's
default "handler of last resort" sends it (stderr, at WARNING+), **not**
to the same stdout stream or JSON structure `_REQUEST_LOG` uses, and
**not** correlated with the `request_id` that `_log_requests` already
generated for that same request via `correlation_scope`. An operator
grepping the structured access log for a `status: 500` line has no
mechanical way to find the matching traceback beyond timestamp-proximity
guessing, because the two never share a request ID in their output.
There is no error store, no `/admin/*` error page, and no count of
"how many 500s in the last hour" anywhere.

## 7. AgentTrace: the one concept with genuinely nothing built

`RunTrace` (`RunManager`) traces a business-capability run as a whole
(prepare → start → checkpoint → complete), which is the right granularity
for "did this ResearchCase orchestration finish." It is not, and was never
meant to be, a trace of the individual tool/skill/model calls *inside* that
run. Nothing in the codebase — not `run_manager.py`, not `execution_context.py`,
not the skill-invocation path reachable from `POST
/api/skills/{skill_id}/invoke` — records per-call agent activity: which
skill ran, against what input, which executor/model handled it, how long it
took, whether it retried, or what it returned. This is the one item from
the brief's eight-concept list with no partial implementation to build on;
E20 would need to design this from scratch, most naturally as a new event
family appended to the existing `EventJournal` (reusing its hash-chain and
correlation-ID machinery rather than inventing a fourth store) keyed under
the `RunManager` run that invoked it, so a single run's trace is
"one `run.*` lifecycle event stream plus its child `agent.tool_call`
events," not a fifth independent log.

## 8. Is there any operator-facing surface at all today?

**No**, beyond the two admin pages that exist for unrelated reasons:
`/admin/audit` (the SQLite `audit_events` table — auth/admin actions only,
§2) and `/admin/overrides` (the qualification-override approval inbox —
a business-workflow queue, not an ops dashboard). Neither shows failures,
retries, rate-limit/budget state, run health, or error rates. Every signal
this document found (`_REQUEST_LOG`'s JSON lines, `RunManager`'s YAML run
records, `BudgetLedger`'s YAML usage files, whatever the unconfigured root
logger does with tracebacks) is either stdout-only or a raw file on disk
with no admin page reading it — exactly the "buried in raw JSONL files
nobody has a UI for" pattern the brief asked this audit to check for,
confirmed across every one of these sources independently.

---

## Summary for E20 scoping

| Concept | Exists today? | Where | Gap to close |
| --- | --- | --- | --- |
| BusinessEvent | Yes, solid | `EventJournal` | None — reuse, don't rebuild |
| AuditEvent | Partial, fragmented | `EventJournal` (business) + `authruntime.db.audit_events` (auth) | Decide whether these should share one integrity model |
| SecurityLog | No | — | Emit events on 401/403/cross-workspace-404/session-revocation |
| RunTrace | Yes, underused | `RunManager` | Wire more business capabilities through it, not just research orchestration |
| AgentTrace | No | — | Design from scratch, as a child event family under RunTrace's run, reusing `EventJournal` |
| ApplicationLog | Yes, thin | `_log_requests` | Add user/workspace context; give it a real sink and a viewer |
| Metric (cost/budget) | Yes, invisible | `BudgetLedger` | Surface it in an admin page; today it's enforcement with no visibility |
| Metric (business) | Yes, and it's E13's, not E20's | `insights_routes.py` | Keep separate — do not fold ops metrics into Insights or its privacy floor |
| Error | No | — | Structured error record correlated to `request_id`; a real logging config |
| Operator surface | No | — | The actual E20 deliverable: one admin page composing the above |

**This document is a proposal for the architecture owner's E20 scoping
decision, not authorization to build.** Every finding above is a research
input; no runtime code, schema, event type, or admin page should be built
on the basis of this document alone until the architecture owner has
reviewed and ratified a scope for E20.
