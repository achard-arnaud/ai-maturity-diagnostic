"""Signal schema loading, dedup, freshness and lifecycle policy (Epic 03 S01).

The one invariant this Epic must never let slip: a signal never becomes,
or is silently read as, proof of demand. Two mechanisms enforce that here:

1. contracts/signal_v1.schema.yaml has additionalProperties: false and
   deliberately excludes every demand-only field (problem, sponsor,
   budget, urgency, timing, initiative...). A signal literally cannot
   carry those fields and validate.
2. assert_no_demand_fields() is a second, defense-in-depth guard for any
   caller building a signal dict by hand (e.g. an ingestion adapter,
   Epic 03 S02) before it ever reaches schema validation -- so a
   programming error is caught immediately with a clear message, not a
   generic schema validation error three layers away.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"

DEMAND_ONLY_FIELDS = frozenset(
    {
        "problem",
        "population",
        "impact",
        "urgency",
        "sponsor",
        "budget",
        "timing",
        "initiative",
    }
)

_TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"reviewed", "expired"}),
    "reviewed": frozenset({"linked", "dismissed", "expired"}),
    "linked": frozenset({"expired"}),
    "dismissed": frozenset(),
    "expired": frozenset(),
}


class SignalPolicyError(RuntimeError):
    pass


def load_signal_schema() -> dict[str, Any]:
    path = CONTRACTS_ROOT / "signal_v1.schema.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def assert_no_demand_fields(candidate: dict[str, Any]) -> None:
    """Raise if a signal-shaped dict carries any demand-only field."""

    found = DEMAND_ONLY_FIELDS & candidate.keys()
    if found:
        raise SignalPolicyError(
            f"signal payload carries demand-only field(s) {sorted(found)} -- "
            "a signal never proves demand (see contracts/signal_v1.schema.yaml x-rules)"
        )


def compute_dedup_key(source_kind: str, source_ref: str, content: str) -> str:
    """Deterministic dedup key for a signal, independent of which
    ingestion adapter (public/manual/import) observed it. Two adapters
    that saw the exact same underlying source+content produce the same
    key, so downstream dedup (Epic 03 S02/S03) doesn't need to know which
    adapter ran.
    """

    if not source_kind or not source_ref:
        raise SignalPolicyError("dedup key requires a non-empty source kind and ref")
    digest = hashlib.sha256(f"{source_kind}::{source_ref}::{content}".encode("utf-8")).hexdigest()
    return f"sig_{digest[:24]}"


def is_expired(signal: dict[str, Any], *, as_of: datetime | None = None) -> bool:
    """A signal is expired once its freshness window has elapsed, measured
    from observed_at -- independent of its current status (a "linked"
    signal can still go stale; that doesn't retroactively invalidate the
    link, but it does mean the signal itself should no longer be treated
    as a fresh prioritization input).
    """

    as_of = as_of or datetime.now(timezone.utc)
    observed_at = datetime.fromisoformat(signal["observed_at"])
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    stale_after_days = signal["freshness"]["stale_after_days"]
    age_days = (as_of - observed_at).total_seconds() / 86400
    return age_days > stale_after_days


def can_transition(from_status: str, to_status: str) -> bool:
    """Whether a signal lifecycle transition is legal.

    new -> reviewed -> {linked, dismissed}; any non-terminal status can
    also transition to expired (freshness-driven, not a human decision);
    dismissed and expired are terminal.
    """

    if from_status not in _TRANSITIONS:
        raise SignalPolicyError(f"unknown signal status: {from_status}")
    if to_status not in _TRANSITIONS:
        raise SignalPolicyError(f"unknown signal status: {to_status}")
    return to_status in _TRANSITIONS[from_status]
