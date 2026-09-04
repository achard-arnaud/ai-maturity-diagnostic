from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class EntityTwoPagerContractTests(unittest.TestCase):
    def test_atomic_contracts_exist_and_are_separate(self) -> None:
        expected = {
            "company_intelligence_atom.schema.yaml": "company",
            "external_product_intelligence_atom.schema.yaml": "external_product",
            "person_intelligence_atom.schema.yaml": "person",
        }
        for filename, entity_type in expected.items():
            path = ROOT / "contracts" / filename
            self.assertTrue(path.is_file(), filename)
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIn("atom_id", data["required"])
            self.assertEqual(entity_type, data["contract"]["entity_type"]["const"])

    def test_external_product_contract_cannot_be_confused_with_internal_offer_truth(self) -> None:
        path = ROOT / "contracts" / "external_product_intelligence_atom.schema.yaml"
        text = path.read_text(encoding="utf-8")
        self.assertIn("MUST NOT be written to product_catalog/", text)
        self.assertIn("contracts/product_profile.schema.yaml", text)
        data = yaml.safe_load(text)
        self.assertEqual(["core", "material", "supporting", "incidental"], data["contract"]["materiality"]["enum"])

    def test_assembly_contract_forces_product_spotlight_on_page_two(self) -> None:
        path = ROOT / "contracts" / "executive_entity_brief.schema.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertIn("product_spotlights", data["contract"]["page_2"]["required"])
        rules = "\n".join(data["rules"])
        self.assertIn("core or material", rules)
        self.assertIn("page_2.product_spotlights", rules)

    def test_skill_metaprompt_preserves_material_products(self) -> None:
        skill = (ROOT / "skills" / "executive-entity-briefing" / "SKILL.md").read_text(encoding="utf-8")
        prompt = (ROOT / "skills" / "executive-entity-briefing" / "references" / "metaprompt.md").read_text(encoding="utf-8")
        for term in ("core", "material", "product_spotlights", "product_catalog"):
            self.assertIn(term, skill)
        self.assertIn("Product spotlight(s)", prompt)
        self.assertIn("page 2", prompt.lower())

    def test_nice_template_is_exactly_two_pages(self) -> None:
        manifest = json.loads((ROOT / "skills" / "nice-output-engine" / "templates" / "manifest.json").read_text(encoding="utf-8"))
        config = manifest["templates"]["entity-two-pager"]
        self.assertEqual([2, 2], config["page_range"])

        example = json.loads((ROOT / "skills" / "nice-output-engine" / "examples" / "entity-two-pager" / "entity-two-pager.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(example["pages"]))
        page_two = json.dumps(example["pages"][1], ensure_ascii=False).lower()
        self.assertIn("product spotlight", page_two)

    def test_trigger_eval_is_balanced(self) -> None:
        items = json.loads((ROOT / "evals" / "trigger_eval_executive-entity-briefing.json").read_text(encoding="utf-8"))
        self.assertEqual(20, len(items))
        self.assertEqual(10, sum(item["should_trigger"] is True for item in items))
        self.assertEqual(10, sum(item["should_trigger"] is False for item in items))


if __name__ == "__main__":
    unittest.main()
