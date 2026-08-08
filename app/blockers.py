from __future__ import annotations

import hashlib
from typing import Any


def _id(category: str, key: str) -> str:
    digest = hashlib.sha256(f"{category}\x1f{key}".encode("utf-8")).hexdigest()[:10].upper()
    return f"BLK-{digest}"


def blocker(
    *,
    category: str,
    key: str,
    message: str,
    required_state: str,
    cta_label: str,
    postcondition: str,
    owner_skill: str | None = None,
    human_action: str | None = None,
    cta_input: str | None = None,
    context_paths: list[str] | None = None,
    severity: str = "blocker",
    prepare_only_safe: bool = True,
) -> dict[str, Any]:
    if not owner_skill and not human_action:
        raise ValueError("a blocker resolver requires owner_skill or human_action")
    return {
        "blocker_id": _id(category, key),
        "category": category,
        "severity": severity,
        "message": message,
        "required_state": required_state,
        "owner_skill": owner_skill,
        "human_action": human_action,
        "cta_label": cta_label,
        "cta_input": cta_input,
        "context_paths": list(context_paths or []),
        "postcondition": postcondition,
        "prepare_only_safe": bool(prepare_only_safe),
    }


def attach_resolution(step: dict[str, Any], resolution: dict[str, Any] | None) -> dict[str, Any]:
    row = dict(step)
    if resolution is not None:
        row["blocker"] = resolution
        row["resolver"] = {
            "owner_skill": resolution.get("owner_skill"),
            "human_action": resolution.get("human_action"),
            "cta_label": resolution["cta_label"],
            "cta_input": resolution.get("cta_input"),
            "context_paths": resolution.get("context_paths", []),
            "postcondition": resolution["postcondition"],
            "prepare_only_safe": resolution["prepare_only_safe"],
        }
    return row


def human_review_blocker(*, key: str, message: str, required_state: str, cta_label: str, postcondition: str) -> dict[str, Any]:
    return blocker(
        category="human_review",
        key=key,
        message=message,
        required_state=required_state,
        cta_label=cta_label,
        postcondition=postcondition,
        human_action=required_state,
        prepare_only_safe=False,
    )
