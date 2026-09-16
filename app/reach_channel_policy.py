"""Epic 09 S01: Sequence/Step/Task/Touchpoint channel policies.

Stop condition: "aucun send implicite" (no implicit send) -- a Step or
Touchpoint is always created unsent; only a later, explicit action
(S03) may move it to sent. This module also enforces the channel-level
rule that LinkedIn write access is categorically unavailable without a
dedicated ADR (this Epic's own deferred-work line).
"""

from __future__ import annotations

from typing import Any, Mapping

_NON_SENT_STEP_STATUSES = frozenset({"pending", "scheduled", "skipped", "cancelled"})
_NON_SENT_TOUCHPOINT_STATUSES = frozenset({"prepared", "failed"})

CHANNEL_SEND_ALLOWED: dict[str, bool] = {
    "email": True,
    "phone": True,
    "manual": True,
    "linkedin": False,
}


class ReachChannelPolicyError(Exception):
    pass


class ImplicitSendError(ReachChannelPolicyError):
    pass


class ChannelNotAuthorizedError(ReachChannelPolicyError):
    pass


def assert_no_implicit_creation_as_sent(record: Mapping[str, Any], *, record_kind: str) -> None:
    """Raise if a Step or Touchpoint is being created already marked
    sent -- creation must always start unsent."""
    if record_kind == "step":
        if record["status"] not in _NON_SENT_STEP_STATUSES:
            raise ImplicitSendError(f"a step must be created pending/scheduled, never status={record['status']!r}")
    elif record_kind == "touchpoint":
        if record["status"] not in _NON_SENT_TOUCHPOINT_STATUSES:
            raise ImplicitSendError(
                f"a touchpoint must be created prepared, never status={record['status']!r}"
            )
    else:
        raise ReachChannelPolicyError(f"unknown record_kind {record_kind!r}")


def can_send_via_channel(channel: str) -> bool:
    if channel not in CHANNEL_SEND_ALLOWED:
        raise ReachChannelPolicyError(f"unknown channel {channel!r}")
    return CHANNEL_SEND_ALLOWED[channel]


def assert_channel_authorized_to_send(channel: str) -> None:
    if not can_send_via_channel(channel):
        raise ChannelNotAuthorizedError(
            f"channel {channel!r} is not authorized to send -- LinkedIn write always requires a dedicated ADR"
        )
