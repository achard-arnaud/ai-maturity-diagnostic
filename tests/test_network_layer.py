from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


CONTACTS = """Name\tJob title\tCompany\tCountry
Alice Martin\tCIO\tEDF\tFrance
Bob Durand\tCISO\tEDF\tFrance
Claire Petit\tHead of AI\tEDF\tFrance
David Robert\tTransformation Program Director\tEDF\tFrance
Eva Simon\tHead of Data\tOrange\tFrance
Farid Bernard\tCIO\tVille de Test\tFrance
"""


class NetworkLayerTests(unittest.TestCase):
    def build_network(self, root: Path) -> tuple[Path, dict[str, dict]]:
        source = root / "contacts.tsv"
        source.write_text(CONTACTS, encoding="utf-8")
        data_root = root / "private"
        for script, args in (
            ("import_contacts.py", (source, "--data-root", data_root, "--batch-date", "2026-07-23")),
            ("map_companies_icb.py", ("--data-root", data_root)),
            ("screen_network_accounts.py", ("--data-root", data_root)),
        ):
            result = run(script, *args)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        companies = {
            item["canonical_name"]: item for item in read_jsonl(data_root / "network" / "companies.jsonl")
        }
        return data_root, companies

    def test_intake_icb_screening_and_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root, companies = self.build_network(root)
            self.assertEqual(len(read_jsonl(data_root / "network" / "people.jsonl")), 6)
            self.assertEqual(len(companies), 3)
            self.assertEqual(companies["EDF"]["icb_mapping"]["sector"]["code"], "651010")
            self.assertEqual(companies["Orange"]["icb_mapping"]["sector"]["code"], "151020")
            self.assertEqual(companies["Ville de Test"]["icb_mapping"]["mapping_status"], "out_of_scope")
            queue = run(
                "sync_study_queue.py",
                "--data-root",
                data_root,
                "--studies-root",
                root / "studies",
                "--date",
                "2026-07-23",
            )
            self.assertEqual(queue.returncode, 0, queue.stdout + queue.stderr)
            entries = load_yaml(data_root / "network" / "study_queue.yaml")["entries"]
            edf = next(item for item in entries if item["company_id"] == companies["EDF"]["company_id"])
            self.assertEqual(edf["action"], "create")
            validation = run("validate_network.py", "--data-root", data_root)
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_same_name_at_two_companies_remains_two_provisional_people(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "homonyms.tsv"
            source.write_text(
                "Name\tJob title\tCompany\tCountry\n"
                "Alex Martin\tCIO\tEDF\tFrance\n"
                "Alex Martin\tCIO\tOrange\tFrance\n",
                encoding="utf-8",
            )
            data_root = root / "private"
            imported = run("import_contacts.py", source, "--data-root", data_root, "--batch-date", "2026-07-23")
            self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
            people = read_jsonl(data_root / "network" / "people.jsonl")
            self.assertEqual(len(people), 2)
            self.assertEqual({item["identity_key_basis"] for item in people}, {"normalized_name_and_company"})
            self.assertEqual(len({item["seed_company_id"] for item in people}), 2)

    def test_network_validator_rejects_invalid_score_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root, _ = self.build_network(root)
            path = data_root / "network" / "account_screening.jsonl"
            records = read_jsonl(path)
            records[0]["score"] = "INVALID"
            write_jsonl(path, records)
            validation = run("validate_network.py", "--data-root", data_root)
            self.assertNotEqual(validation.returncode, 0)
            self.assertIn("score must be numeric", validation.stdout)

    def test_fit_then_person_targeting_then_reach_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root, companies = self.build_network(root)
            studies = root / "studies"
            company = companies["EDF"]
            init = run(
                "init_study.py",
                "EDF",
                "--company-id",
                company["company_id"],
                "--date",
                "2026-07-23",
                "--root",
                studies,
                "--offers",
                "OFFER-AF-01",
            )
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            study = studies / "edf-20260723"

            profile_path = study / "05_enterprise_demand_profile.yaml"
            profile = load_yaml(profile_path)
            profile["evidence_claims"] = [{"claim_id": "C001", "statement": "Delivery pressure is evidenced."}]
            profile["strategic_priorities"] = [{"claim_id": "C002", "statement": "Accelerate engineering delivery."}]
            profile["capability_gaps"] = [{"claim_id": "C003", "statement": "Collective workflow execution remains constrained."}]
            profile["confidence"] = "medium"
            dump_yaml(profile_path, profile)

            fit_path = study / "06_product_fit_matrix.yaml"
            fit = load_yaml(fit_path)
            fit["recommended_offer_id"] = "OFFER-AF-01"
            fit["decision"] = "validate"
            fit["matches"] = [
                {
                    "offer_id": "OFFER-AF-01",
                    "product_profile_version": "2026-07-23.v0.2",
                    "problem_fit": 4,
                    "strategic_relevance": 4,
                    "urgency": 3,
                    "gap_fit": 4,
                    "technical_fit": 3,
                    "organizational_fit": 3,
                    "access_fit": 4,
                    "proofability": 3,
                    "evidence_confidence": 3,
                    "hard_gates": [{"id": "AF-GATE-03", "status": "OPEN", "severity": "blocker"}],
                    "score": 72,
                    "decision": "validate",
                    "invalidators": ["Required access is impossible"],
                }
            ]
            dump_yaml(fit_path, fit)

            target = run("target_study_contacts.py", study, "--data-root", data_root)
            self.assertEqual(target.returncode, 0, target.stdout + target.stderr)
            targets = load_yaml(study / "06b_contact_targets.yaml")["targets"]
            self.assertGreaterEqual(len(targets), 2)
            reach = run("build_reach_hypotheses.py", study)
            self.assertEqual(reach.returncode, 0, reach.stdout + reach.stderr)
            first = load_yaml(study / "07b_reach_hypotheses.yaml")["hypotheses"][0]
            self.assertEqual(first["status"], "blocked")
            self.assertIn("Dated validation of the contact's current role", first["missing_inputs"])

            relationships_path = data_root / "network" / "relationships.jsonl"
            relationships = read_jsonl(relationships_path)
            for relationship in relationships:
                if relationship["company_id"] == company["company_id"]:
                    relationship["current_status"] = "current"
                    relationship["requires_validation"] = False
                    relationship["observed_at"] = "2026-07-23"
            write_jsonl(relationships_path, relationships)
            rerun = run("target_study_contacts.py", study, "--data-root", data_root)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            reach = run("build_reach_hypotheses.py", study)
            self.assertEqual(reach.returncode, 0, reach.stdout + reach.stderr)
            hypotheses = load_yaml(study / "07b_reach_hypotheses.yaml")["hypotheses"]
            self.assertGreater(sum(item["status"] == "ready" for item in hypotheses), 0)

    def test_sector_rollup_requires_and_accepts_three_complete_studies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sector.tsv"
            source.write_text(
                "Name\tJob title\tCompany\tCountry\n"
                "Alpha One\tCIO\tEDF Alpha\tFrance\n"
                "Beta Two\tCIO\tEDF Beta\tFrance\n"
                "Gamma Three\tCIO\tEDF Gamma\tFrance\n",
                encoding="utf-8",
            )
            data_root = root / "private"
            imported = run("import_contacts.py", source, "--data-root", data_root, "--batch-date", "2026-07-23")
            self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
            mapped = run("map_companies_icb.py", "--data-root", data_root)
            self.assertEqual(mapped.returncode, 0, mapped.stdout + mapped.stderr)
            companies = read_jsonl(data_root / "network" / "companies.jsonl")
            studies = root / "studies"
            for index, company in enumerate(companies, start=1):
                study = studies / f"study-{index}"
                study.mkdir(parents=True)
                dump_yaml(
                    study / "00_manifest.yaml",
                    {
                        "schema_version": "0.2",
                        "study_id": f"study-{index}",
                        "company_id": company["company_id"],
                        "company": company["canonical_name"],
                        "updated_at": "2026-07-23",
                    },
                )
                dump_yaml(
                    study / "05_enterprise_demand_profile.yaml",
                    {
                        "schema_version": "0.2",
                        "study_id": f"study-{index}",
                        "company": company["canonical_name"],
                        "evidence_claims": [{"claim_id": f"C{index}01", "statement": "A supported fact."}],
                        "strategic_priorities": [{"claim_id": f"C{index}02", "statement": "Grid modernization."}],
                        "capability_gaps": [{"claim_id": f"C{index}03", "statement": "Delivery capacity gap."}],
                        "confidence": "medium",
                    },
                )
            rollup = run(
                "build_sector_rollups.py",
                "--data-root",
                data_root,
                "--studies-root",
                studies,
                "--date",
                "2026-07-23",
            )
            self.assertEqual(rollup.returncode, 0, rollup.stdout + rollup.stderr)
            output = load_yaml(data_root / "sector_rollups" / "ICB-651010.yaml")
            self.assertEqual(len(output["covered_accounts"]), 3)
            self.assertEqual(output["next_skill"], "sector-intelligence-consolidation")
            self.assertEqual(output["classification_basis"], "candidate")
            self.assertEqual(output["publication_status"], "exploratory")
            self.assertTrue(all(item["icb_mapping_status"] == "candidate" for item in output["covered_accounts"]))

    def test_future_dated_study_is_not_sector_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sector.tsv"
            source.write_text(
                "Name\tJob title\tCompany\tCountry\n"
                "Alpha One\tCIO\tEDF Alpha\tFrance\n"
                "Beta Two\tCIO\tEDF Beta\tFrance\n"
                "Gamma Three\tCIO\tEDF Gamma\tFrance\n",
                encoding="utf-8",
            )
            data_root = root / "private"
            self.assertEqual(run("import_contacts.py", source, "--data-root", data_root, "--batch-date", "2026-07-23").returncode, 0)
            self.assertEqual(run("map_companies_icb.py", "--data-root", data_root).returncode, 0)
            companies = read_jsonl(data_root / "network" / "companies.jsonl")
            studies = root / "studies"
            for index, company in enumerate(companies, start=1):
                study = studies / f"study-{index}"
                study.mkdir(parents=True)
                updated = "2026-07-24" if index == 1 else "2026-07-23"
                dump_yaml(study / "00_manifest.yaml", {"study_id": f"study-{index}", "company_id": company["company_id"], "updated_at": updated})
                dump_yaml(
                    study / "05_enterprise_demand_profile.yaml",
                    {"evidence_claims": [{"claim_id": "C1"}], "capability_gaps": [{"claim_id": "C2"}], "confidence": "medium"},
                )
            rollup = run("build_sector_rollups.py", "--data-root", data_root, "--studies-root", studies, "--date", "2026-07-23")
            self.assertEqual(rollup.returncode, 0, rollup.stdout + rollup.stderr)
            self.assertFalse((data_root / "sector_rollups" / "ICB-651010.yaml").exists())


if __name__ == "__main__":
    unittest.main()
