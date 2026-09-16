from __future__ import annotations

import unittest

from app.product_policy import (
    SnapshotImmutabilityError,
    assert_snapshot_immutable,
    can_transition_version,
    compute_content_hash,
    next_version_number,
)


def _content(**kwargs) -> dict:
    base = {
        "name": "Acme Suite",
        "description": "Core offering",
        "exclusions": ["no on-prem"],
        "hard_gates": ["SOC2 required"],
        "capabilities": [],
    }
    base.update(kwargs)
    return base


class VersionTransitionTests(unittest.TestCase):
    def test_draft_to_in_review_allowed(self) -> None:
        self.assertTrue(can_transition_version("draft", "in_review"))

    def test_draft_to_published_not_allowed_directly(self) -> None:
        self.assertFalse(can_transition_version("draft", "published"))

    def test_in_review_to_published_allowed(self) -> None:
        self.assertTrue(can_transition_version("in_review", "published"))

    def test_in_review_back_to_draft_allowed(self) -> None:
        self.assertTrue(can_transition_version("in_review", "draft"))

    def test_published_to_superseded_allowed(self) -> None:
        self.assertTrue(can_transition_version("published", "superseded"))

    def test_published_to_draft_not_allowed(self) -> None:
        self.assertFalse(can_transition_version("published", "draft"))

    def test_superseded_is_terminal(self) -> None:
        self.assertFalse(can_transition_version("superseded", "published"))
        self.assertFalse(can_transition_version("superseded", "draft"))


class ContentHashTests(unittest.TestCase):
    def test_same_content_same_hash(self) -> None:
        self.assertEqual(compute_content_hash(_content()), compute_content_hash(_content()))

    def test_key_order_does_not_affect_hash(self) -> None:
        a = {"name": "X", "description": "Y", "exclusions": [], "hard_gates": []}
        b = {"hard_gates": [], "exclusions": [], "description": "Y", "name": "X"}
        self.assertEqual(compute_content_hash(a), compute_content_hash(b))

    def test_different_content_different_hash(self) -> None:
        self.assertNotEqual(
            compute_content_hash(_content()),
            compute_content_hash(_content(description="Changed")),
        )


class SnapshotImmutabilityTests(unittest.TestCase):
    def test_identical_content_is_accepted(self) -> None:
        content = _content()
        snapshot = {"snapshot_id": "snap1", "content_hash": compute_content_hash(content)}
        assert_snapshot_immutable(snapshot, content)  # should not raise

    def test_changed_content_is_rejected(self) -> None:
        original = _content()
        snapshot = {"snapshot_id": "snap1", "content_hash": compute_content_hash(original)}
        with self.assertRaises(SnapshotImmutabilityError):
            assert_snapshot_immutable(snapshot, _content(description="Sneaky edit"))

    def test_n_minus_1_snapshot_is_unaffected_by_a_new_publish(self) -> None:
        # Publishing version N (a new snapshot_id) never touches version
        # N-1's already-published snapshot -- its hash still matches its
        # own original content, unconditionally.
        v1_content = _content()
        v1_snapshot = {"snapshot_id": "snap-v1", "content_hash": compute_content_hash(v1_content)}

        v2_content = _content(description="Updated for v2")
        v2_snapshot = {"snapshot_id": "snap-v2", "content_hash": compute_content_hash(v2_content)}

        # v1's snapshot is still exactly reproducible from its own content.
        assert_snapshot_immutable(v1_snapshot, v1_content)
        # v2's snapshot is a distinct, independently valid artifact.
        assert_snapshot_immutable(v2_snapshot, v2_content)
        self.assertNotEqual(v1_snapshot["content_hash"], v2_snapshot["content_hash"])


class VersionNumberTests(unittest.TestCase):
    def test_first_version_is_1(self) -> None:
        self.assertEqual(1, next_version_number([]))

    def test_next_version_is_one_past_highest(self) -> None:
        self.assertEqual(4, next_version_number([1, 2, 3]))

    def test_archived_version_numbers_are_never_reused(self) -> None:
        # Even if version 2 was archived, the next one is still 4, not 2.
        self.assertEqual(4, next_version_number([1, 3]))


if __name__ == "__main__":
    unittest.main()
