"""Account/contact "360 view" aggregation (CRM-audit gap #1).

Plain Python, no framework imports (ADR-004: business modules stay
framework-free; only app/server.py may depend on FastAPI). This module
never writes anything -- it purely aggregates already-computed, already
canonical data from:

  - the network SQLite index (app.network_index) for the company record
    and the people who work there;
  - app.qualification.QualificationCockpit for the qualification study
    tied to that company, if one exists;
  - app.reach.ReachMatchmaker's ready-list for reach status, if any;
  - app.blocker_actions.BlockerActionLog for recent human actions on that
    study's blockers.

Design decision (documented per the task's "pick one and be consistent"
instruction): `get_account_360` returns `None` for an unknown
company_id, rather than raising `ControlPlaneError`. This mirrors
app.network_index.search_companies/get_company, which already return an
empty/None result instead of raising for a company the index does not
know about -- a 360 view is a read-side aggregation, and "not found" is
an ordinary, expected outcome for it (contrast with app.reach's
`_study_dir`, which raises because a missing study there is a caller
programming error against a required precondition).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.blocker_actions import BlockerActionLog
from app.network_index import get_company, search_people
from app.qualification import QualificationCockpit
from app.reach import ReachMatchmaker


def get_account_360(root: Path, company_id: str, *, index_path: Path | None = None) -> dict[str, Any] | None:
    """Aggregate everything the app knows about one company.

    `root` is the workspace/repo root used to instantiate the file-based
    business modules (QualificationCockpit, ReachMatchmaker,
    BlockerActionLog), matching their existing `for_workspace`/`Class(root)`
    construction convention. `index_path` defaults to the standard derived
    SQLite index location under `root` (see app/server.py's
    NETWORK_INDEX_PATH) but can be overridden, e.g. for tests.

    Returns None if the company is not known to the network index at all
    (see module docstring for why this is `None`, not an exception).
    Every other missing piece (no qualification study yet, no reach
    status, no recorded blocker actions) is populated as `None`/[] rather
    than raising, since not every company has reached those stages.
    """
    company_id = str(company_id or "").strip()
    if not company_id:
        return None
    idx_path = index_path or (root / "data" / "private" / "network" / "network_index.sqlite")

    company = get_company(idx_path, company_id)
    if company is None:
        return None

    people = search_people(idx_path, company_id=company_id)

    qualification: dict[str, Any] | None = None
    recent_actions: list[dict[str, Any]] = []
    for study_row in QualificationCockpit(root).list_studies():
        if study_row.get("company_id") == company_id:
            qualification = study_row
            recent_actions = BlockerActionLog(root).list_actions(str(study_row["study_id"]))
            break

    reach: dict[str, Any] | None = None
    if qualification is not None:
        for reach_row in ReachMatchmaker(root).list_ready():
            if reach_row.get("study_id") == qualification.get("study_id"):
                reach = reach_row
                break

    return {
        "company": company,
        "people": people,
        "qualification": qualification,
        "reach": reach,
        "recent_actions": recent_actions,
    }
