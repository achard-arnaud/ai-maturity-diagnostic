from __future__ import annotations

import unittest

from jsonschema import Draft202012Validator

from app.artifact_policy import (
    ArtifactPolicyError,
    archive,
    build_artifact,
    can_archive,
    can_restore,
    load_artifact_schema,
    restore,
)


def make_artifact(**overrides):
    defaults = dict(
        artifact_id="artifact_1",
        kind="research_case",
        title="Acme research",
        workspace_id="acme-ws",
        created_at="2026-06-01T00:00:00+00:00",
        created_by="alice@example.com",
        locator="/api/v1/workspaces/acme-ws/research-cases/rc1",
    )
    defaults.update(overrides)
    return build_artifact(**defaults)


class BuildArtifactTests(unittest.TestCase):
    def test_valid_artifact_is_schema_valid(self) -> None:
        artifact = make_artifact()
        Draft202012Validator(load_artifact_schema()).validate(artifact)
        self.assertEqual("active", artifact["status"])
        self.assertEqual(1, artifact["version"])
        self.assertEqual({"preview": False, "export": False}, artifact["capabilities"])

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(kind="not_a_real_kind")

    def test_missing_title_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(title="  ")

    def test_missing_workspace_id_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(workspace_id="")

    def test_missing_locator_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(locator="")

    def test_invalid_status_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(status="deleted")

    def test_non_positive_version_is_rejected(self) -> None:
        with self.assertRaises(ArtifactPolicyError):
            make_artifact(version=0)

    def test_related_ids_and_capabilities_round_trip(self) -> None:
        artifact = make_artifact(related_ids=("evidence_1", "evidence_2"), preview=True, export=True)
        self.assertEqual(["evidence_1", "evidence_2"], artifact["related_ids"])
        self.assertEqual({"preview": True, "export": True}, artifact["capabilities"])
        Draft202012Validator(load_artifact_schema()).validate(artifact)


class ArchiveRestoreTests(unittest.TestCase):
    def test_archive_then_restore_round_trips(self) -> None:
        artifact = make_artifact()
        self.assertTrue(can_archive(artifact))
        self.assertFalse(can_restore(artifact))

        archived = archive(artifact)
        self.assertEqual("archived", archived["status"])
        self.assertFalse(can_archive(archived))
        self.assertTrue(can_restore(archived))

        restored = restore(archived)
        self.assertEqual("active", restored["status"])

    def test_archive_does_not_mutate_the_original(self) -> None:
        artifact = make_artifact()
        archive(artifact)
        self.assertEqual("active", artifact["status"])

    def test_double_archive_is_rejected(self) -> None:
        artifact = archive(make_artifact())
        with self.assertRaises(ArtifactPolicyError):
            archive(artifact)

    def test_restore_of_active_artifact_is_rejected(self) -> None:
        artifact = make_artifact()
        with self.assertRaises(ArtifactPolicyError):
            restore(artifact)

    def test_archive_only_changes_status_field(self) -> None:
        artifact = make_artifact()
        archived = archive(artifact)
        without_status = {k: v for k, v in archived.items() if k != "status"}
        original_without_status = {k: v for k, v in artifact.items() if k != "status"}
        self.assertEqual(original_without_status, without_status)


if __name__ == "__main__":
    unittest.main()
