"""Typed workflow records for the synthetic BEFORE reference backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class EncounterState(str, Enum):
    DRAFT = "DRAFT"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    GATE_EVALUATED = "GATE_EVALUATED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REMEDIATION = "REMEDIATION"
    CONSENT_COMPILED = "CONSENT_COMPILED"
    BASELINE_CAPTURED = "BASELINE_CAPTURED"
    AWAITING_ATTESTATION = "AWAITING_ATTESTATION"
    READY_FOR_PROCEDURE = "READY_FOR_PROCEDURE"
    SEALED = "SEALED"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class AuditEvent:
    id: str
    encounter_id: str
    action: str
    from_state: str
    to_state: str
    actor_role: str
    reason: str
    payload_hash: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class ReviewTask:
    id: str
    encounter_id: str
    kind: str
    assigned_role: str
    status: str
    reason: str
    source_ref: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class EncounterRecord:
    id: str
    fixture_id: str
    patient_display_name: str
    provider_id: str
    procedure: str
    jurisdiction: str
    scheduled_on: str
    state: str = EncounterState.DRAFT.value
    version: int = 0
    evidence_overrides: dict[str, Any] = field(default_factory=dict)
    gate_decision: dict[str, Any] | None = None
    review_tasks: list[dict[str, Any]] = field(default_factory=list)
    alert_candidates: list[dict[str, Any]] = field(default_factory=list)
    consent: dict[str, Any] | None = None
    comprehension: dict[str, Any] | None = None
    baseline: dict[str, Any] | None = None
    evidence_record: dict[str, Any] | None = None
    attestation: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    audit_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
