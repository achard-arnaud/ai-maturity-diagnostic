"""Read-side aggregation of the "Suivi" / "Qualification" / "Nudging" flat lists into
one kanban-shaped board (E2E audit finding: these three tabs have no shared
pipeline/stage view -- see tests/e2e/journey-*.spec.ts).

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's module
docstring on the FastAPI-boundary rule).

This module does not recompute qualification stage, reach readiness, or nudging
hypotheses: it calls QualificationCockpit.list_studies(), ReachMatchmaker.list_ready(),
UseCaseNudger.list_inventories()/generate(), and FollowUpDashboard.items() -- all
already-existing public read methods -- and re-shapes their output into columns.

Vocabulary finding (documented rather than silently resolved): the three modules
use genuinely different stage vocabularies.
  - QualificationCockpit.list_studies()[*]["stage"] is a single, ordered pipeline
    field: demand -> product_snapshot -> matching (or matching_invalid) ->
    contact_targeting -> reach -> pilot -> completed, with a "stopped" side state.
  - ReachMatchmaker.list_ready()[*]["status"] is a *different* three-value enum
    ("blocked" / "ready" / "completed") describing readiness of the reach artifact
    for a study that is already in qualification's "reach" stage or later -- it is
    not the same axis as qualification's "stage" and does not nest cleanly under it
    (e.g. "completed" here means the reach strategy document exists, not that the
    opportunity is won).
  - UseCaseNudger has no stage/status pipeline field at all: nudges only carry a
    "mode" (productivization / upsell_dependency / cross_sell_package) and a
    constant "status": "hypothesis". Nudging is not itself staged.
  - FollowUpDashboard.items() reuses qualification's "stage" verbatim for its
    "qualification" kind, but for "value_chain" / "sector" / "technical_todo" kinds
    it has no per-study stage at all (those are sector- or repo-level, not
    per-opportunity), so this module only lifts the "qualification" kind onto the
    board; the others are not shaped as kanban cards.
CANONICAL_STAGES below is derived from (not invented on top of) qualification's
pipeline vocabulary, plus one additional "cross_sell" column that nudging's
otherwise-unstaged output is placed into, since it is the only forward activity
that happens after a study is otherwise complete.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.dashboard import FollowUpDashboard
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit
from app.reach import ReachMatchmaker

# Canonical, small stage list for the aggregated board. Order is the qualification
# pipeline order (see app/qualification.py's stage assignment), with "cross_sell"
# appended for nudging output and "stopped" kept last as the disqualified sink.
CANONICAL_STAGES: tuple[str, ...] = (
    "demand",
    "product_snapshot",
    "matching",
    "contact_targeting",
    "reach",
    "pilot",
    "completed",
    "cross_sell",
    "stopped",
)

# qualification.py also emits "matching_invalid" for a fit whose decision cannot be
# reconciled with its selected match; it is the same pipeline position as "matching"
# (repair needed before progressing), so it folds into the "matching" column.
_QUALIFICATION_STAGE_ALIASES: dict[str, str] = {"matching_invalid": "matching"}


def _qualification_stage(raw_stage: str | None) -> str:
    stage = _QUALIFICATION_STAGE_ALIASES.get(str(raw_stage), str(raw_stage))
    return stage if stage in CANONICAL_STAGES else "demand"


def build_board(root: Path) -> dict[str, Any]:
    """Aggregate qualification/reach/nudging/follow-up read state into one board.

    Never writes anything and never recomputes stage/readiness/hypothesis truth:
    every card is re-shaped from an existing public read method's own output.
    """
    columns: dict[str, list[dict[str, Any]]] = {stage: [] for stage in CANONICAL_STAGES}

    for row in QualificationCockpit(root).list_studies():
        stage = _qualification_stage(row.get("stage"))
        actions = [row["next_action"]] if row.get("next_action") else []
        columns[stage].append(
            {
                "study_id": row.get("study_id"),
                "company_id": row.get("company_id"),
                "title": row.get("company") or row.get("study_id"),
                "stage": stage,
                "source": "qualification",
                "actions": actions,
            }
        )

    for row in ReachMatchmaker(root).list_ready():
        # A reach artifact already exists ("completed" readiness): the study has
        # moved on to designing the proof/pilot. Otherwise it is still actively
        # being worked in the reach stage ("ready" or "blocked").
        stage = "pilot" if row.get("status") == "completed" else "reach"
        actions = ["Build / resolve reach"] if row.get("status") != "completed" else ["Design proof / pilot"]
        columns[stage].append(
            {
                "study_id": row.get("study_id"),
                "title": row.get("company") or row.get("study_id"),
                "stage": stage,
                "source": "reach",
                "actions": actions,
            }
        )

    nudger = UseCaseNudger(root)
    for inventory in nudger.list_inventories():
        study_id = inventory.get("study_id")
        if not study_id:
            continue
        generated = nudger.generate(study_id, mode="all")
        modes = sorted({nudge.get("mode") for nudge in generated.get("nudges", []) if nudge.get("mode")})
        columns["cross_sell"].append(
            {
                "study_id": study_id,
                "title": inventory.get("company") or study_id,
                "stage": "cross_sell",
                "source": "nudging",
                "actions": modes,
            }
        )

    for item in FollowUpDashboard(root).items():
        if item.get("kind") != "qualification":
            # value_chain / sector / technical_todo items have no per-study stage
            # of their own (sector- or repo-scoped); they do not map onto a
            # per-opportunity kanban column (see module docstring finding above).
            continue
        study_id = item.get("navigation", {}).get("study_id")
        if not study_id:
            continue
        stage = _qualification_stage(item.get("state"))
        columns[stage].append(
            {
                "study_id": study_id,
                "title": item.get("label"),
                "stage": stage,
                "source": "follow_up",
                "actions": [item["resolver"]["cta_label"]] if item.get("resolver") else [],
            }
        )

    return {"columns": [{"stage": stage, "cards": columns[stage]} for stage in CANONICAL_STAGES]}
