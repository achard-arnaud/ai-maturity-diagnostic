from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core import RepoControlPlane


class RepoControlPlaneWorkspaceTests(unittest.TestCase):
    def test_for_workspace_default_matches_legacy_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plane = RepoControlPlane.for_workspace("default", repo_root=root)
            self.assertEqual(plane.root, root.resolve())

    def test_for_workspace_named_resolves_under_workspaces_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plane = RepoControlPlane.for_workspace("acme", repo_root=root)
            self.assertEqual(plane.root, (root / "workspaces" / "acme").resolve())


if __name__ == "__main__":
    unittest.main()
