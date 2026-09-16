"""Epic 06 S05: snapshot content diff (pure, read-only).

Compares two ProductSnapshot `content` dicts field by field. Scalar
fields (name/description) report old/new when changed; list fields
(exclusions/hard_gates/capabilities) report added/removed items as set
differences -- order-independent, so reordering an unchanged list never
shows up as a diff.
"""

from __future__ import annotations

from typing import Any, Mapping

_SCALAR_FIELDS = ("name", "description")
_LIST_FIELDS = ("exclusions", "hard_gates", "capabilities")


def diff_snapshot_content(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    diff: dict[str, Any] = {}

    for field in _SCALAR_FIELDS:
        old_value = old.get(field)
        new_value = new.get(field)
        if old_value != new_value:
            diff[field] = {"old": old_value, "new": new_value}

    for field in _LIST_FIELDS:
        old_set = set(old.get(field) or [])
        new_set = set(new.get(field) or [])
        added = sorted(new_set - old_set)
        removed = sorted(old_set - new_set)
        if added or removed:
            diff[field] = {"added": added, "removed": removed}

    return diff
