from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.event_journal import EventJournal
from app.product_workflow import (
    ProductAuthorizationError,
    ProductWorkflowError,
    create_draft_version,
    publish_version,
    submit_for_review,
)


def _content(**kwargs) -> dict:
    base = {"name": "Acme Suite", "description": "Core", "exclusions": [], "hard_gates": [], "capabilities": []}
    base.update(kwargs)
    return base


def _shared_scope() -> dict:
    return {"kind": "shared", "workspace_id": None}


class DraftAndSubmitTests(unittest.TestCase):
    def test_create_draft_starts_in_draft_status(self) -> None:
        version = create_draft_version(
            product_version_id="pv1", product_id="p1", version_number=1,
            created_by="alice", created_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual("draft", version["status"])
        self.assertIsNone(version["published_snapshot_id"])

    def test_submit_for_review_transitions_status(self) -> None:
        version = create_draft_version(
            product_version_id="pv1", product_id="p1", version_number=1,
            created_by="alice", created_at="2026-01-01T00:00:00+00:00",
        )
        submitted = submit_for_review(version)
        self.assertEqual("in_review", submitted["status"])

    def test_submit_already_in_review_is_rejected(self) -> None:
        version = create_draft_version(
            product_version_id="pv1", product_id="p1", version_number=1,
            created_by="alice", created_at="2026-01-01T00:00:00+00:00",
        )
        submitted = submit_for_review(version)
        with self.assertRaises(ProductWorkflowError):
            submit_for_review(submitted)


class PublishVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        draft = create_draft_version(
            product_version_id="pv1", product_id="p1", version_number=1,
            created_by="alice", created_at="2026-01-01T00:00:00+00:00",
        )
        self.in_review = submit_for_review(draft)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_requires_product_owner_role(self) -> None:
        with self.assertRaises(ProductAuthorizationError):
            publish_version(
                self.root, self.in_review, _content(),
                owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=[],
                published_by="alice", actor_role="standard_user",
                published_at="2026-01-05T00:00:00+00:00",
            )

    def test_publish_rejects_unauthenticated_role(self) -> None:
        with self.assertRaises(ProductAuthorizationError):
            publish_version(
                self.root, self.in_review, _content(),
                owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=[],
                published_by="alice", actor_role=None,
                published_at="2026-01-05T00:00:00+00:00",
            )

    def test_publish_requires_in_review_status(self) -> None:
        draft = create_draft_version(
            product_version_id="pv2", product_id="p1", version_number=2,
            created_by="alice", created_at="2026-01-01T00:00:00+00:00",
        )
        with self.assertRaises(ProductWorkflowError):
            publish_version(
                self.root, draft, _content(),
                owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=[],
                published_by="bob", actor_role="product_owner",
                published_at="2026-01-05T00:00:00+00:00",
            )

    def test_publish_succeeds_with_product_owner_role(self) -> None:
        published, snapshot, superseded = publish_version(
            self.root, self.in_review, _content(),
            owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=["e1"],
            published_by="bob", actor_role="product_owner",
            published_at="2026-01-05T00:00:00+00:00",
        )
        self.assertEqual("published", published["status"])
        self.assertEqual("snap1", published["published_snapshot_id"])
        self.assertEqual("snap1", snapshot["snapshot_id"])
        self.assertIsNone(superseded)
        self.assertIsNone(snapshot["supersedes_snapshot_id"])

    def test_publish_writes_audit_event(self) -> None:
        publish_version(
            self.root, self.in_review, _content(),
            owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=[],
            published_by="bob", actor_role="product_owner",
            published_at="2026-01-05T00:00:00+00:00",
        )
        journal = EventJournal(self.root)
        events = list(journal.replay())
        event = next(e for e in events if e["event_type"] == "ProductPublished")
        self.assertEqual("bob", event["actor_id"])
        self.assertEqual("snap1", event["data"]["snapshot_id"])

    def test_publishing_supersedes_previous_published_version(self) -> None:
        first_published, first_snapshot, _ = publish_version(
            self.root, self.in_review, _content(),
            owner_scope=_shared_scope(), snapshot_id="snap1", evidence_ids=[],
            published_by="bob", actor_role="product_owner",
            published_at="2026-01-05T00:00:00+00:00",
        )

        draft_v2 = create_draft_version(
            product_version_id="pv2", product_id="p1", version_number=2,
            created_by="alice", created_at="2026-02-01T00:00:00+00:00",
        )
        in_review_v2 = submit_for_review(draft_v2)

        published_v2, snapshot_v2, superseded = publish_version(
            self.root, in_review_v2, _content(description="v2 update"),
            owner_scope=_shared_scope(), snapshot_id="snap2", evidence_ids=[],
            published_by="bob", actor_role="product_owner",
            published_at="2026-02-05T00:00:00+00:00",
            previous_published_version=first_published,
        )

        self.assertEqual("superseded", superseded["status"])
        self.assertEqual("snap1", snapshot_v2["supersedes_snapshot_id"])
        self.assertEqual("published", published_v2["status"])
        # v1's own snapshot content/hash is untouched by the v2 publish.
        self.assertEqual("Core", first_snapshot["content"]["description"])


if __name__ == "__main__":
    unittest.main()
