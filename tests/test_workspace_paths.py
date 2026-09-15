from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.workspace_paths import WorkspacePathError, WorkspacePaths, resolve_workspace_root


class WorkspacePathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        (self.repo_root / "studies").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_default_workspace_resolves_legacy_mono_root(self) -> None:
        paths = WorkspacePaths(self.repo_root, "default")
        self.assertEqual(paths.root(), self.repo_root.resolve())
        self.assertEqual(paths.resolve("studies"), (self.repo_root / "studies").resolve())

    def test_other_workspace_resolves_under_workspaces_tree(self) -> None:
        paths = WorkspacePaths(self.repo_root, "acme")
        root = paths.root()
        self.assertEqual(root, (self.repo_root / "workspaces" / "acme").resolve())
        self.assertTrue(root.is_dir())

    def test_resolve_rejects_path_escape(self) -> None:
        paths = WorkspacePaths(self.repo_root, "acme")
        with self.assertRaises(WorkspacePathError):
            paths.resolve("..", "..", "etc", "passwd")

    def test_workspace_id_cannot_escape_workspaces_root(self) -> None:
        paths = WorkspacePaths(self.repo_root, "../../etc")
        with self.assertRaises(WorkspacePathError):
            paths.root()


class ResolveWorkspaceRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        (self.repo_root / "studies").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_default_workspace_matches_legacy_root(self) -> None:
        self.assertEqual(resolve_workspace_root("default", self.repo_root), self.repo_root.resolve())

    def test_named_workspace_resolves_under_workspaces_tree(self) -> None:
        root = resolve_workspace_root("acme", self.repo_root)
        self.assertEqual(root, (self.repo_root / "workspaces" / "acme").resolve())

    def test_no_arguments_uses_repo_root_default(self) -> None:
        from app.workspace_paths import _REPO_ROOT

        self.assertEqual(resolve_workspace_root(), _REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
