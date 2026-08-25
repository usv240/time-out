from __future__ import annotations

import unittest

from before.app.integrations import ALL_ADAPTERS, seed_all_caches
from before.app.service import BeforeService, RECEIPT_BOUNDARY, WorkflowError


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_all_caches()

    def setUp(self):
        self.service = BeforeService(offline=True)
        self.service.seed()

    def test_complete_offline_hero_path_reaches_verified_sealed_receipt(self):
        result = self.service.run_hero_path()
        encounter = result["encounter"]
        receipt = result["timeline"][-1]["result"]
        self.assertEqual("SEALED", encounter["state"])
        self.assertEqual(14, len(result["timeline"]))
        self.assertTrue(all(task["status"] == "RESOLVED" for task in encounter["review_tasks"]))
        self.assertTrue(self.service.verify_receipt(receipt["receipt_hash"])["verified"])
        self.assertIn("does not certify legality", receipt["boundary"])

    def test_consent_waits_for_exactly_two_treatment_party_signatures(self):
        encounter_id = "SYN-ENC-CLEAR-001"
        self.assertEqual("CLEAR", self.service.evaluate(encounter_id)["verdict"])
        consent = self.service.compile_consent(encounter_id)
        encounter = self.service.get_encounter(encounter_id)
        self.assertEqual("AWAITING_SIGNATURES", consent["status"])
        self.assertEqual("PENDING", consent["signature_status"])
        self.assertEqual("HUMAN_REVIEW", encounter["state"])
        self.assertEqual("TREATMENT_PARTY_SIGNATURES", encounter["review_tasks"][-1]["kind"])
        with self.assertRaises(WorkflowError):
            self.service.record_comprehension(encounter_id, [])
        with self.assertRaises(WorkflowError):
            self.service.record_consent_signatures(encounter_id, ["Patient", "Medical Director"])
        signed = self.service.record_consent_signatures(
            encounter_id,
            ["Patient", "Injector"],
            envelope_id=consent["envelope_id"],
        )
        self.assertEqual("COMPLETED", signed["signature_status"])
        self.assertEqual("CONSENT_COMPILED", self.service.get_encounter(encounter_id)["state"])

    def test_every_transition_is_audited_and_sequence_is_reversible(self):
        result = self.service.run_hero_path()
        encounter = result["encounter"]
        actions = [item["action"] for item in encounter["audit_events"]]
        self.assertIn("alert_candidate_raised", actions)
        self.assertIn("alert_candidate_dismissed", actions)
        raised = next(item for item in encounter["audit_events"] if item["action"] == "alert_candidate_raised")
        self.assertEqual("READY_FOR_PROCEDURE", raised["from_state"])
        self.assertEqual("HUMAN_REVIEW", raised["to_state"])
        self.assertTrue(all(item["payload_hash"] and len(item["payload_hash"]) == 64 for item in encounter["audit_events"]))

    def test_invalid_transition_cannot_skip_human_attestation(self):
        with self.assertRaises(WorkflowError):
            self.service.attest("SYN-ENC-CLEAR-001")

    def test_blocked_encounter_cannot_produce_receipt(self):
        self.service.evaluate("SYN-ENC-BLOCKED-002")
        with self.assertRaises(WorkflowError):
            self.service.seal_receipt("SYN-ENC-BLOCKED-002")

    def test_decision_reproduces_after_documented_remediation(self):
        encounter_id = "SYN-ENC-BLOCKED-002"
        self.service.evaluate(encounter_id)
        self.service.remediate(
            encounter_id,
            {
                "provider_id": "SYN-PROV-RN-002",
                "delegation_document_present": True,
                "protocol_signed_and_dated": True,
                "delegating_physician_active": True,
                "patient_specific_order_present": True,
                "order_contains_drug_dose_strength_route": True,
                "practitioner_patient_relationship_established": True,
                "adequate_medical_record_present": True,
                "performer_identity_disclosed": True,
                "bls_person_present": True,
                "supervisor_immediately_available": True,
                "physician_emergency_appointment_available": True,
            },
        )
        decision = self.service.evaluate(encounter_id)
        self.assertEqual("CLEAR", decision["verdict"])
        self.assertTrue(self.service.reproduce_decision(encounter_id)["identical"])

    def test_all_integration_adapters_replay_typed_cache(self):
        for adapter_type in ALL_ADAPTERS:
            with self.subTest(vendor=adapter_type.vendor):
                result = adapter_type(offline=True).run()
                self.assertTrue(result.vendor)

    def test_receipt_boundary_remains_bounded(self):
        self.assertIn("does not certify legality", RECEIPT_BOUNDARY)
        self.assertIn("product authenticity", RECEIPT_BOUNDARY)
        self.assertIn("outcome", RECEIPT_BOUNDARY)


if __name__ == "__main__":
    unittest.main()
