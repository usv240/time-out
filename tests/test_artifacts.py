from __future__ import annotations

import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_synthetic_evidence_record_is_committed_pdf(self):
        path = ROOT / "output" / "pdf" / "synthetic-safety-evidence-record.pdf"
        self.assertTrue(path.exists())
        self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
        self.assertGreater(path.stat().st_size, 5_000)

    def test_doctavian_docx_contains_real_elements_and_distinct_signature_anchors(self):
        path = ROOT / "before" / "doctavian" / "tx-neurotoxin-consent-v1.docx"
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml").decode("utf-8")
            core_xml = archive.read("docProps/core.xml").decode("utf-8")
            timestamps = {item.date_time for item in archive.infolist()}
        for token in (
            "mdoc:paragraph",
            "mdoc:repeater",
            "$count(Encounter[0].RequiredDisclosures)",
            "_SIG_PATIENT_",
            "_SIG_INJECTOR_",
            "RuleSnapshotSha256",
        ):
            self.assertIn(token, document_xml)
        self.assertIn("Time-Out synthetic demo", core_xml)
        self.assertEqual({(2026, 8, 18, 0, 0, 0)}, timestamps)
    def test_doctavian_template_and_vendor_contracts_are_present(self):
        for relative in (
            "before/doctavian/consent-template.json",
            "before/doctavian/consent-data.synthetic.json",
            "before/doctavian/tx-neurotoxin-consent-v1.docx",
            "before/perfectcorp/capture-contract.json",
            "before/foxit/agent-contract.json",
            "before/namecom/receipt-dns-contract.json",
            "before/xano/api-contract.json",
        ):
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
