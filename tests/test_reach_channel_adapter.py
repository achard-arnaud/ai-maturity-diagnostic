from __future__ import annotations

import unittest

from app.reach_channel_adapter import (
    EmailAdapter,
    build_manual_export,
    get_adapter,
)
from app.reach_channel_policy import ChannelNotAuthorizedError


def _touchpoint(channel: str, status: str = "prepared") -> dict:
    return {
        "touchpoint_id": "tp1", "step_id": "s1", "channel": channel, "content_ref": "msg-1",
        "status": status, "sent_at": None, "sent_by": None,
    }


class EmailAdapterTests(unittest.TestCase):
    def test_sends_an_email_touchpoint(self) -> None:
        sent = EmailAdapter().send(_touchpoint("email"), sent_by="alice", sent_at="2026-01-03T00:00:00Z")
        self.assertEqual("sent", sent["status"])
        self.assertEqual("alice", sent["sent_by"])

    def test_refuses_a_non_email_touchpoint(self) -> None:
        with self.assertRaises(ValueError):
            EmailAdapter().send(_touchpoint("phone"), sent_by="alice", sent_at="2026-01-03T00:00:00Z")


class GetAdapterTests(unittest.TestCase):
    def test_email_adapter_available(self) -> None:
        adapter = get_adapter("email")
        self.assertIsInstance(adapter, EmailAdapter)

    def test_linkedin_adapter_never_registered_and_raises(self) -> None:
        with self.assertRaises(ChannelNotAuthorizedError):
            get_adapter("linkedin")

    def test_phone_has_no_adapter_use_manual_export_instead(self) -> None:
        with self.assertRaises(ValueError):
            get_adapter("phone")


class ManualExportTests(unittest.TestCase):
    def test_builds_export_for_phone_touchpoint(self) -> None:
        record = build_manual_export(_touchpoint("phone"))
        self.assertEqual("tp1", record.touchpoint_id)
        self.assertEqual("phone", record.channel)

    def test_builds_export_for_manual_touchpoint(self) -> None:
        record = build_manual_export(_touchpoint("manual"))
        self.assertEqual("manual", record.channel)

    def test_refuses_email_channel(self) -> None:
        with self.assertRaises(ValueError):
            build_manual_export(_touchpoint("email"))

    def test_refuses_linkedin_channel(self) -> None:
        with self.assertRaises(ValueError):
            build_manual_export(_touchpoint("linkedin"))

    def test_refuses_a_non_prepared_touchpoint(self) -> None:
        with self.assertRaises(ValueError):
            build_manual_export(_touchpoint("phone", status="sent"))

    def test_export_never_marks_the_touchpoint_sent(self) -> None:
        touchpoint = _touchpoint("phone")
        build_manual_export(touchpoint)
        self.assertEqual("prepared", touchpoint["status"])


if __name__ == "__main__":
    unittest.main()
