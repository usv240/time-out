"""Typed evidence and result models for a human-reviewed safety determination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Mapping


class Verdict(str, Enum):
    CLEAR = "CLEAR"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"


class FindingStatus(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ProviderEvidence:
    provider_id: str
    credential: str
    license_state: str
    license_status: str
    license_expires_on: date
    license_confidence: Confidence
    disciplinary_status: str
    training_documented: bool
    complication_training_documented: bool


@dataclass(frozen=True)
class EncounterEvidence:
    encounter_id: str
    jurisdiction: str
    procedure: str
    scheduled_on: date
    delegation_document_present: bool
    protocol_signed_and_dated: bool
    delegating_physician_active: bool
    patient_specific_order_present: bool
    order_contains_drug_dose_strength_route: bool
    practitioner_patient_relationship_established: bool
    adequate_medical_record_present: bool
    performer_identity_disclosed: bool
    bls_person_present: bool
    supervisor_onsite: bool
    supervisor_immediately_available: bool
    physician_emergency_appointment_available: bool
    product_lot_verified: bool
    product_lot_alerted: bool
    product_lot_confidence: Confidence
    comprehension_recorded: bool
    comprehension_score: int | None
    comprehension_threshold: int
    comprehension_confidence: Confidence


@dataclass(frozen=True)
class Finding:
    check_id: str
    status: FindingStatus
    summary: str
    citation_urls: tuple[str, ...]
    facts: Mapping[str, Any]


@dataclass(frozen=True)
class GateDecision:
    encounter_id: str
    verdict: Verdict
    determination_scope: str
    findings: tuple[Finding, ...]
    rule_snapshot_json: str
    rule_snapshot_sha256: str

