"""Framework-neutral correlation context propagated across platform services."""

from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Iterator


_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)


def current_correlation_id() -> str:
    value = _correlation_id.get()
    return value or str(uuid.uuid4())


@contextmanager
def correlation_scope(correlation_id: str | None = None) -> Iterator[str]:
    value = str(correlation_id or uuid.uuid4())
    token = _correlation_id.set(value)
    try:
        yield value
    finally:
        _correlation_id.reset(token)
