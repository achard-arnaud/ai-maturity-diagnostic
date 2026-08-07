from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.core import _read_yaml


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


@dataclass(frozen=True)
class DemandCatalog:
    root: Path
    stale_after_days: int = 180

    def _taxonomy_sectors(self) -> dict[str, dict[str, Any]]:
        path = self.root / "data" / "taxonomies" / "icb_v5_2026.yaml"
        if not path.is_file():
            return {}
        doc = _read_yaml(path)
        result: dict[str, dict[str, Any]] = {}
        for industry in doc.get("industries", []) or []:
            if not isinstance(industry, dict):
                continue
            for supersector in industry.get("supersectors", []) or []:
                if not isinstance(supersector, dict):
                    continue
                for sector in supersector.get("sectors", []) or []:
                    if not isinstance(sector, dict) or not sector.get("code"):
                        continue
                    code = str(sector["code"])
                    result[code] = {
                        "sector_code": code,
                        "sector_name": sector.get("name"),
                        "supersector_code": str(supersector.get("code") or ""),
                        "supersector_name": supersector.get("name"),
                        "industry_code": str(industry.get("code") or ""),
                        "industry_name": industry.get("name"),
                    }
        return result

    def _companies(self) -> dict[str, dict[str, Any]]:
        rows = _read_jsonl(self.root / "data" / "private" / "network" / "companies.jsonl")
        return {str(row.get("company_id")): row for row in rows if row.get("company_id")}

    def _mappings(self) -> dict[str, dict[str, Any]]:
        rows = _read_jsonl(self.root / "data" / "private" / "network" / "company_icb_mappings.jsonl")
        return {str(row.get("company_id")): row for row in rows if row.get("company_id")}

    def _latest_studies(self, as_of: date) -> dict[str, dict[str, Any]]:
        studies_root = self.root / "studies"
        latest: dict[str, dict[str, Any]] = {}
        if not studies_root.is_dir():
            return latest
        for manifest_path in studies_root.glob("*/00_manifest.yaml"):
            study_dir = manifest_path.parent
            try:
                manifest = _read_yaml(manifest_path)
            except Exception:
                continue
            company_id = manifest.get("company_id")
            if not company_id:
                continue
            updated = _iso_date(manifest.get("updated_at"))
            current = bool(updated and updated <= as_of and as_of - updated <= timedelta(days=self.stale_after_days))
            profile_path = study_dir / "05_enterprise_demand_profile.yaml"
            profile = _read_yaml(profile_path) if profile_path.is_file() else {}
            complete = bool(profile.get("evidence_claims") and profile.get("capability_gaps")) and profile.get("confidence") in {"medium", "high"}
            use_case_path = study_dir / "05b_use_case_inventory.yaml"
            inventory = _read_yaml(use_case_path) if use_case_path.is_file() else {}
            record = {
                "study_id": manifest.get("study_id") or study_dir.name,
                "study_path": study_dir.relative_to(self.root).as_posix(),
                "company_id": str(company_id),
                "company": manifest.get("company"),
                "updated_at": manifest.get("updated_at"),
                "current": current,
                "complete": complete,
                "eligible": current and complete,
                "use_case_count": len(inventory.get("use_cases", []) or []),
                "use_case_inventory_path": use_case_path.relative_to(self.root).as_posix() if use_case_path.is_file() else None,
            }
            prior = latest.get(str(company_id))
            if prior is None or str(record.get("updated_at") or "") >= str(prior.get("updated_at") or ""):
                latest[str(company_id)] = record
        return latest

    def snapshot(self, *, as_of: date | None = None) -> dict[str, Any]:
        effective_date = as_of or date.today()
        taxonomy = self._taxonomy_sectors()
        companies = self._companies()
        mappings = self._mappings()
        studies = self._latest_studies(effective_date)

        sector_companies: dict[str, list[dict[str, Any]]] = {code: [] for code in taxonomy}
        for company_id, mapping in mappings.items():
            if mapping.get("mapping_status") not in {"candidate", "validated"}:
                continue
            sector = mapping.get("sector") or {}
            sector_code = str(sector.get("code") or "")
            if not sector_code:
                continue
            company = companies.get(company_id, {})
            study = studies.get(company_id, {})
            sector_companies.setdefault(sector_code, []).append(
                {
                    "company_id": company_id,
                    "company": company.get("canonical_name") or study.get("company") or company_id,
                    "mapping_status": mapping.get("mapping_status"),
                    "icb_confidence": mapping.get("confidence"),
                    "study_id": study.get("study_id"),
                    "study_path": study.get("study_path"),
                    "study_current": bool(study.get("current")),
                    "study_complete": bool(study.get("complete")),
                    "eligible": bool(study.get("eligible")),
                    "use_case_count": int(study.get("use_case_count") or 0),
                    "use_case_inventory_path": study.get("use_case_inventory_path"),
                }
            )

        sectors: list[dict[str, Any]] = []
        for code, meta in sorted(taxonomy.items(), key=lambda pair: (pair[1]["industry_code"], pair[0])):
            company_rows = sorted(sector_companies.get(code, []), key=lambda row: str(row.get("company") or ""))
            eligible = [row for row in company_rows if row["eligible"]]
            rollup_path = self.root / "data" / "private" / "sector_rollups" / f"ICB-{code}.yaml"
            if rollup_path.is_file():
                benchmark_state = "consolidated"
                primary_action = "refresh_benchmark"
            elif len(eligible) >= 3:
                benchmark_state = "benchmark_ready"
                primary_action = "launch_benchmark"
            elif len(eligible) == 2:
                benchmark_state = "benchmark_edge"
                primary_action = "add_third_company"
            elif len(eligible) == 1:
                benchmark_state = "building"
                primary_action = "add_company"
            else:
                benchmark_state = "empty"
                primary_action = "add_contact"
            sectors.append(
                {
                    **meta,
                    "mapped_company_count": len(company_rows),
                    "eligible_study_count": len(eligible),
                    "benchmark_threshold": 3,
                    "benchmark_state": benchmark_state,
                    "primary_action": primary_action,
                    "benchmark_enabled": len(eligible) >= 3,
                    "third_company_cta": len(eligible) == 2,
                    "use_case_count": sum(row["use_case_count"] for row in company_rows),
                    "rollup_path": rollup_path.relative_to(self.root).as_posix() if rollup_path.is_file() else None,
                    "companies": company_rows,
                }
            )
        return {
            "schema_version": "0.6",
            "as_of": effective_date.isoformat(),
            "taxonomy": "ICB 5.0",
            "sector_count": len(sectors),
            "sectors": sectors,
        }

    def inventories(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        studies_root = self.root / "studies"
        if not studies_root.is_dir():
            return result
        for path in sorted(studies_root.glob("*/05b_use_case_inventory.yaml")):
            doc = _read_yaml(path)
            result.append(
                {
                    "study_id": doc.get("study_id") or path.parent.name,
                    "company": doc.get("company") or path.parent.name,
                    "company_id": doc.get("company_id"),
                    "inventory_version": doc.get("inventory_version"),
                    "use_case_count": len(doc.get("use_cases", []) or []),
                    "path": path.relative_to(self.root).as_posix(),
                    "use_cases": doc.get("use_cases", []) or [],
                }
            )
        return result
