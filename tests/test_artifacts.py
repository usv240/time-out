from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_synthetic_evidence_record_is_committed_pdf(self):
        path = ROOT / "output" / "pdf" / "synthetic-safety-evidence-record.pdf"
        self.assertTrue(path.exists())
        self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
        self.assertGreater(path.stat().st_size, 5_000)

    def test_doctavian_template_and_vendor_contracts_are_present(self):
        for relative in (
            "before/doctavian/consent-template.json",
            "before/perfectcorp/capture-contract.json",
            "before/foxit/agent-contract.json",
            "before/namecom/receipt-dns-contract.json",
            "before/xano/api-contract.json",
        ):
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
