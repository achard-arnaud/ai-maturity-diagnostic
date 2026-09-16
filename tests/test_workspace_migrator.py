import json
import tempfile
import unittest
from pathlib import Path

from app.workspace_migrator import MigrationError, WorkspaceMigrator


class WorkspaceMigratorTests(unittest.TestCase):
    def seed(self, root: Path) -> None:
        (root / "studies/acme").mkdir(parents=True)
        (root / "studies/acme/00_manifest.yaml").write_text("study: acme\n")
        (root / "data/private/network").mkdir(parents=True)
        (root / "data/private/network/companies.jsonl").write_text('{"company_id":"acme"}\n')
        (root / "artifacts").mkdir()
        (root / "artifacts/TODO.yaml").write_text("items: []\n")
        (root / "product_catalog").mkdir()
        (root / "product_catalog/index.yaml").write_text("offers: []\n")

    def test_dry_run_apply_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(root)
            migrator = WorkspaceMigrator(root, "default-migrated")
            plan = migrator.plan()
            self.assertEqual(plan["counts"]["copy"], 3)
            self.assertNotIn("product_catalog/index.yaml", [item["source"] for item in plan["items"]])
            manifest = migrator.apply(plan)
            self.assertTrue((root / "workspaces/default-migrated/studies/acme/00_manifest.yaml").is_file())
            self.assertEqual(json.loads(manifest.read_text())["counts"]["files"], 3)
            result = migrator.rollback(manifest)
            self.assertEqual(len(result["removed"]), 3)
            self.assertTrue((root / "studies/acme/00_manifest.yaml").is_file())

    def test_changed_source_after_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(root)
            migrator = WorkspaceMigrator(root, "ws")
            plan = migrator.plan()
            (root / "artifacts/TODO.yaml").write_text("changed: true\n")
            with self.assertRaises(MigrationError):
                migrator.apply(plan)

    def test_rollback_refuses_modified_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(root)
            migrator = WorkspaceMigrator(root, "ws")
            manifest = migrator.apply(migrator.plan())
            destination = root / "workspaces/ws/studies/acme/00_manifest.yaml"
            destination.write_text("user change\n")
            with self.assertRaises(MigrationError):
                migrator.rollback(manifest)

    def test_apply_preflight_leaves_no_partial_copy_when_source_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(root)
            migrator = WorkspaceMigrator(root, "ws")
            plan = migrator.plan()
            (root / "studies/acme/00_manifest.yaml").write_text("changed\n")
            with self.assertRaises(MigrationError):
                migrator.apply(plan)
            self.assertFalse((root / "workspaces/ws").exists())


if __name__ == "__main__":
    unittest.main()
