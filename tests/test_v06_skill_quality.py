from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
V06_SKILLS = ("enterprise-use-case-intelligence", "use-case-nudging")


class V06SkillQualityTests(unittest.TestCase):
    def test_agent_metadata_is_complete(self) -> None:
        for skill in V06_SKILLS:
            path = ROOT / "skills" / skill / "agents" / "openai.yaml"
            self.assertTrue(path.is_file(), skill)
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            interface = data["interface"]
            for field in ("display_name", "short_description", "default_prompt"):
                self.assertTrue(str(interface.get(field) or "").strip(), f"{skill}:{field}")
            self.assertIn(f"${skill}", interface["default_prompt"])

    def test_trigger_evals_are_balanced(self) -> None:
        for skill in V06_SKILLS:
            path = ROOT / "evals" / f"trigger_eval_{skill}.json"
            items = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(20, len(items), skill)
            self.assertEqual(10, sum(item.get("should_trigger") is True for item in items), skill)
            self.assertEqual(10, sum(item.get("should_trigger") is False for item in items), skill)
            queries = [item.get("query") for item in items]
            self.assertTrue(all(isinstance(query, str) and query.strip() for query in queries), skill)
            self.assertEqual(len(queries), len(set(queries)), skill)

    def test_nudging_skill_declares_forbidden_contexts(self) -> None:
        text = (ROOT / "skills/use-case-nudging/SKILL.md").read_text(encoding="utf-8").lower()
        for forbidden in ("icb", "sector rollups", "05_enterprise_demand_profile", "product catalog", "06_product_fit_matrix"):
            self.assertIn(forbidden.lower(), text)


if __name__ == "__main__":
    unittest.main()
