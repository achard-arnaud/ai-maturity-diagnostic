"""Epic 10 S03: objection classification, confidence, human review.

Stop condition: "faible confiance routée" (low confidence routed) -- a
classification below the confidence threshold can never drive a
downstream action (S04) until a human reviews it; it is always routed
to a review queue instead of being silently acted on.
"""

from __future__ import annotations

from typing import Any, Sequence

CONFIDENCE_THRESHOLD = 0.7


class EngagementClassificationError(Exception):
    pass


def classify_objection(
    *, objection_id: str, engagement_event_id: str, category: str, confidence: float, raised_at: str,
) -> dict[str, Any]:
    """The sole constructor. Always created status=draft -- confidence
    alone decides whether it can already act (see can_act_on_objection),
    never the constructor."""
    if not 0.0 <= confidence <= 1.0:
        raise EngagementClassificationError(f"confidence must be in [0, 1], got {confidence!r}")
    return {
        "objection_id": objection_id,
        "engagement_event_id": engagement_event_id,
        "category": category,
        "confidence": confidence,
        "status": "draft",
        "raised_at": raised_at,
        "reviewed_by": None,
        "reviewed_at": None,
    }


def needs_human_review(objection: dict[str, Any]) -> bool:
    return objection["status"] == "draft" and objection["confidence"] < CONFIDENCE_THRESHOLD


def can_act_on_objection(objection: dict[str, Any]) -> bool:
    """The sole choke point downstream code (S04) must call before
    acting on an Objection. A low-confidence draft is always blocked
    until a human reviews it; a high-confidence one may already act
    even in draft -- but review, once done, is never re-litigated."""
    return objection["status"] == "reviewed" or objection["confidence"] >= CONFIDENCE_THRESHOLD


def review_objection(objection: dict[str, Any], *, reviewed_by: str, reviewed_at: str) -> dict[str, Any]:
    if objection["status"] != "draft":
        raise EngagementClassificationError(f"cannot review an objection in status={objection['status']!r}")
    updated = dict(objection)
    updated["status"] = "reviewed"
    updated["reviewed_by"] = reviewed_by
    updated["reviewed_at"] = reviewed_at
    return updated


def build_review_queue(objections: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic queue of everything a human still needs to look
    at -- low-confidence drafts only, oldest first."""
    queue = [o for o in objections if needs_human_review(o)]
    queue.sort(key=lambda o: (o["raised_at"], o["objection_id"]))
    return queue
