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


def test_doctavian_generated_consent_is_a_real_rendered_document() -> None:
    """The artifact Doctavian returned, not one we assembled.

    Every expression must be resolved: several unsupported expressions return HTTP 200
    and render blank, so a leftover `{!` — or a missing value — means we shipped a
    template the platform silently declined to fill.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    pdf = root / "before" / "doctavian" / "generated" / "tx-neurotoxin-consent.pdf"
    if not pdf.exists():
        import pytest
        pytest.skip("no generated consent committed")
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-")

    import fitz
    text = "".join(page.get_text() for page in fitz.open(pdf))
    assert "{!" not in text, "an expression was left unresolved in the generated document"
    assert "SYN-ENC-CLEAR-001" in text, "encounter data was not merged"
    assert "Disclosures cited for this encounter: 3" in text, "$count did not evaluate"
    for title in ("Temporary effect and alternatives", "Who will perform the procedure"):
        assert title in text, f"cited disclosure missing from the document: {title}"
    assert "synthetic" in text.lower()


def test_doctavian_data_contract_is_enforced_in_code() -> None:
    """Numbers and booleans make the template read fail, reported misleadingly.

    The payload must be one root `data` object with every scalar leaf a string. This is
    the contract that took longest to find, so it is pinned rather than remembered.
    """
    from before.doctavian_generate import _stringify
    out = _stringify({"a": 1, "b": True, "c": None, "d": [{"e": 2.5}]})
    assert out == {"a": "1", "b": "true", "c": "", "d": [{"e": "2.5"}]}
