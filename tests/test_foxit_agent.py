import unittest
from before import foxit_agent


class FoxitAgentTests(unittest.TestCase):
    def test_plan_is_deterministic_and_names_the_boundary(self):
        enc, steps = foxit_agent.plan("assemble the safety record for encounter SYN-ENC-BLOCKED-002")
        self.assertEqual(enc, "SYN-ENC-BLOCKED-002")
        self.assertTrue(steps[-1].startswith("STOP"))

    def test_plan_rejects_prompt_without_encounter(self):
        with self.assertRaises(foxit_agent.AgentError):
            foxit_agent.plan("assemble something")

    def test_replay_pauses_at_boundary_and_records_workarounds(self):
        run = foxit_agent.run("x encounter SYN-ENC-BLOCKED-002", offline=True)
        self.assertTrue(run.paused_at_boundary)
        self.assertIsNotNone(run.output_sha256)
        tools = [c.tool for c in run.calls]
        self.assertGreaterEqual(tools.count("upload_document"), 3)
        self.assertIn("download_document", tools)
        self.assertTrue(any(t.startswith("REST pdf-combine") for t in tools))
        self.assertTrue(any(t.startswith("REST pdf-watermark") for t in tools))
        for call in run.calls:
            self.assertNotIn("fileContent", str(call.args).replace("<base64", ""))  # redacted

    def test_attestation_dry_run_never_sends(self):
        import os
        os.environ.setdefault("FOXIT_ESIGN_MEDICAL_DIRECTOR_EMAIL", "synthetic@example.test")
        if not foxit_agent.OUTPUT_PDF.exists():
            self.skipTest("assembled PDF not present")
        result = foxit_agent.request_attestation(dry_run=True)
        self.assertFalse(result["sent"])
        self.assertEqual(result["prepared"]["signer_role"], "Medical Director")


if __name__ == "__main__":
    unittest.main()
