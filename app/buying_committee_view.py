"""Epic 08 S04: buying committee graph/read model.

Stop condition: "projection sans new truth" (a projection introduces no
new truth) -- this module is a pure, read-only function over already
recorded StakeholderRole/Influence data. It never writes anything, never
infers a fact not already present in its inputs, and its output is
deterministic (stable node/edge ordering regardless of input order) so
the same underlying data always projects to the exact same graph.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_committee_graph(
    stakeholders: Sequence[Mapping[str, Any]],
    influences_by_stakeholder_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Returns {"nodes": [...], "edges": [...]}, both stably sorted by id
    so two calls over the same (possibly differently-ordered) input
    always produce byte-identical output."""
    nodes = [
        {
            "id": s["stakeholder_role_id"],
            "role": s["role"],
            "person_entity_id": s["person_entity_id"],
            "status": s["status"],
        }
        for s in stakeholders
    ]
    nodes.sort(key=lambda n: n["id"])

    edges = []
    for stakeholder in stakeholders:
        sid = stakeholder["stakeholder_role_id"]
        influence = influences_by_stakeholder_id.get(sid)
        if influence and influence.get("warm_path"):
            edges.append(
                {
                    "from": f"warm_path:{influence['warm_path']}",
                    "to": sid,
                    "confidence": influence["confidence"],
                }
            )
    edges.sort(key=lambda e: (e["from"], e["to"]))

    return {"nodes": nodes, "edges": edges}
