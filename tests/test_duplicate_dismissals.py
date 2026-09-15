from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core import ControlPlaneError
from app.duplicate_dismissals import dismiss_duplicate_group, list_dismissals, list_dismissed_group_keys


class DuplicateDismissalsTests(unittest.TestCase):
    def test_dismiss_records_group_key_and_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = dismiss_duplicate_group(root, ["PERS-2", "PERS-1"], actor="rep@acme.com")
            self.assertTrue(record["group_key"])
            self.assertEqual(["PERS-1", "PERS-2"], record["person_ids"])
            self.assertEqual("rep@acme.com", record["actor"])
            self.assertTrue(record["dismissed_at"])

    def test_group_key_is_independent_of_person_id_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="rep@acme.com")
            b = dismiss_duplicate_group(root, ["PERS-2", "PERS-1"], actor="rep@acme.com")
            self.assertEqual(a["group_key"], b["group_key"])

    def test_dismiss_is_idempotent_and_does_not_duplicate_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="rep@acme.com")
            dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="someone-else@acme.com", reason="checked again")
            records = list_dismissals(root)
            self.assertEqual(1, len(records))
            self.assertEqual("someone-else@acme.com", records[0]["actor"])
            self.assertEqual("checked again", records[0]["reason"])

    def test_list_dismissed_group_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="rep@acme.com")
            self.assertIn(record["group_key"], list_dismissed_group_keys(root))

    def test_missing_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ControlPlaneError):
                dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="")

    def test_fewer_than_two_person_ids_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ControlPlaneError):
                dismiss_duplicate_group(root, ["PERS-1"], actor="rep@acme.com")

    def test_no_dismissals_yields_empty_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(set(), list_dismissed_group_keys(root))
            self.assertEqual([], list_dismissals(root))


if __name__ == "__main__":
    unittest.main()
