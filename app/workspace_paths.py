"""WorkspacePaths — step 1 of the ADR-007 §5 legacy mono-root migration.

Plain Python, no framework dependency (per ADR-007 §6, business/runtime
path resolution must not import FastAPI/Starlette request objects).

This introduces the path resolver *behind* the existing domain
constructors (which already accept a ``root: Path``) while the default
workspace still resolves the legacy v0.7 mono-root layout unchanged.
Steps 2-5 of the migration sequence (dry-run inventory, copy/migrate with
verification, cutover, rollback manifest) are explicitly deferred to a
follow-up sprint — this only makes the boundary explicit and reversible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKSPACE_ID = "default"


class WorkspacePathError(ValueError):
    """Raised when a resolved path would escape its workspace root."""


@dataclass(frozen=True)
class WorkspacePaths:
    repo_root: Path
    workspace_id: str
    default_workspace_id: str = DEFAULT_WORKSPACE_ID

    def root(self) -> Path:
        """The root a domain constructor should treat as its ``root: Path``.

        The default workspace resolves to the existing legacy mono-root
        layout untouched (studies/, product_catalog/, data/, ...). Any
        other workspace resolves under workspaces/<id>/, which is created
        on first use and starts empty (no data migration happens here).
        """
        repo_root = self.repo_root.resolve()
        if self.workspace_id == self.default_workspace_id:
            return repo_root
        base = (repo_root / "workspaces" / self.workspace_id).resolve()
        try:
            base.relative_to((repo_root / "workspaces").resolve())
        except ValueError as exc:
            raise WorkspacePathError(f"workspace id escapes workspaces root: {self.workspace_id!r}") from exc
        base.mkdir(parents=True, exist_ok=True)
        return base

    def resolve(self, *parts: str) -> Path:
        """Resolve a sub-path within this workspace, rejecting escapes."""
        base = self.root()
        target = (base / Path(*parts)).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise WorkspacePathError(f"path escapes workspace root: {parts!r}") from exc
        return target


_REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_workspace_root(workspace_id: str = DEFAULT_WORKSPACE_ID, repo_root: Path | None = None) -> Path:
    """Resolve the ``root: Path`` a business-module constructor should use.

    Shared helper for each domain module's ``for_workspace`` classmethod
    (ADR-007 §5 migration step 1). Defaults ``repo_root`` to the same
    repository root the plain ``Class(ROOT)`` call sites already use, so
    ``resolve_workspace_root()`` with no arguments is byte-identical to
    today's hardcoded ``Path(__file__).resolve().parents[1]``.
    """
    base = repo_root if repo_root is not None else _REPO_ROOT
    return WorkspacePaths(base, workspace_id).root()
