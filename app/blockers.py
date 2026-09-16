from __future__ import annotations

import hashlib
from typing import Any


def _id(category: str, key: str, *, prefix: str = "BLK") -> str:
    digest = hashlib.sha256(f"{category}\x1f{key}".encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


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


_EPISTEMIC_STATUSES = {"fact", "inference", "hypothesis", "unknown"}


def issue(
    *,
    kind: str,
    statement: str,
    epistemic_status: str = "hypothesis",
    can_change_decision: bool = False,
    key: str | None = None,
    context_paths: list[str] | None = None,
) -> dict[str, Any]:
    """A non-blocking tension worth a human/dashboard's attention.

    Unlike a blocker(), an issue() never stops qualification progress: it has
    no owner_skill/human_action/cta and no postcondition to satisfy. It is a
    structured "we noticed something soft here" note, not a gate.
    """
    if not kind or not statement:
        raise ValueError("an issue requires both kind and statement")
    if epistemic_status not in _EPISTEMIC_STATUSES:
        raise ValueError(f"unknown epistemic_status {epistemic_status!r}; expected one of {sorted(_EPISTEMIC_STATUSES)}")
    return {
        "issue_id": _id("issue", key or f"{kind}\x1f{statement}", prefix="ISS"),
        "kind": kind,
        "statement": statement,
        "epistemic_status": epistemic_status,
        "can_change_decision": bool(can_change_decision),
        "context_paths": list(context_paths or []),
    }


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
