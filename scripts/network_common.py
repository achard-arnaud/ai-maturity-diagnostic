"""Shared deterministic helpers for the private network data layer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def stable_id(prefix: str, *values: str, length: int = 12) -> str:
    payload = "\x1f".join(normalize(value) for value in values)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length].upper()
    return f"{prefix}-{digest}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def dump_yaml(path: Path, data: Any) -> None:
    atomic_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        records.append(item)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]], sort_key: str) -> None:
    ordered = sorted(records, key=lambda item: str(item.get(sort_key, "")))
    content = "".join(json.dumps(item, ensure_ascii=False, sort_keys=False) + "\n" for item in ordered)
    atomic_text(path, content)


ROLE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("veto_player", r"\b(ciso|cyber|security|securite|risk|risque|compliance|conformite|dpo|data protection|audit|legal)\b", "medium"),
    ("economic_sponsor", r"\b(cio|chief information officer|cto|chief technology officer|chief digital officer|chief data officer|chief artificial intelligence officer|group cio|vp data|vp it|executive director)\b", "medium"),
    ("technical_sponsor", r"\b(head of ai|head of data|head of technology|head of engineering|head of digital|director.*(data|digital|technology|information systems|it)|global head.*(ai|data|technology))\b", "medium"),
    ("terrain_owner", r"\b(manager|lead|head|director|responsable).*(ai|data|engineering|platform|cloud|devops|digital|architecture|transformation|program|project|product)\b", "medium"),
    ("transformation_owner", r"\b(transformation|change management|digital adoption|operational excellence|pmo|portfolio|program director|project director)\b", "medium"),
    ("influencer", r"\b(architect|data scientist|data engineer|ai engineer|product manager|project manager|tech lead|expert|consultant)\b", "low"),
)


def infer_roles(job_title: str) -> list[dict[str, str]]:
    title = normalize(job_title)
    roles: list[dict[str, str]] = []
    for role, pattern, confidence in ROLE_PATTERNS:
        if re.search(pattern, title, flags=re.I):
            roles.append(
                {
                    "role": role,
                    "confidence": confidence,
                    "basis": "job_title_only",
                    "epistemic_status": "hypothesis",
                }
            )
    if not roles:
        roles.append(
            {
                "role": "unclassified_contact",
                "confidence": "low",
                "basis": "job_title_only",
                "epistemic_status": "unknown",
            }
        )
    return roles


def title_signals(job_title: str) -> dict[str, bool]:
    title = normalize(job_title)
    return {
        "senior": bool(re.search(r"\b(chief|cio|cto|ciso|cdo|vp|vice president|director|directeur|head)\b", title)),
        "ai_data": bool(re.search(r"\b(ai|artificial intelligence|ia|data|machine learning|gen ai|analytics)\b", title)),
        "delivery": bool(re.search(r"\b(engineering|platform|cloud|devops|architecture|program|project|product|transformation|operations|digital)\b", title)),
        "security": bool(re.search(r"\b(ciso|cyber|security|securite|risk|compliance|dpo|audit)\b", title)),
    }


def parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
