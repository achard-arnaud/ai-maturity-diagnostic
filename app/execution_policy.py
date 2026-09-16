"""Budget, cache and retry policy for bounded AI/tool execution."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from app.artifact_store import ArtifactStore


class BudgetExceeded(RuntimeError):
    def __init__(self, dimension: str, limit: float, used: float, requested: float) -> None:
        self.dimension = dimension
        self.limit = limit
        self.used = used
        self.requested = requested
        super().__init__(f"{dimension} budget exceeded: {used} + {requested} > {limit}")


@dataclass(frozen=True)
class BudgetEnvelope:
    max_calls: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_units: float
    max_wall_seconds: float

    def __post_init__(self) -> None:
        for field, value in asdict(self).items():
            if value < 0:
                raise ValueError(f"{field} must be non-negative")


@dataclass(frozen=True)
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: float = 0.0
    wall_seconds: float = 0.0

    def plus(self, other: "Usage") -> "Usage":
        return Usage(**{field: getattr(self, field) + getattr(other, field) for field in asdict(self)})


@dataclass(frozen=True)
class BudgetStatus:
    mode: str
    used: Usage
    limits: BudgetEnvelope
    utilization: float


class BudgetLedger:
    def __init__(self, root: Path, workspace_id: str, envelope: BudgetEnvelope) -> None:
        self.root = root
        self.workspace_id = workspace_id
        self.envelope = envelope
        self.store = ArtifactStore(root)
        self.path = root / "runtime" / "budgets" / f"{workspace_id}.yaml"

    def _load(self, data: bytes) -> Usage:
        if not data:
            return Usage()
        document = yaml.safe_load(data.decode("utf-8")) or {}
        return Usage(**(document.get("used") or {}))

    def _check(self, used: Usage, requested: Usage) -> Usage:
        resulting = used.plus(requested)
        checks = {
            "calls": (self.envelope.max_calls, resulting.calls, requested.calls),
            "input_tokens": (self.envelope.max_input_tokens, resulting.input_tokens, requested.input_tokens),
            "output_tokens": (self.envelope.max_output_tokens, resulting.output_tokens, requested.output_tokens),
            "cost_units": (self.envelope.max_cost_units, resulting.cost_units, requested.cost_units),
            "wall_seconds": (self.envelope.max_wall_seconds, resulting.wall_seconds, requested.wall_seconds),
        }
        for dimension, (limit, value, increment) in checks.items():
            if value > limit:
                raise BudgetExceeded(dimension, float(limit), float(value - increment), float(increment))
        return resulting

    def consume(self, usage: Usage) -> BudgetStatus:
        resulting: Usage | None = None

        def update(previous: bytes) -> bytes:
            nonlocal resulting
            resulting = self._check(self._load(previous), usage)
            document = {
                "schema_version": "1.0",
                "workspace_id": self.workspace_id,
                "limits": asdict(self.envelope),
                "used": asdict(resulting),
            }
            return yaml.safe_dump(document, sort_keys=False).encode("utf-8")

        self.store.update_bytes(self.path, update)
        assert resulting is not None
        return self.status(resulting)

    def status(self, used: Usage | None = None) -> BudgetStatus:
        if used is None:
            current = self.store.read_bytes(self.path)
            used = self._load(current[0]) if current else Usage()
        ratios = [
            (used.calls / self.envelope.max_calls) if self.envelope.max_calls else (1.0 if used.calls else 0.0),
            (used.input_tokens / self.envelope.max_input_tokens)
            if self.envelope.max_input_tokens
            else (1.0 if used.input_tokens else 0.0),
            (used.output_tokens / self.envelope.max_output_tokens)
            if self.envelope.max_output_tokens
            else (1.0 if used.output_tokens else 0.0),
            (used.cost_units / self.envelope.max_cost_units)
            if self.envelope.max_cost_units
            else (1.0 if used.cost_units else 0.0),
            (used.wall_seconds / self.envelope.max_wall_seconds)
            if self.envelope.max_wall_seconds
            else (1.0 if used.wall_seconds else 0.0),
        ]
        utilization = max(ratios)
        mode = "blocked" if utilization >= 1 else "checkpoint_required" if utilization >= 0.8 else "normal"
        return BudgetStatus(mode, used, self.envelope, utilization)


def cache_key(*, provider: str, model: str, prompt_version: str, policy_version: str, payload: Any) -> str:
    document = {
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
        "policy_version": policy_version,
        "payload": payload,
    }
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    delay_seconds: float
    reason: str


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter_ratio: float = 0.2

    def decide(
        self,
        *,
        attempt: int,
        status_code: int | None = None,
        timed_out: bool = False,
        retry_after_seconds: float | None = None,
        random_value: float | None = None,
    ) -> RetryDecision:
        retryable = timed_out or status_code in {408, 425, 429, 500, 502, 503, 504}
        if not retryable:
            return RetryDecision(False, 0.0, "non_retryable")
        if attempt >= self.max_attempts:
            return RetryDecision(False, 0.0, "attempt_limit")
        if retry_after_seconds is not None:
            delay = min(max(0.0, retry_after_seconds), self.max_delay_seconds)
            return RetryDecision(True, delay, "retry_after")
        base = min(self.base_delay_seconds * (2 ** max(0, attempt - 1)), self.max_delay_seconds)
        sample = random.random() if random_value is None else random_value
        jitter = base * self.jitter_ratio * ((sample * 2) - 1)
        return RetryDecision(True, max(0.0, min(base + jitter, self.max_delay_seconds)), "backoff")
