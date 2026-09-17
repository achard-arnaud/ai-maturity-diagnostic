"""Derived, rebuildable SQLite search index over the private network JSONL layer.

Design (ADR-007 follow-on): the JSONL files under data/private/network/
(people.jsonl, companies.jsonl, relationships.jsonl) remain the canonical,
versioned source of truth. This module never writes to them. It only reads
them and materializes a SQLite index used for read-side search/filtering,
analogous to how scripts/build_sector_rollups.py derives a rollup from
source files. The index is always fully rebuilt (drop + recreate), never
incrementally patched, since a full rebuild is cheap at this data size
(~1300 people / ~40 companies).

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's
module docstring on the FastAPI-boundary rule).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from scripts.network_common import stable_id


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            records.append(item)
    return records


def _role_names(role_hypotheses: Any) -> list[str]:
    """Role hypotheses may be a list of strings or a list of objects with a
    'role' key (see scripts/network_common.py's infer_roles). Be defensive
    about either shape, and about malformed/missing values."""
    names: list[str] = []
    if not isinstance(role_hypotheses, list):
        return names
    for item in role_hypotheses:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(item.get("role"), str):
            names.append(item["role"])
    return names


def _parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _is_stale(last_updated: Any, stale_after_months: Any, *, as_of: date) -> bool:
    parsed = _parse_iso_date(last_updated)
    if parsed is None:
        return False
    try:
        months = int(stale_after_months)
    except (TypeError, ValueError):
        return False
    if months < 1:
        return False
    return as_of - parsed >= timedelta(days=months * 30)


DEFAULT_WORKSPACE_ID = "default"


SCHEMA = """
CREATE TABLE people (
    person_id TEXT PRIMARY KEY,
    display_name TEXT,
    normalized_name TEXT,
    seed_company_id TEXT,
    identity_confidence TEXT,
    status TEXT,
    last_updated TEXT,
    stale_after_months INTEGER,
    is_stale INTEGER NOT NULL DEFAULT 0,
    role_names TEXT,
    record_json TEXT NOT NULL
);
CREATE INDEX idx_people_status ON people(status);
CREATE INDEX idx_people_seed_company_id ON people(seed_company_id);
CREATE INDEX idx_people_identity_confidence ON people(identity_confidence);
CREATE INDEX idx_people_is_stale ON people(is_stale);

CREATE TABLE companies (
    company_id TEXT PRIMARY KEY,
    canonical_name TEXT,
    normalized_name TEXT,
    status TEXT,
    sector_code TEXT,
    workspace_id TEXT NOT NULL,
    last_updated TEXT,
    stale_after_months INTEGER,
    record_json TEXT NOT NULL
);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_sector_code ON companies(sector_code);
CREATE INDEX idx_companies_workspace_id ON companies(workspace_id);

CREATE TABLE relationships (
    relationship_id TEXT PRIMARY KEY,
    person_id TEXT,
    company_id TEXT,
    job_title TEXT,
    current_status TEXT,
    record_json TEXT NOT NULL
);
CREATE INDEX idx_relationships_person_id ON relationships(person_id);
CREATE INDEX idx_relationships_company_id ON relationships(company_id);
"""


def rebuild(data_root: Path, index_path: Path, *, as_of: date | None = None) -> dict[str, int]:
    """Fully rebuild the SQLite index at `index_path` from the JSONL files
    under `data_root` (people.jsonl, companies.jsonl, relationships.jsonl).

    Missing files are treated as empty, not an error. Returns the record
    counts written. Drops and recreates all tables every call -- this is a
    full rebuild, not an incremental update.
    """
    as_of = as_of or date.today()
    people = _read_jsonl(data_root / "people.jsonl")
    companies = _read_jsonl(data_root / "companies.jsonl")
    relationships = _read_jsonl(data_root / "relationships.jsonl")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(index_path))
    try:
        connection.executescript(
            """
            DROP TABLE IF EXISTS people;
            DROP TABLE IF EXISTS companies;
            DROP TABLE IF EXISTS relationships;
            """
        )
        connection.executescript(SCHEMA)

        for item in people:
            role_names = _role_names(item.get("role_hypotheses"))
            connection.execute(
                """
                INSERT INTO people (
                    person_id, display_name, normalized_name, seed_company_id,
                    identity_confidence, status, last_updated, stale_after_months,
                    is_stale, role_names, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("person_id"),
                    item.get("display_name"),
                    item.get("normalized_name"),
                    item.get("seed_company_id"),
                    item.get("identity_confidence"),
                    item.get("status"),
                    item.get("last_updated"),
                    item.get("stale_after_months"),
                    1 if _is_stale(item.get("last_updated"), item.get("stale_after_months"), as_of=as_of) else 0,
                    json.dumps(role_names),
                    json.dumps(item, ensure_ascii=False),
                ),
            )

        for item in companies:
            icb_mapping = item.get("icb_mapping") or {}
            sector = icb_mapping.get("sector") or {} if isinstance(icb_mapping, dict) else {}
            sector_code = sector.get("code") if isinstance(sector, dict) else None
            workspace_id = item.get("workspace_id") or DEFAULT_WORKSPACE_ID
            connection.execute(
                """
                INSERT INTO companies (
                    company_id, canonical_name, normalized_name, status,
                    sector_code, workspace_id, last_updated, stale_after_months, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("company_id"),
                    item.get("canonical_name"),
                    item.get("normalized_name"),
                    item.get("status"),
                    sector_code,
                    workspace_id,
                    item.get("last_updated"),
                    item.get("stale_after_months"),
                    json.dumps(item, ensure_ascii=False),
                ),
            )

        for item in relationships:
            connection.execute(
                """
                INSERT INTO relationships (
                    relationship_id, person_id, company_id, job_title,
                    current_status, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("relationship_id"),
                    item.get("person_id"),
                    item.get("company_id"),
                    item.get("job_title"),
                    item.get("current_status"),
                    json.dumps(item, ensure_ascii=False),
                ),
            )

        connection.commit()
    finally:
        connection.close()

    return {"people": len(people), "companies": len(companies), "relationships": len(relationships)}


