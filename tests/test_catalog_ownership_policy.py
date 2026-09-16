from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CatalogOwnershipPolicyTests(unittest.TestCase):
    def test_catalog_ownership_contract_matches_adr(self) -> None:
        contract = yaml.safe_load((ROOT / "contracts/catalog_ownership.schema.yaml").read_text(encoding="utf-8"))
        adr = (ROOT / "docs/ADR-008-product-catalog-ownership.md").read_text(encoding="utf-8")

        self.assertEqual(contract["properties"]["model"]["const"], "shared_core_workspace_overlay")
        self.assertIs(contract["properties"]["silent_shadowing"]["const"], False)
        self.assertIn("shared, read-only published catalog", adr)
        self.assertIn("Silent shadowing is forbidden", adr)
        self.assertIn("immutable snapshot IDs and hashes", adr)


if __name__ == "__main__":
    unittest.main()
