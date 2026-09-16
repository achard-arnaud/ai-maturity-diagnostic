"""Epic 09 S04: local scheduler, quotas, and time windows.

Stop condition: "degraded mode actif" (degraded mode active) -- when a
send would exceed a channel's quota, or falls outside its allowed
time window, the scheduler must never silently drop or force the send:
it enters an explicit, visible degraded mode and defers the attempt,
never pretending things are normal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

DEFAULT_TIME_WINDOWS: dict[str, tuple[int, int]] = {
    "email": (7, 19),
    "phone": (9, 18),
    "manual": (0, 24),
}


class ReachSchedulerError(Exception):
    pass


@dataclass(frozen=True)
class ScheduleDecision:
    allowed: bool
    degraded: bool
    reason: str | None


def is_within_time_window(channel: str, *, hour: int, windows: Mapping[str, tuple[int, int]] | None = None) -> bool:
    windows = windows if windows is not None else DEFAULT_TIME_WINDOWS
    if channel not in windows:
        raise ReachSchedulerError(f"no time window configured for channel {channel!r}")
    start, end = windows[channel]
    return start <= hour < end


def count_sent_today(channel: str, sent_events: Sequence[Mapping[str, Any]], *, today: str) -> int:
    return sum(1 for e in sent_events if e["channel"] == channel and e["sent_at"].startswith(today))


def evaluate_schedule(
    channel: str,
    *,
    hour: int,
    today: str,
    sent_events: Sequence[Mapping[str, Any]],
    daily_quota: int,
    windows: Mapping[str, tuple[int, int]] | None = None,
) -> ScheduleDecision:
    """The sole choke point for whether a send may proceed now. Never
    forces a send through a closed window or a spent quota -- either
    condition puts the scheduler into degraded mode (allowed=False,
    degraded=True) rather than silently dropping or bypassing."""
    if not is_within_time_window(channel, hour=hour, windows=windows):
        return ScheduleDecision(allowed=False, degraded=True, reason="outside_time_window")
    sent_today = count_sent_today(channel, sent_events, today=today)
    if sent_today >= daily_quota:
        return ScheduleDecision(allowed=False, degraded=True, reason="quota_exhausted")
    return ScheduleDecision(allowed=True, degraded=False, reason=None)


def is_degraded_mode_active(decisions: Sequence[ScheduleDecision]) -> bool:
    return any(d.degraded for d in decisions)
