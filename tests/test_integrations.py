from __future__ import annotations

import json

import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

from before.app.integrations import (
    IntegrationError,
    NameComClient,
    NutrientClient,
    PerfectCorpClient,
    SerpApiClient,
    cache_manifest,
    redact_for_egress,
    seed_all_caches,
)


class IntegrationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_all_caches()

    def test_semantic_redaction_removes_identifier_fields_before_egress(self):
        source = {
            "patient_id": "SYN-PATIENT-001",
            "clinical": {"allergies": [], "email": "synthetic@example.invalid"},
            "document_type": "patient_intake",
        }
        redacted = redact_for_egress(source)
        self.assertEqual("[REDACTED]", redacted["patient_id"])
        self.assertEqual("[REDACTED]", redacted["clinical"]["email"])
        self.assertEqual("patient_intake", redacted["document_type"])

    def test_nutrient_bundle_routes_low_confidence_to_named_role(self):
        result = NutrientClient().run()
        self.assertEqual(3, len(result.extractions))
        self.assertTrue(result.review_required)
        self.assertEqual("Medical Director", result.assigned_role)
        self.assertTrue(result.redacted_before_egress)
        self.assertTrue(result.page_coordinates["lot"])

    def test_serpapi_has_both_fda_and_texas_board_queries(self):
        result = SerpApiClient().run()
        self.assertEqual(2, len(result.queries))
        self.assertEqual("CANDIDATE", result.status)
        self.assertIn("human", result.boundary.lower())

    def test_perfect_corp_uses_sd_and_matches_the_live_run(self):
        result = PerfectCorpClient().run()
        self.assertEqual("SD", result.mode)
        live = json.loads((ROOT / "fixtures" / "perfectcorp-live-run.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(live["concerns"]), sorted(result.concerns))  # real API output, not invented names
        self.assertEqual(12, len(result.concerns))
        self.assertIn("Not diagnosis", result.boundary)

    def test_namecom_contract_covers_four_surfaces_and_limits(self):
        result = NameComClient().run()
        self.assertGreaterEqual(len(result.operations), 5)
        self.assertTrue(result.mutable)
        self.assertIn("sandbox API", result.verified_through)

    def test_online_mode_refuses_to_invent_unconfigured_vendor_calls(self):
        with self.assertRaises(IntegrationError):
            NutrientClient(offline=False).run()

    def test_every_seeded_cache_has_a_manifest_hash(self):
        manifest = cache_manifest()
        self.assertEqual(6, len(manifest))
        self.assertTrue(all(len(value) == 64 for value in manifest.values()))


if __name__ == "__main__":
    unittest.main()
