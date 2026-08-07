from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load(relative: str) -> dict:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


class LinkedInDeferredDesignTests(unittest.TestCase):
    def test_design_contracts_are_traceable_and_read_only(self) -> None:
        result = run("validate_linkedin_design.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        evidence = load("contracts/linkedin_connector_evidence.schema.yaml")
        action = evidence["properties"]["policy"]["properties"]["action_class"]
        self.assertEqual(action["const"], "read")
        Draft202012Validator.check_schema(evidence)
        required = set(evidence["required"])
        self.assertTrue({"request_id", "acquisition_method", "authorization_program", "limitations"}.issubset(required))

        trace = load("artifacts/linkedin_prd_traceability.yaml")
        self.assertEqual(len(trace["items"]), 15)
        self.assertEqual(trace["policy"]["runtime_status"], "not_implemented")

    def test_plugin_disabled_core_remains_valid(self) -> None:
        self.assertFalse((ROOT / "plugins" / "linkedin-qualification-adapter").exists())
        self.assertFalse((ROOT / "skills" / "linkedin-capability-routing").exists())
        self.assertFalse((ROOT / "skills" / "linkedin-role-validation").exists())
        package = run("validate_package.py")
        self.assertEqual(package.returncode, 0, package.stdout + package.stderr)

    def test_external_evidence_cannot_be_canonical_truth(self) -> None:
        mapping = load("contracts/external_identity_mapping.schema.yaml")
        rules = " ".join(mapping["x-rules"]).lower()
        self.assertIn("never replace internal ids", rules)

        observation = load("contracts/relationship_observation.schema.yaml")
        self.assertIn("merge_decision", observation["required"])
        self.assertEqual(
            observation["properties"]["merge_decision"]["enum"],
            ["accepted", "human_review", "rejected"],
        )


if __name__ == "__main__":
    unittest.main()
