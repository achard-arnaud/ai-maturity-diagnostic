from __future__ import annotations

import unittest

from app.reach_channel_policy import (
    ChannelNotAuthorizedError,
    ImplicitSendError,
    assert_channel_authorized_to_send,
    assert_no_implicit_creation_as_sent,
    can_send_via_channel,
)


class NoImplicitSendTests(unittest.TestCase):
    def test_step_created_pending_is_allowed(self) -> None:
        assert_no_implicit_creation_as_sent({"status": "pending"}, record_kind="step")

    def test_step_created_scheduled_is_allowed(self) -> None:
        assert_no_implicit_creation_as_sent({"status": "scheduled"}, record_kind="step")

    def test_step_created_sent_is_rejected(self) -> None:
        with self.assertRaises(ImplicitSendError):
            assert_no_implicit_creation_as_sent({"status": "sent"}, record_kind="step")

    def test_touchpoint_created_prepared_is_allowed(self) -> None:
        assert_no_implicit_creation_as_sent({"status": "prepared"}, record_kind="touchpoint")

    def test_touchpoint_created_sent_is_rejected(self) -> None:
        with self.assertRaises(ImplicitSendError):
            assert_no_implicit_creation_as_sent({"status": "sent"}, record_kind="touchpoint")

    def test_unknown_record_kind_rejected(self) -> None:
        from app.reach_channel_policy import ReachChannelPolicyError

        with self.assertRaises(ReachChannelPolicyError):
            assert_no_implicit_creation_as_sent({"status": "pending"}, record_kind="widget")


class ChannelPolicyTests(unittest.TestCase):
    def test_email_send_allowed(self) -> None:
        self.assertTrue(can_send_via_channel("email"))
        assert_channel_authorized_to_send("email")  # should not raise

    def test_manual_send_allowed(self) -> None:
        self.assertTrue(can_send_via_channel("manual"))

    def test_phone_send_allowed(self) -> None:
        self.assertTrue(can_send_via_channel("phone"))

    def test_linkedin_send_forbidden(self) -> None:
        self.assertFalse(can_send_via_channel("linkedin"))
        with self.assertRaises(ChannelNotAuthorizedError):
            assert_channel_authorized_to_send("linkedin")

    def test_unknown_channel_rejected(self) -> None:
        from app.reach_channel_policy import ReachChannelPolicyError

        with self.assertRaises(ReachChannelPolicyError):
            can_send_via_channel("carrier_pigeon")


if __name__ == "__main__":
    unittest.main()
