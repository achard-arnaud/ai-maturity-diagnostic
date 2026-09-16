"""Atomic, version-aware persistence for canonical file artifacts.

The store deliberately does not become business truth. It only centralizes
safe writes to the existing YAML/Markdown/JSONL artifacts and keeps callers
inside an explicit workspace root.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

import yaml


class ArtifactStoreError(RuntimeError):
    pass


class ArtifactPathError(ArtifactStoreError):
    pass


class ArtifactVersionConflict(ArtifactStoreError):
    pass


class ArtifactLockTimeout(ArtifactStoreError):
    pass


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ArtifactWriteResult:
    path: Path
    version: str
    previous_version: str | None
    bytes_written: int


@dataclass(frozen=True)
class ArtifactStore:
    root: Path
    lock_timeout_seconds: float = 10.0
    stale_lock_seconds: float = 120.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, path: Path | str) -> Path:
        candidate = Path(path)
        target = candidate.resolve() if candidate.is_absolute() else (self.root / candidate).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ArtifactPathError(f"artifact path escapes store root: {path}") from exc
        return target

    def version(self, path: Path | str) -> str | None:
        target = self._path(path)
        return _digest(target.read_bytes()) if target.is_file() else None

    def read_bytes(self, path: Path | str) -> tuple[bytes, str] | None:
        target = self._path(path)
        if not target.is_file():
            return None
        data = target.read_bytes()
        return data, _digest(data)

    def _lock_path(self, target: Path) -> Path:
        key = hashlib.sha256(target.relative_to(self.root).as_posix().encode("utf-8")).hexdigest()
        lock_root = self.root / "runtime" / "locks"
        lock_root.mkdir(parents=True, exist_ok=True)
        return lock_root / f"{key}.lock"

    @contextmanager
    def lock(self, path: Path | str) -> Iterator[None]:
        target = self._path(path)
        lock_path = self._lock_path(target)
        deadline = time.monotonic() + self.lock_timeout_seconds
        while True:
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(json.dumps({"pid": os.getpid(), "created_at": time.time()}))
                break
            except FileExistsError:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                    if age > self.stale_lock_seconds:
                        lock_path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() >= deadline:
                    raise ArtifactLockTimeout(f"timed out acquiring artifact lock: {target}")
                time.sleep(0.01)
        try:
            yield
        finally:
            lock_path.unlink(missing_ok=True)

    def write_bytes(
        self,
        path: Path | str,
        data: bytes,
        *,
        expected_version: str | None = None,
    ) -> ArtifactWriteResult:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.lock(target):
            previous = self.version(target)
            if expected_version is not None and previous != expected_version:
                raise ArtifactVersionConflict(
                    f"artifact version conflict for {target}: expected {expected_version}, found {previous}"
                )
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
                try:
                    directory_fd = os.open(target.parent, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                except OSError:
                    # Directory fsync is not supported on every platform.
                    pass
            finally:
                temporary.unlink(missing_ok=True)
        return ArtifactWriteResult(target, _digest(data), previous, len(data))

    def update_bytes(
        self,
        path: Path | str,
        updater: Callable[[bytes], bytes],
        *,
        expected_version: str | None = None,
    ) -> ArtifactWriteResult:
        """Atomically derive new bytes from the latest locked content."""

        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.lock(target):
            previous_data = target.read_bytes() if target.is_file() else b""
            previous = _digest(previous_data) if target.is_file() else None
            if expected_version is not None and previous != expected_version:
                raise ArtifactVersionConflict(
                    f"artifact version conflict for {target}: expected {expected_version}, found {previous}"
                )
            data = updater(previous_data)
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return ArtifactWriteResult(target, _digest(data), previous, len(data))

    def write_text(
        self,
        path: Path | str,
        text: str,
        *,
        expected_version: str | None = None,
    ) -> ArtifactWriteResult:
        return self.write_bytes(path, text.encode("utf-8"), expected_version=expected_version)

    def write_yaml(
        self,
        path: Path | str,
        document: Any,
        *,
        expected_version: str | None = None,
    ) -> ArtifactWriteResult:
        text = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
        return self.write_text(path, text, expected_version=expected_version)

    def append_jsonl(self, path: Path | str, record: dict[str, Any]) -> ArtifactWriteResult:
        line = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        return self.update_bytes(path, lambda previous: previous + line)

    @staticmethod
    def new_id(prefix: str = "artifact") -> str:
        return f"{prefix}_{uuid.uuid4().hex}"
