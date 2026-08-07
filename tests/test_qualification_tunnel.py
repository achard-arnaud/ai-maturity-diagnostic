from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_study.py"
VALIDATE = ROOT / "scripts" / "validate_study.py"
PACKAGE = ROOT / "scripts" / "validate_package.py"


def run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


class QualificationTunnelTests(unittest.TestCase):
    def initialize(self, root: Path, offers: str = "all") -> Path:
        result = run(INIT, "Société Démo", "--date", "2026-07-23", "--root", root, "--offers", offers)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return root / "societe-demo-20260723"

    def test_package_and_fresh_study_are_valid(self) -> None:
        package = run(PACKAGE)
        self.assertEqual(package.returncode, 0, package.stdout + package.stderr)
        self.assertIn("RESULT: 0 error(s), 0 warning(s)", package.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp))
            result = run(VALIDATE, study)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("RESULT: 0 error(s), 0 warning(s)", result.stdout)

    def test_force_keeps_recoverable_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = self.initialize(root)
            first_manifest = load(study / "00_manifest.yaml")
            result = run(
                INIT,
                "Société Démo",
                "--date",
                "2026-07-23",
                "--root",
                root,
                "--offers",
                "OFFER-AF-01",
                "--force",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            backups = list(root.glob("societe-demo-20260723.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(load(backups[0] / "00_manifest.yaml"), first_manifest)

    def test_snapshot_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp), "OFFER-AF-01")
            manifest = load(study / "00_manifest.yaml")
            snapshot = study / manifest["product_snapshots"][0]["path"]
            snapshot.write_text(snapshot.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
            result = run(VALIDATE, study)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Snapshot checksum mismatch", result.stdout)

    def test_enterprise_product_leak_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp), "OFFER-AF-01")
            profile_path = study / "05_enterprise_demand_profile.yaml"
            profile = load(profile_path)
            profile["recommended_offer"] = "OFFER-AF-01"
            dump(profile_path, profile)
            result = run(VALIDATE, study)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden product-fit fields", result.stdout)

    def test_blocking_gate_overrides_high_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp), "OFFER-AF-01")
            fit_path = study / "06_product_fit_matrix.yaml"
            fit = load(fit_path)
            fit["decision"] = "pursue"
            fit["recommended_offer_id"] = "OFFER-AF-01"
            fit["matches"] = [
                {
                    "offer_id": "OFFER-AF-01",
                    "product_profile_version": "2026-07-23.v0.2",
                    "problem_fit": 5,
                    "strategic_relevance": 5,
                    "urgency": 5,
                    "gap_fit": 5,
                    "technical_fit": 5,
                    "organizational_fit": 5,
                    "access_fit": 5,
                    "proofability": 5,
                    "evidence_confidence": 5,
                    "hard_gates": [
                        {
                            "id": "AF-GATE-03",
                            "status": "FAIL",
                            "severity": "blocker",
                        }
                    ],
                    "score": 100,
                    "decision": "pursue",
                    "invalidators": ["Required tool access remains impossible"],
                }
            ]
            dump(fit_path, fit)
            result = run(VALIDATE, study)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PURSUE is forbidden", result.stdout)

    def test_top_level_decision_and_weighted_score_must_match_selected_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp), "OFFER-AF-01")
            fit_path = study / "06_product_fit_matrix.yaml"
            fit = load(fit_path)
            fit["recommended_offer_id"] = "OFFER-AF-01"
            fit["decision"] = "validate"
            fit["matches"] = [
                {
                    "offer_id": "OFFER-AF-01",
                    "product_profile_version": "2026-07-23.v0.2",
                    "problem_fit": 0,
                    "strategic_relevance": 0,
                    "urgency": 0,
                    "gap_fit": 0,
                    "technical_fit": 0,
                    "organizational_fit": 0,
                    "access_fit": 0,
                    "proofability": 0,
                    "evidence_confidence": 0,
                    "hard_gates": [{"id": "AF-GATE-03", "status": "FAIL", "severity": "blocker"}],
                    "score": 0,
                    "decision": "disqualify",
                    "invalidators": [],
                }
            ]
            dump(fit_path, fit)
            result = run(VALIDATE, study)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Top-level decision must equal", result.stdout)

            manifest = load(study / "00_manifest.yaml")
            manifest["company_id"] = "COMP-DEMO"
            dump(study / "00_manifest.yaml", manifest)
            target = run(ROOT / "scripts" / "target_study_contacts.py", study, "--data-root", Path(tmp) / "private")
            self.assertNotEqual(target.returncode, 0)

    def test_stored_fit_score_must_equal_canonical_weighting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            study = self.initialize(Path(tmp), "OFFER-AF-01")
            fit_path = study / "06_product_fit_matrix.yaml"
            fit = load(fit_path)
            fit["recommended_offer_id"] = "OFFER-AF-01"
            fit["decision"] = "validate"
            fit["matches"] = [
                {
                    "offer_id": "OFFER-AF-01",
                    "product_profile_version": "2026-07-23.v0.2",
                    "problem_fit": 4, "strategic_relevance": 4, "urgency": 3, "gap_fit": 4,
                    "technical_fit": 3, "organizational_fit": 3, "access_fit": 4,
                    "proofability": 3, "evidence_confidence": 3,
                    "hard_gates": [{"id": "AF-GATE-03", "status": "OPEN", "severity": "blocker"}],
                    "score": 99,
                    "decision": "validate",
                    "invalidators": ["Access cannot be established"],
                }
            ]
            dump(fit_path, fit)
            result = run(VALIDATE, study)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not equal weighted score 72", result.stdout)


if __name__ == "__main__":
    unittest.main()
