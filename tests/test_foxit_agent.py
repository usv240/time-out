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
            if "fileContent" in call.args:  # uploads: content must be redacted, never raw base64
                self.assertTrue(str(call.args["fileContent"]).startswith("<base64"))

    def test_attestation_default_is_draft_and_refuses_without_signer(self):
        import inspect, os
        # default must be a no-email draft; sending is an explicit human choice
        self.assertIs(inspect.signature(foxit_agent.request_attestation).parameters["send"].default, False)
        saved = os.environ.pop("FOXIT_ESIGN_MEDICAL_DIRECTOR_EMAIL", None)
        try:
            with self.assertRaises(foxit_agent.AgentError):
                foxit_agent.request_attestation()
        finally:
            if saved is not None:
                os.environ["FOXIT_ESIGN_MEDICAL_DIRECTOR_EMAIL"] = saved

    def test_esign_fixture_records_handoff_not_signature(self):
        """The envelope proves a handoff to a named human, never a signature by the agent.

        `sent` is deliberately not asserted either way: sending is a human decision
        (`request_attestation` defaults to send=False and emails nobody), so both
        states are legitimate. What must never drift is that the record names a
        human signer role and carries no claim that the agent applied a signature.
        """
        import json
        fixture = foxit_agent.ROOT / "fixtures" / "foxit" / "esign-folder.json"
        if not fixture.exists():
            self.skipTest("eSign fixture not present")
        record = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(record["signer_role"], "Medical Director")
        self.assertIn("folderId", record["folder"])
        self.assertIn("stopped", record["boundary_note"])
        self.assertNotIn("signature", record)
        self.assertNotIn("signed_by", record)

    def test_request_attestation_defaults_to_not_sending(self):
        """The default must never email a human. Sending has to be chosen explicitly."""
        import inspect
        default = inspect.signature(foxit_agent.request_attestation).parameters["send"].default
        self.assertIs(default, False)


if __name__ == "__main__":
    unittest.main()
