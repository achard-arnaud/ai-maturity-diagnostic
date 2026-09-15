from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.blocker_actions import STEP_ORDER, BlockerActionLog
from app.core import ControlPlaneError


class BlockerActionLogTests(unittest.TestCase):
    def test_cancel_records_actor_timestamp_and_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = BlockerActionLog(root)
            entry = log.record(study_id="acme-1", step_id="matching", action="cancel", actor="francois.arnaud.rjc@gmail.com")
            self.assertEqual("cancel", entry["action"])
            self.assertEqual("matching", entry["step_id"])
            self.assertEqual("francois.arnaud.rjc@gmail.com", entry["actor"])
            self.assertIn("timestamp", entry)
            rows = log.list_actions("acme-1")
            self.assertEqual(1, len(rows))
            self.assertEqual(entry, rows[0])

    def test_force_requires_a_mandatory_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="force", actor="a@b.com")
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="force", actor="a@b.com", reason="   ")

    def test_force_with_reason_is_logged_with_actor_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            entry = log.record(study_id="acme-1", step_id="matching", action="force", actor="a@b.com", reason="Client contract deadline")
            self.assertEqual("force", entry["action"])
            self.assertEqual("Client contract deadline", entry["reason"])
            self.assertEqual("a@b.com", entry["actor"])
            self.assertIn("timestamp", entry)

    def test_step_back_requires_a_target_earlier_in_the_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            entry = log.record(study_id="acme-1", step_id="reach", action="step_back", actor="a@b.com", target_step_id="matching")
            self.assertEqual("step_back", entry["action"])
            self.assertEqual("matching", entry["target_step_id"])
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="step_back", actor="a@b.com", target_step_id="reach")
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="step_back", actor="a@b.com")

    def test_unknown_step_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="not-a-step", action="cancel", actor="a@b.com")

    def test_unknown_action_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="teleport", actor="a@b.com")

    def test_actor_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            with self.assertRaises(ControlPlaneError):
                log.record(study_id="acme-1", step_id="matching", action="cancel", actor="  ")

    def test_actions_persist_across_log_instances_and_are_scoped_per_study(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BlockerActionLog(root).record(study_id="acme-1", step_id="matching", action="cancel", actor="a@b.com")
            BlockerActionLog(root).record(study_id="other-1", step_id="matching", action="cancel", actor="a@b.com")
            rows = BlockerActionLog(root).list_actions("acme-1")
            self.assertEqual(1, len(rows))
            self.assertEqual("acme-1", rows[0]["study_id"])

    def test_step_order_is_the_qualification_pipeline(self) -> None:
        self.assertEqual(["demand", "snapshots", "matching", "contacts", "reach", "pilot"], STEP_ORDER)

    def test_list_actions_with_no_study_id_lists_across_all_studies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = BlockerActionLog(root)
            log.record(study_id="acme-1", step_id="matching", action="cancel", actor="a@b.com")
            log.record(study_id="other-1", step_id="reach", action="force", actor="a@b.com", reason="deadline")
            rows = log.list_actions()
            self.assertEqual(2, len(rows))
            self.assertEqual({"acme-1", "other-1"}, {row["study_id"] for row in rows})

    def test_list_actions_filters_by_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = BlockerActionLog(root)
            log.record(study_id="acme-1", step_id="matching", action="cancel", actor="a@b.com")
            log.record(study_id="acme-1", step_id="reach", action="force", actor="a@b.com", reason="deadline")
            rows = log.list_actions("acme-1", action="force")
            self.assertEqual(1, len(rows))
            self.assertEqual("force", rows[0]["action"])

    def test_list_actions_filters_by_step_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = BlockerActionLog(root)
            log.record(study_id="acme-1", step_id="matching", action="cancel", actor="a@b.com")
            log.record(study_id="acme-1", step_id="reach", action="cancel", actor="a@b.com")
            rows = log.list_actions("acme-1", step_id="reach")
            self.assertEqual(1, len(rows))
            self.assertEqual("reach", rows[0]["step_id"])

    def test_list_actions_filters_by_since_and_until(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = BlockerActionLog(root)
            entry = log.record(study_id="acme-1", step_id="matching", action="cancel", actor="a@b.com")
            timestamp = entry["timestamp"]
            self.assertEqual(1, len(log.list_actions("acme-1", since=timestamp)))
            self.assertEqual(1, len(log.list_actions("acme-1", until=timestamp)))
            self.assertEqual(0, len(log.list_actions("acme-1", since="9999-01-01T00:00:00+00:00")))
            self.assertEqual(0, len(log.list_actions("acme-1", until="0001-01-01T00:00:00+00:00")))

    def test_list_actions_with_no_recorded_actions_and_no_filters_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = BlockerActionLog(Path(tmp))
            self.assertEqual([], log.list_actions())
            self.assertEqual([], log.list_actions("unknown-study"))


if __name__ == "__main__":
    unittest.main()
