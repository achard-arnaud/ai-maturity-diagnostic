"""Epic 09 S07: first authorized channel adapter, and a manual-send
export for channels a human executes by hand. Stop condition:
"LinkedIn write toujours interdit sans ADR" (LinkedIn write is always
forbidden without an ADR) -- no adapter is ever registered for
`linkedin`, and the registry itself refuses to look one up, so the
categorical prohibition holds at the adapter layer too, not just at
the channel-policy layer (Epic 09 S01).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from app.reach_channel_policy import assert_channel_authorized_to_send
from app.reach_execution import send_touchpoint


class ChannelAdapter(Protocol):
    def send(self, touchpoint: Mapping[str, Any], *, sent_by: str, sent_at: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class EmailAdapter:
    """The first authorized channel adapter: email. Delegates to the
    already-audited send_touchpoint -- it adds no bypass of its own."""

    def send(self, touchpoint: Mapping[str, Any], *, sent_by: str, sent_at: str) -> dict[str, Any]:
        if touchpoint["channel"] != "email":
            raise ValueError(f"EmailAdapter cannot send a {touchpoint['channel']!r} touchpoint")
        return send_touchpoint(touchpoint, sent_by=sent_by, sent_at=sent_at)


@dataclass(frozen=True)
class ManualExportRecord:
    touchpoint_id: str
    channel: str
    content_ref: str
    instructions: str


def build_manual_export(touchpoint: Mapping[str, Any]) -> ManualExportRecord:
    """Produce an export a human executes outside the system (e.g. a
    phone call or a manual outreach step) -- this never itself marks
    the touchpoint sent; a later explicit send_touchpoint call still
    does that once the human confirms the action happened."""
    if touchpoint["channel"] not in ("phone", "manual"):
        raise ValueError(f"manual export is only for phone/manual channels, got {touchpoint['channel']!r}")
    if touchpoint["status"] != "prepared":
        raise ValueError(f"cannot export a touchpoint in status={touchpoint['status']!r}")
    return ManualExportRecord(
        touchpoint_id=touchpoint["touchpoint_id"],
        channel=touchpoint["channel"],
        content_ref=touchpoint["content_ref"],
        instructions=f"Execute this {touchpoint['channel']} touchpoint by hand, then confirm it as sent.",
    )


_ADAPTERS: dict[str, ChannelAdapter] = {"email": EmailAdapter()}


def get_adapter(channel: str) -> ChannelAdapter:
    """The sole lookup point for a sendable channel adapter. Always
    re-checks channel authorization first -- LinkedIn is never
    registered here, and asking for it raises the same
    ChannelNotAuthorizedError as the channel-policy layer, never a bare
    KeyError that could be mistaken for a config gap."""
    assert_channel_authorized_to_send(channel)
    if channel not in _ADAPTERS:
        raise ValueError(f"no adapter registered for authorized channel {channel!r} -- use build_manual_export instead")
    return _ADAPTERS[channel]
