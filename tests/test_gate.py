from __future__ import annotations

import json
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from shared.gate import (
    Confidence,
    EncounterEvidence,
    FindingStatus,
    ProviderEvidence,
    Verdict,
    evaluate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
RULE = json.loads((ROOT / "fixtures/rules/tx-neurotoxin.json").read_text(encoding="utf-8"))


def clear_provider() -> ProviderEvidence:
    return ProviderEvidence(
        provider_id="SYN-PROV-RN-TEST",
        credential="RN",
        license_state="TX",
        license_status="ACTIVE",
        license_expires_on=date(2027, 12, 31),
        license_confidence=Confidence.HIGH,
        disciplinary_status="CLEAR",
        training_documented=True,
        complication_training_documented=True,
    )


def clear_encounter() -> EncounterEvidence:
    return EncounterEvidence(
        encounter_id="SYN-ENC-TEST",
        jurisdiction="TX",
        procedure="NEUROTOXIN_INJECTION",
        scheduled_on=date(2026, 8, 20),
        delegation_document_present=True,
        protocol_signed_and_dated=True,
        delegating_physician_active=True,
        patient_specific_order_present=True,
        order_contains_drug_dose_strength_route=True,
        practitioner_patient_relationship_established=True,
        adequate_medical_record_present=True,
        performer_identity_disclosed=True,
        bls_person_present=True,
        supervisor_onsite=False,
        supervisor_immediately_available=True,
        physician_emergency_appointment_available=True,
        product_lot_verified=True,
        product_lot_alerted=False,
        product_lot_confidence=Confidence.HIGH,
        comprehension_recorded=True,
        comprehension_score=4,
        comprehension_threshold=4,
        comprehension_confidence=Confidence.HIGH,
    )


class GateTests(unittest.TestCase):
    def test_rn_with_complete_evidence_is_clear(self):
        decision = evaluate_gate(clear_provider(), clear_encounter(), RULE)
        self.assertEqual(Verdict.CLEAR, decision.verdict)
        self.assertEqual(7, len(decision.findings))
        self.assertTrue(all(item.status is FindingStatus.PASS for item in decision.findings))
        self.assertEqual("Pre-procedure safety determination for human review", decision.determination_scope)

    def test_aesthetician_without_delegation_is_blocked_but_title_is_reviewed(self):
        provider = replace(
            clear_provider(),
            credential="AESTHETICIAN",
            training_documented=False,
            complication_training_documented=False,
        )
        encounter = replace(
            clear_encounter(),
            delegation_document_present=False,
            protocol_signed_and_dated=False,
            delegating_physician_active=False,
            patient_specific_order_present=False,
            order_contains_drug_dose_strength_route=False,
            practitioner_patient_relationship_established=False,
            adequate_medical_record_present=False,
            performer_identity_disclosed=False,
            bls_person_present=False,
            supervisor_immediately_available=False,
            physician_emergency_appointment_available=False,
        )
        decision = evaluate_gate(provider, encounter, RULE)
        statuses = {finding.check_id: finding.status for finding in decision.findings}
        self.assertEqual(Verdict.BLOCKED, decision.verdict)
        self.assertEqual(FindingStatus.REVIEW, statuses["authority_pathway"])
        self.assertEqual(FindingStatus.BLOCK, statuses["delegation_and_supervision"])

    def test_low_confidence_input_routes_to_review(self):
        encounter = replace(clear_encounter(), product_lot_confidence=Confidence.LOW)
        decision = evaluate_gate(clear_provider(), encounter, RULE)
        self.assertEqual(Verdict.REVIEW, decision.verdict)
        self.assertEqual(FindingStatus.REVIEW, decision.findings[4].status)

    def test_each_of_the_seven_checks_can_prevent_clear(self):
        cases = [
            ("provider_license", replace(clear_provider(), license_status="EXPIRED"), clear_encounter(), FindingStatus.BLOCK),
            ("authority_pathway", replace(clear_provider(), training_documented=False), clear_encounter(), FindingStatus.BLOCK),
            ("delegation_and_supervision", clear_provider(), replace(clear_encounter(), delegation_document_present=False), FindingStatus.BLOCK),
            ("preprocedure_assessment", clear_provider(), replace(clear_encounter(), adequate_medical_record_present=False), FindingStatus.BLOCK),
            ("product_lot", clear_provider(), replace(clear_encounter(), product_lot_alerted=True), FindingStatus.BLOCK),
            ("comprehension", clear_provider(), replace(clear_encounter(), comprehension_score=3), FindingStatus.BLOCK),
            ("disciplinary_status", replace(clear_provider(), disciplinary_status="ACTION"), clear_encounter(), FindingStatus.BLOCK),
        ]
        for check_id, provider, encounter, expected in cases:
            with self.subTest(check_id=check_id):
                decision = evaluate_gate(provider, encounter, RULE)
                finding = next(item for item in decision.findings if item.check_id == check_id)
                self.assertEqual(expected, finding.status)
                self.assertEqual(Verdict.BLOCKED, decision.verdict)
                self.assertTrue(finding.citation_urls)
                self.assertTrue(finding.facts)

    def test_low_confidence_has_precedence_over_apparent_pass(self):
        provider = replace(clear_provider(), license_confidence=Confidence.LOW)
        encounter = replace(clear_encounter(), comprehension_confidence=Confidence.LOW)
        decision = evaluate_gate(provider, encounter, RULE)
        review_checks = {item.check_id for item in decision.findings if item.status is FindingStatus.REVIEW}
        self.assertEqual({"provider_license", "comprehension"}, review_checks)
        self.assertEqual(Verdict.REVIEW, decision.verdict)

    def test_rule_snapshot_is_canonical_and_tamper_evident(self):
        first = evaluate_gate(clear_provider(), clear_encounter(), RULE)
        reordered = dict(reversed(list(RULE.items())))
        second = evaluate_gate(clear_provider(), clear_encounter(), reordered)
        self.assertEqual(first.rule_snapshot_json, second.rule_snapshot_json)
        self.assertEqual(first.rule_snapshot_sha256, second.rule_snapshot_sha256)
        self.assertEqual(64, len(first.rule_snapshot_sha256))

    def test_gate_collects_all_findings_without_short_circuiting(self):
        provider = replace(clear_provider(), license_status="EXPIRED", disciplinary_status="ACTION")
        encounter = replace(clear_encounter(), product_lot_alerted=True, comprehension_recorded=False)
        decision = evaluate_gate(provider, encounter, RULE)
        self.assertEqual(7, len(decision.findings))
        self.assertGreaterEqual(sum(item.status is FindingStatus.BLOCK for item in decision.findings), 4)


if __name__ == "__main__":
    unittest.main()

