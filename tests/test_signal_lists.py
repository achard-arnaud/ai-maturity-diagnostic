from __future__ import annotations

import unittest

from app.signal_lists import (
    SignalListError,
    create_list,
    create_watchlist,
    materialize_smart_list,
    matches_criteria,
    run_saved_search,
    update_list_members,
)


def _signal(signal_id: str, *, source_kind: str = "public", status: str = "new", workspace_id: str = "ws-a") -> dict:
    return {
        "signal_id": signal_id,
        "workspace_id": workspace_id,
        "source": {"kind": source_kind, "ref": "ref"},
        "status": status,
    }


class SavedSearchTests(unittest.TestCase):
    def test_matches_on_single_criterion(self) -> None:
        self.assertTrue(matches_criteria(_signal("s1", source_kind="public"), {"source_kind": "public"}))
        self.assertFalse(matches_criteria(_signal("s1", source_kind="manual"), {"source_kind": "public"}))

    def test_criteria_are_and_ed(self) -> None:
        signal = _signal("s1", source_kind="public", status="new")
        self.assertTrue(matches_criteria(signal, {"source_kind": "public", "status": "new"}))
        self.assertFalse(matches_criteria(signal, {"source_kind": "public", "status": "reviewed"}))

    def test_unknown_criterion_key_raises(self) -> None:
        with self.assertRaises(SignalListError):
            matches_criteria(_signal("s1"), {"bogus_field": "x"})

    def test_run_saved_search_is_deterministic_regardless_of_input_order(self) -> None:
        signals_order_a = [_signal("s3"), _signal("s1"), _signal("s2")]
        signals_order_b = [_signal("s1"), _signal("s2"), _signal("s3")]
        result_a = run_saved_search(signals_order_a, {"source_kind": "public"})
        result_b = run_saved_search(signals_order_b, {"source_kind": "public"})
        self.assertEqual([s["signal_id"] for s in result_a], [s["signal_id"] for s in result_b])
        self.assertEqual(["s1", "s2", "s3"], [s["signal_id"] for s in result_a])

    def test_non_matching_signals_are_excluded(self) -> None:
        signals = [_signal("s1", source_kind="public"), _signal("s2", source_kind="manual")]
        result = run_saved_search(signals, {"source_kind": "public"})
        self.assertEqual(["s1"], [s["signal_id"] for s in result])


class ListVersioningTests(unittest.TestCase):
    def test_new_list_starts_at_version_1(self) -> None:
        lst = create_list("list-1", "ws-a", member_ids=["s1", "s2"])
        self.assertEqual(1, lst.version)
        self.assertEqual(("s1", "s2"), lst.member_ids)

    def test_updating_members_increments_version_and_does_not_mutate_original(self) -> None:
        original = create_list("list-1", "ws-a", member_ids=["s1"])
        updated = update_list_members(original, ["s1", "s2"])
        self.assertEqual(1, original.version)
        self.assertEqual(("s1",), original.member_ids)
        self.assertEqual(2, updated.version)
        self.assertEqual(("s1", "s2"), updated.member_ids)

    def test_members_are_deduplicated_and_sorted(self) -> None:
        lst = create_list("list-1", "ws-a", member_ids=["s2", "s1", "s2"])
        self.assertEqual(("s1", "s2"), lst.member_ids)

    def test_cannot_update_members_of_a_smart_list_directly(self) -> None:
        smart = materialize_smart_list(None, "sl-1", "ws-a", {"source_kind": "public"}, [_signal("s1")])
        with self.assertRaises(SignalListError):
            update_list_members(smart, ["s2"])


class WatchlistTests(unittest.TestCase):
    def test_watchlist_is_a_versioned_list_of_company_entity_ids(self) -> None:
        watchlist = create_watchlist("wl-1", "ws-a", company_entity_ids=["entity_1", "entity_2"])
        self.assertEqual("watchlist", watchlist.kind)
        self.assertEqual(1, watchlist.version)
        self.assertEqual(("entity_1", "entity_2"), watchlist.member_ids)


class SmartListTests(unittest.TestCase):
    def test_first_materialization_is_version_1(self) -> None:
        smart = materialize_smart_list(None, "sl-1", "ws-a", {"status": "new"}, [_signal("s1"), _signal("s2", status="reviewed")])
        self.assertEqual(1, smart.version)
        self.assertEqual(("s1",), smart.member_ids)

    def test_rematerializing_against_unchanged_signals_reproduces_same_membership(self) -> None:
        signals = [_signal("s1"), _signal("s2", status="reviewed")]
        first = materialize_smart_list(None, "sl-1", "ws-a", {"status": "new"}, signals)
        second = materialize_smart_list(first, "sl-1", "ws-a", {"status": "new"}, signals)
        self.assertEqual(first.member_ids, second.member_ids)
        self.assertEqual(2, second.version)

    def test_rematerializing_after_signal_change_updates_membership(self) -> None:
        signals = [_signal("s1", status="new")]
        first = materialize_smart_list(None, "sl-1", "ws-a", {"status": "new"}, signals)
        signals[0]["status"] = "reviewed"
        second = materialize_smart_list(first, "sl-1", "ws-a", {"status": "new"}, signals)
        self.assertEqual(("s1",), first.member_ids)
        self.assertEqual((), second.member_ids)


if __name__ == "__main__":
    unittest.main()