def _row_record(row: sqlite3.Row) -> dict[str, Any]:
    return json.loads(row["record_json"])


def search_people(
    index_path: Path,
    *,
    text: str | None = None,
    status: str | None = None,
    company_id: str | None = None,
    role: str | None = None,
    stale_only: bool = False,
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    """Search the people table. Returns [] if the index has not been built
    yet (index_path missing) rather than raising -- callers (e.g. the
    read-side API routes) should not error just because nobody has run
    scripts/rebuild_network_index.py yet.

    `workspace_id` has no column of its own on people -- a person has no
    workspace_id, it is always derived through their company. It is
    implemented as a correlated lookup against companies.workspace_id via
    seed_company_id; a seed_company_id that does not resolve to any indexed
    company is treated as the "default" workspace (via COALESCE), matching
    rebuild()'s default for companies with no workspace_id of their own."""
    if not Path(index_path).is_file():
        return []
    connection = sqlite3.connect(str(index_path))
    connection.row_factory = sqlite3.Row
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if text:
            needle = f"%{text.strip().lower()}%"
            clauses.append("(lower(display_name) LIKE ? OR lower(normalized_name) LIKE ?)")
            params.extend([needle, needle])
        if status:
            clauses.append("status = ?")
            params.append(status)
        if company_id:
            clauses.append("seed_company_id = ?")
            params.append(company_id)
        if role:
            clauses.append("role_names LIKE ?")
            params.append(f'%"{role}"%')
        if stale_only:
            clauses.append("is_stale = 1")
        if workspace_id:
            clauses.append(
                "COALESCE("
                "(SELECT c.workspace_id FROM companies c WHERE c.company_id = people.seed_company_id),"
                f" '{DEFAULT_WORKSPACE_ID}') = ?"
            )
            params.append(workspace_id)
        query = "SELECT record_json FROM people"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY person_id"
        rows = connection.execute(query, params).fetchall()
        return [_row_record(row) for row in rows]
    finally:
        connection.close()


def get_company(index_path: Path, company_id: str) -> dict[str, Any] | None:
    """Single-record lookup by exact company_id. Returns None if the index
    has not been built yet, or no company with that id is indexed (never
    raises for either case, matching search_people/search_companies)."""
    if not Path(index_path).is_file():
        return None
    connection = sqlite3.connect(str(index_path))
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT record_json FROM companies WHERE company_id = ?", (company_id,)
        ).fetchone()
        return _row_record(row) if row is not None else None
    finally:
        connection.close()


def get_person(index_path: Path, person_id: str) -> dict[str, Any] | None:
    """Single-record lookup by exact person_id. Returns None if the index
    has not been built yet, or no person with that id is indexed (never
    raises for either case, matching get_company)."""
    if not Path(index_path).is_file():
        return None
    connection = sqlite3.connect(str(index_path))
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT record_json FROM people WHERE person_id = ?", (person_id,)
        ).fetchone()
        return _row_record(row) if row is not None else None
    finally:
        connection.close()


