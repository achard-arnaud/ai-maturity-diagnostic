"""Epic 05 S01: Demand v1 policy primitives.

Per this Epic's own invariants ("Demand indépendante du catalogue ;
inconnues visibles ; fit et ciblage interdits dans ce contexte"): a
Demand never carries a product/catalog/fit/targeting field, and every one
of its 8 knowable dimensions is either an explicit known value or a
visible, typed unknown -- never a silent omission or a guessed default.
"""

from __future__ import annotations

from typing import Any, Mapping

FORBIDDEN_TOKENS = ("product", "catalog", "offer", "fit", "recommend", "match", "target")

KNOWABLE_FIELDS = (
    "problem",
    "population",
    "impact",
    "urgency",
    "initiative",
    "sponsor",
    "budget",
    "timing",
)


class DemandContaminationError(Exception):
    pass


def known(value: str) -> dict[str, Any]:
    """A knowable_field with an explicit value."""
    if not value:
        raise ValueError("known() requires a non-empty value -- use unknown() otherwise")
    return {"known": True, "value": value}


def unknown() -> dict[str, Any]:
    """A knowable_field marked as an explicit, visible unknown."""
    return {"known": False, "value": None}


def assert_no_product_fields(data: Mapping[str, Any]) -> None:
    """Defense-in-depth runtime guard mirroring
    app.signal_policy.assert_no_demand_fields: walks every key in data
    (and, for knowable fields, their value text) for banned
    product/fit/targeting vocabulary."""
    for key, value in data.items():
        lowered = key.lower()
        for token in FORBIDDEN_TOKENS:
            if token in lowered:
                raise DemandContaminationError(f"field {key!r} looks product/fit-shaped")
        if isinstance(value, Mapping) and "value" in value and isinstance(value["value"], str):
            text = value["value"].lower()
            for token in FORBIDDEN_TOKENS:
                if token in text:
                    raise DemandContaminationError(
                        f"field {key!r}'s value mentions banned vocabulary {token!r}"
                    )


def is_complete(demand: Mapping[str, Any]) -> bool:
    """A Demand is "complete" once problem is known -- the one dimension
    this Epic's target state treats as load-bearing; every other
    dimension may legitimately stay an unknown."""
    return bool(demand.get("problem", {}).get("known"))


def count_unknowns(demand: Mapping[str, Any]) -> int:
    return sum(1 for field in KNOWABLE_FIELDS if not demand.get(field, {}).get("known"))
