"""Pure Texas neurotoxin Gate: evidence in, deterministic findings out."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .models import (
    Confidence,
    EncounterEvidence,
    Finding,
    FindingStatus,
    GateDecision,
    ProviderEvidence,
    Verdict,
)


DETERMINATION_SCOPE = "Pre-procedure safety determination for human review"


def _finding(
    check_id: str,
    status: FindingStatus,
    summary: str,
    citations: list[str],
    **facts: Any,
) -> Finding:
    return Finding(check_id, status, summary, tuple(citations), facts)


def _snapshot(rule: Mapping[str, Any]) -> tuple[str, str]:
    frozen = json.dumps(rule, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return frozen, hashlib.sha256(frozen.encode("utf-8")).hexdigest()


def evaluate_gate(
    provider: ProviderEvidence,
    encounter: EncounterEvidence,
    rule: Mapping[str, Any],
) -> GateDecision:
    """Return all seven findings without network calls or short-circuiting.

    The output is operational evidence for a human reviewer. It is not a legal
    opinion and intentionally refuses to infer missing or low-confidence facts.
    """

    findings: list[Finding] = []
    tmb = rule["citations"]["tmb_chapter_169"]
    bon = rule["citations"]["bon_rn_cosmetic_faq"]
    statute = rule["citations"]["occupations_code_157"]

    # 1. Active, in-state, unexpired professional licence.
    license_facts = {
        "state": provider.license_state,
        "license_status": provider.license_status,
        "expires_on": provider.license_expires_on.isoformat(),
        "scheduled_on": encounter.scheduled_on.isoformat(),
        "confidence": provider.license_confidence.value,
    }
    if provider.license_confidence is Confidence.LOW:
        findings.append(_finding("provider_license", FindingStatus.REVIEW, "Licence evidence is low-confidence.", [bon], **license_facts))
    elif provider.license_state != rule["jurisdiction"] or provider.license_status != "ACTIVE" or provider.license_expires_on < encounter.scheduled_on:
        findings.append(_finding("provider_license", FindingStatus.BLOCK, "Provider licence evidence is not active, in-state, and unexpired.", [bon], **license_facts))
    else:
        findings.append(_finding("provider_license", FindingStatus.PASS, "Provider licence evidence is active, in-state, and unexpired.", [bon], **license_facts))

    # 2. Credential/authority pathway. Texas does not publish a simple whitelist.
    credential = provider.credential.upper()
    credential_facts = {
        "credential": credential,
        "training_documented": provider.training_documented,
        "complication_training_documented": provider.complication_training_documented,
    }
    if credential in rule["direct_performer_credentials"]:
        findings.append(_finding("authority_pathway", FindingStatus.PASS, "Credential follows the direct physician pathway.", [tmb], **credential_facts))
    elif credential in rule["credential_interpretation_review"]:
        findings.append(_finding("authority_pathway", FindingStatus.REVIEW, "This title alone neither establishes nor disproves delegated authority; reviewer must assess the other licence and delegation rules.", [tmb, statute], **credential_facts))
    elif credential not in rule["delegated_path_credentials"]:
        findings.append(_finding("authority_pathway", FindingStatus.REVIEW, "Credential is not mapped to a reviewed Texas authority pathway.", [tmb, statute], **credential_facts))
    elif not provider.training_documented or not provider.complication_training_documented:
        findings.append(_finding("authority_pathway", FindingStatus.BLOCK, "Required procedure and complication-response training is not documented.", [tmb, bon], **credential_facts))
    else:
        findings.append(_finding("authority_pathway", FindingStatus.PASS, "Delegated-performer training evidence is documented.", [tmb, bon], **credential_facts))

    # 3. Delegation, written order, and supervision/availability.
    delegated = credential not in rule["direct_performer_credentials"]
    supervision_facts = {
        "delegation_required": delegated,
        "delegation_document_present": encounter.delegation_document_present,
        "protocol_signed_and_dated": encounter.protocol_signed_and_dated,
        "delegating_physician_active": encounter.delegating_physician_active,
        "patient_specific_order_present": encounter.patient_specific_order_present,
        "order_contains_drug_dose_strength_route": encounter.order_contains_drug_dose_strength_route,
        "supervisor_onsite": encounter.supervisor_onsite,
        "supervisor_immediately_available": encounter.supervisor_immediately_available,
        "physician_emergency_appointment_available": encounter.physician_emergency_appointment_available,
        "bls_person_present": encounter.bls_person_present,
    }
    if not delegated:
        findings.append(_finding("delegation_and_supervision", FindingStatus.PASS, "No delegation is asserted for the physician performer.", [tmb], **supervision_facts))
    else:
        required = (
            encounter.delegation_document_present,
            encounter.protocol_signed_and_dated,
            encounter.delegating_physician_active,
            encounter.patient_specific_order_present,
            encounter.order_contains_drug_dose_strength_route,
            encounter.bls_person_present,
            encounter.supervisor_onsite or encounter.supervisor_immediately_available,
            encounter.physician_emergency_appointment_available,
        )
        if all(required):
            findings.append(_finding("delegation_and_supervision", FindingStatus.PASS, "Delegation, order, BLS, and availability evidence is complete.", [tmb, bon, statute], **supervision_facts))
        else:
            findings.append(_finding("delegation_and_supervision", FindingStatus.BLOCK, "Delegation, order, BLS, or required availability evidence is incomplete.", [tmb, bon, statute], **supervision_facts))

    # 4. Use the current rule's explicit pre-procedure requirements; do not
    # silently equate them with the industry label "good-faith exam."
    assessment_facts = {
        "practitioner_patient_relationship_established": encounter.practitioner_patient_relationship_established,
        "adequate_medical_record_present": encounter.adequate_medical_record_present,
        "performer_identity_disclosed": encounter.performer_identity_disclosed,
        "good_faith_exam_label_status": rule["requires_good_faith_exam"],
    }
    if all((encounter.practitioner_patient_relationship_established, encounter.adequate_medical_record_present, encounter.performer_identity_disclosed)):
        findings.append(_finding("preprocedure_assessment", FindingStatus.PASS, "The explicit Chapter 169 pre-procedure evidence is present.", [tmb], **assessment_facts))
    else:
        findings.append(_finding("preprocedure_assessment", FindingStatus.BLOCK, "Practitioner-patient relationship, medical record, or performer disclosure evidence is missing.", [tmb], **assessment_facts))

    # 5. Product provenance is a safety control, not a Texas scope conclusion.
    lot_facts = {
        "verified": encounter.product_lot_verified,
        "alerted": encounter.product_lot_alerted,
        "confidence": encounter.product_lot_confidence.value,
    }
    if encounter.product_lot_confidence is Confidence.LOW:
        findings.append(_finding("product_lot", FindingStatus.REVIEW, "Product-lot evidence is low-confidence.", rule["product_safety_citations"], **lot_facts))
    elif not encounter.product_lot_verified or encounter.product_lot_alerted:
        findings.append(_finding("product_lot", FindingStatus.BLOCK, "Product lot is unverified or has an active alert.", rule["product_safety_citations"], **lot_facts))
    else:
        findings.append(_finding("product_lot", FindingStatus.PASS, "Product lot is verified and has no captured alert.", rule["product_safety_citations"], **lot_facts))

    # 6. Comprehension must be recorded and meet the configured threshold.
    comprehension_facts = {
        "recorded": encounter.comprehension_recorded,
        "score": encounter.comprehension_score,
        "threshold": encounter.comprehension_threshold,
        "confidence": encounter.comprehension_confidence.value,
    }
    if encounter.comprehension_confidence is Confidence.LOW:
        findings.append(_finding("comprehension", FindingStatus.REVIEW, "Comprehension evidence is low-confidence.", rule["comprehension_citations"], **comprehension_facts))
    elif not encounter.comprehension_recorded or encounter.comprehension_score is None or encounter.comprehension_score < encounter.comprehension_threshold:
        findings.append(_finding("comprehension", FindingStatus.BLOCK, "Comprehension was not recorded or did not meet the configured threshold.", rule["comprehension_citations"], **comprehension_facts))
    else:
        findings.append(_finding("comprehension", FindingStatus.PASS, "Comprehension evidence meets the configured threshold.", rule["comprehension_citations"], **comprehension_facts))

    # 7. Unknown status is reviewable; a captured action blocks the hero path.
    discipline_facts = {"disciplinary_status": provider.disciplinary_status}
    if provider.disciplinary_status == "CLEAR":
        findings.append(_finding("disciplinary_status", FindingStatus.PASS, "Captured disciplinary status is clear.", [bon], **discipline_facts))
    elif provider.disciplinary_status == "ACTION":
        findings.append(_finding("disciplinary_status", FindingStatus.BLOCK, "Captured disciplinary status reports an action.", [bon], **discipline_facts))
    else:
        findings.append(_finding("disciplinary_status", FindingStatus.REVIEW, "Disciplinary status is unknown or stale.", [bon], **discipline_facts))

    statuses = {finding.status for finding in findings}
    verdict = Verdict.BLOCKED if FindingStatus.BLOCK in statuses else Verdict.REVIEW if FindingStatus.REVIEW in statuses else Verdict.CLEAR
    snapshot_json, snapshot_sha256 = _snapshot(rule)
    return GateDecision(
        encounter_id=encounter.encounter_id,
        verdict=verdict,
        determination_scope=DETERMINATION_SCOPE,
        findings=tuple(findings),
        rule_snapshot_json=snapshot_json,
        rule_snapshot_sha256=snapshot_sha256,
    )