def find_potential_duplicates(
    index_path: Path,
    *,
    root: Path | None = None,
    include_dismissed: bool = False,
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    """Detection-only duplicate-person finder (CRM-audit gap #3).

    contracts/person.schema.yaml recomputes `person_id` per company, so a
    person changing employer gets a brand-new person_id and their old
    record is orphaned rather than merged. This groups indexed people by
    `normalized_name` (already indexed) where more than one row shares
    the same normalized_name across *different* seed_company_id values,
    and returns one group per name with both/all records so a human can
    review and decide. This function never merges, deletes or otherwise
    mutates anything -- see the module docstring's "no active cleanup
    pass" note from the workspace sprint; it is read-only detection.

    Two people who happen to have the same normalized_name at the *same*
    company are not flagged here (that is an identity-key collision, a
    different and separately-tracked problem, not a company-change
    duplicate). Returns [] if the index has not been built yet.

    Each returned group carries a `group_key` -- the same content-derived id
    `app.duplicate_dismissals.dismiss_duplicate_group` computes from the
    group's person_ids -- so a caller can dismiss it. When `root` (the
    workspace root that owns `data/private/network/duplicate_dismissals.jsonl`,
    same convention as `app.duplicate_dismissals`) is passed, a group a human
    has already dismissed as "not a duplicate" (red-team-side-story C3) is
    excluded from the result by default, since re-running detection
    recomputes groups fresh every call and would otherwise make a dismissed
    group reappear forever; pass `include_dismissed=True` to see everything,
    dismissed or not. `root` is optional (and ignored when absent) so
    existing callers that only care about raw detection are unaffected.

    `workspace_id`, when given, restricts groups to people whose company
    resolves (via the same COALESCE-over-seed_company_id lookup used by
    search_people) to that workspace. A person changing employer across
    workspaces is out of scope for this detector -- both rows must share
    a workspace to be flagged.
    """
    if not Path(index_path).is_file():
        return []
    connection = sqlite3.connect(str(index_path))
    connection.row_factory = sqlite3.Row
    try:
        clauses = ["normalized_name IS NOT NULL", "normalized_name != ''"]
        params: list[Any] = []
        if workspace_id:
            clauses.append(
                "COALESCE("
                "(SELECT c.workspace_id FROM companies c WHERE c.company_id = people.seed_company_id),"
                f" '{DEFAULT_WORKSPACE_ID}') = ?"
            )
            params.append(workspace_id)
        query = (
            "SELECT normalized_name, person_id, seed_company_id, status, record_json "
            "FROM people WHERE " + " AND ".join(clauses) + " ORDER BY normalized_name, person_id"
        )
        rows = connection.execute(query, params).fetchall()
    finally:
        connection.close()

    by_name: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_name.setdefault(row["normalized_name"], []).append(row)

    dismissed_keys: set[str] = set()
    if root is not None and not include_dismissed:
        from app.duplicate_dismissals import list_dismissed_group_keys

        dismissed_keys = list_dismissed_group_keys(root)

    groups: list[dict[str, Any]] = []
    for normalized_name, group_rows in by_name.items():
        companies = {row["seed_company_id"] for row in group_rows}
        if len(group_rows) < 2 or len(companies) < 2:
            continue
        person_ids = sorted({row["person_id"] for row in group_rows if row["person_id"]})
        group_key = stable_id("DUPDISMISS", *person_ids) if len(person_ids) >= 2 else None
        if group_key is not None and group_key in dismissed_keys:
            continue
        groups.append(
            {
                "normalized_name": normalized_name,
                "group_key": group_key,
                "records": [
                    {
                        "person_id": row["person_id"],
                        "seed_company_id": row["seed_company_id"],
                        "status": row["status"],
                        "record": _row_record(row),
                    }
                    for row in group_rows
                ],
            }
        )
    groups.sort(key=lambda item: item["normalized_name"])
    return groups


def search_companies(
    index_path: Path,
    *,
    text: str | None = None,
    sector: str | None = None,
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    if not Path(index_path).is_file():
        return []
    connection = sqlite3.connect(str(index_path))
    connection.row_factory = sqlite3.Row
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if text:
            needle = f"%{text.strip().lower()}%"
            clauses.append("(lower(canonical_name) LIKE ? OR lower(normalized_name) LIKE ?)")
            params.extend([needle, needle])
        if sector:
            clauses.append("sector_code = ?")
            params.append(sector)
        if workspace_id:
            clauses.append("workspace_id = ?")
            params.append(workspace_id)
        query = "SELECT record_json FROM companies"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY company_id"
        rows = connection.execute(query, params).fetchall()
        return [_row_record(row) for row in rows]
    finally:
        connection.close()
