from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from app.artifact_store import ArtifactStore

from app.core import ControlPlaneError, _read_yaml
from scripts.init_study import slugify
from scripts.network_common import utc_now


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
# TODO(red-team-spec): stale_after_days is a single flat constant for every
# sector/company; revisit once a second workspace onboards with a genuinely
# different demand-refresh cadence than the first customer's.
class DemandCatalog:
    root: Path
    stale_after_days: int = 180

    @classmethod
    def for_workspace(cls, workspace_id: str, repo_root: Path | None = None) -> "DemandCatalog":
        """Instantiate against a specific workspace (ADR-007 §5 step 1)."""
        from app.workspace_paths import resolve_workspace_root

        return cls(resolve_workspace_root(workspace_id, repo_root))

    def _find_study_dir(self, study_id: str) -> Path:
        studies_root = self.root / "studies"
        if studies_root.is_dir():
            for manifest_path in studies_root.glob("*/00_manifest.yaml"):
                manifest = _read_yaml(manifest_path)
                if str(manifest.get("study_id") or manifest_path.parent.name) == study_id:
                    return manifest_path.parent
        raise ControlPlaneError(f"unknown study_id: {study_id}")

    def create_demand_profile(
        self,
        *,
        company: str,
        problem_statement: str,
        company_id: str | None = None,
        sector_code: str | None = None,
        confidence: str = "low",
        study_id: str | None = None,
    ) -> dict[str, Any]:
        """Write a schema-conformant `05_enterprise_demand_profile.yaml`
        (contracts/enterprise_demand_profile.schema.yaml) from the minimum
        a human can type, closing the M2 gap: until now `DemandCatalog` had
        no write path at all (see the module-level TODO history and
        docs/red-team-side-story/trigger-journey-audit.md's M2 section) --
        onboarding a new account required hand-authoring this YAML offline.

        This is a plain structured-data form, not an agent/skill run: it
        never calls an LLM and never infers or fabricates content. Only
        `company` and `problem_statement` are required (matching the
        contract's own required fields plus the one free-text field a
        human can reasonably type off the top of their head). Every field
        the human did not supply is written as an honest empty
        list/`unknowns` entry, never a plausible-sounding guess -- compare
        app/catalog_promotion.py's promote_candidate, which follows the
        same discipline for a similarly human/harvest-entered record.

        Evidence-status choice: `problem_statement` becomes a single
        evidence_claims entry with `evidence_status: "hypothesis"` --
        mirroring promote_candidate's rule that a claim with no
        independent source is a hypothesis, not a vendor_claim (there is
        no source_url/raw_claims equivalent here since a human typed this
        directly into a form, with nothing to independently corroborate
        it yet).

        Study-directory collision handling (reusing scripts/init_study.py's
        conventions, not inventing a new layout):
        - `study_id` given: the target study must already exist (its
          `00_manifest.yaml` resolves it) -- this call overwrites *only*
          `05_enterprise_demand_profile.yaml` inside it. Use this for an
          existing company/study.
        - `study_id` omitted: a brand-new study directory is created using
          scripts/init_study.py's exact naming convention
          (`slugify(company)-YYYYMMDD`) plus a minimal
          `00_manifest.yaml` (from templates/study_manifest.yaml). If a
          directory with that name already exists, this raises
          ControlPlaneError rather than silently overwriting an unrelated
          study (same non-force default as scripts/init_study.py) -- the
          caller should retry with an explicit `study_id` if they meant to
          target that existing study.
        """

        company = str(company or "").strip()
        if not company:
            raise ControlPlaneError("company is required")
        problem_statement = str(problem_statement or "").strip()
        if not problem_statement:
            raise ControlPlaneError("problem_statement is required")
        confidence = str(confidence or "low").strip().lower()
        if confidence not in {"low", "medium", "high"}:
            raise ControlPlaneError("confidence must be one of: low, medium, high")

        now = utc_now()
        today = now[:10]

        if study_id:
            study_dir = self._find_study_dir(str(study_id).strip())
            resolved_study_id = str(study_id).strip()
        else:
            resolved_study_id = f"{slugify(company)}-{today.replace('-', '')}"
            study_dir = self.root / "studies" / resolved_study_id
            if study_dir.exists():
                raise ControlPlaneError(
                    f"study already exists: {resolved_study_id} "
                    "(pass study_id to target it explicitly instead of creating a new one)"
                )
            # templates/ lives at the repo root, not per-workspace (mirrors
            # scripts/init_study.py's `pkg = Path(__file__).resolve().parents[1]`).
            repo_root = Path(__file__).resolve().parents[1]
            template_path = repo_root / "templates" / "study_manifest.yaml"
            manifest = _read_yaml(template_path) if template_path.is_file() else {}
            manifest.update(
                {
                    "study_id": resolved_study_id,
                    "company_id": company_id,
                    "company": company,
                    "created_at": today,
                    "updated_at": today,
                }
            )
            study_dir.mkdir(parents=True)
            ArtifactStore(self.root).write_yaml(study_dir / "00_manifest.yaml", manifest)

        unknowns = [
            "Strategic priorities are unknown -- not captured by this intake form yet.",
            "Capability gaps are unknown -- not captured by this intake form yet.",
            "Buying context (sponsors, terrain owners, veto players, timing signals) is unknown.",
            "Constraints (technical, organizational, regulatory) are unknown.",
        ]
        if not sector_code:
            unknowns.append("Sector (ICB code) is unknown -- not supplied at intake time.")

        profile: dict[str, Any] = {
            "schema_version": "0.2",
            "study_id": resolved_study_id,
            "profile_version": "manual-intake.v0.1",
            "company": company,
            "evidence_claims": [
                {
                    "claim_id": "E1",
                    "statement": problem_statement,
                    "source": "manual_entry",
                    "evidence_status": "hypothesis",
                }
            ],
            "strategic_priorities": [],
            "capability_gaps": [],
            "buying_context": {
                "sponsors": [],
                "terrain_owners": [],
                "veto_players": [],
                "timing_signals": [],
            },
            "constraints": {
                "technical": [],
                "organizational": [],
                "regulatory": [],
            },
            "unknowns": unknowns,
            "confidence": confidence,
        }
        if sector_code:
            profile["sector_code"] = str(sector_code).strip()

        profile_path = study_dir / "05_enterprise_demand_profile.yaml"
        ArtifactStore(self.root).write_yaml(profile_path, profile)
        return {
            "study_id": resolved_study_id,
            "study_path": study_dir.relative_to(self.root).as_posix(),
            "profile_path": profile_path.relative_to(self.root).as_posix(),
            "profile": profile,
            "created_study": not bool(study_id),
        }

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
                "updated_date": updated,
                "current": current,
                "complete": complete,
                "eligible": current and complete,
                "use_case_count": len(inventory.get("use_cases", []) or []),
                "use_case_inventory_path": use_case_path.relative_to(self.root).as_posix() if use_case_path.is_file() else None,
            }
            prior = latest.get(str(company_id))
            prior_date = prior.get("updated_date") if prior else None
            if prior is None or (updated or date.min) >= (prior_date or date.min):
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
                    "study_updated_at": study.get("updated_at"),
                }
            )

        sectors: list[dict[str, Any]] = []
        for code, meta in sorted(taxonomy.items(), key=lambda pair: (pair[1]["industry_code"], pair[0])):
            company_rows = sorted(sector_companies.get(code, []), key=lambda row: str(row.get("company") or ""))
            eligible = [row for row in company_rows if row["eligible"]]
            study_updates = [row["study_updated_at"] for row in company_rows if row.get("study_updated_at")]
            most_recent_study_update = max(study_updates) if study_updates else None
            rollup_path = self.root / "data" / "private" / "sector_rollups" / f"ICB-{code}.yaml"
            rollup_exists = rollup_path.is_file()
            # A historical rollup is never sufficient to bypass the current >=3 eligibility gate.
            if len(eligible) >= 3 and rollup_exists:
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
                    "rollup_stale": rollup_exists and len(eligible) < 3,
                    "use_case_count": sum(row["use_case_count"] for row in company_rows),
                    "rollup_path": rollup_path.relative_to(self.root).as_posix() if rollup_exists else None,
                    "most_recent_study_update": most_recent_study_update,
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
