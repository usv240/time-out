"""End-to-end synthetic BEFORE workflow.

This module is the executable reference for the business logic intended to live
in Xano. It never determines legality and never infers ambiguous evidence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from before.gate_demo import _encounter, _load, _provider
from shared.gate import evaluate_gate

from .cache import OperationCache
from .integrations import (
    DoctavianClient,
    FoxitClient,
    NameComClient,
    NutrientClient,
    PerfectCorpClient,
    SerpApiClient,
    cache_manifest,
)
from .models import AuditEvent, EncounterRecord, EncounterState, ReviewTask, now_iso
from .repository import EncounterRepository


DETERMINATION_SCOPE = "Pre-procedure safety determination for human review"
ALLOWED_TRANSITIONS = {
    "DRAFT": {"EVIDENCE_PENDING"},
    "EVIDENCE_PENDING": {"GATE_EVALUATED"},
    "GATE_EVALUATED": {"REMEDIATION", "HUMAN_REVIEW", "CONSENT_COMPILED"},
    "REMEDIATION": {"EVIDENCE_PENDING"},
    "HUMAN_REVIEW": {"EVIDENCE_PENDING", "CONSENT_COMPILED", "READY_FOR_PROCEDURE"},
    "CONSENT_COMPILED": {"HUMAN_REVIEW", "BASELINE_CAPTURED"},
    "BASELINE_CAPTURED": {"AWAITING_ATTESTATION"},
    "AWAITING_ATTESTATION": {"READY_FOR_PROCEDURE"},
    "READY_FOR_PROCEDURE": {"HUMAN_REVIEW", "SEALED"},
    "SEALED": set(),
}

RECEIPT_BOUNDARY = (
    "This receipt records which checks, evidence, sources, and rule snapshot were captured before the "
    "procedure. It does not certify legality, safety, product authenticity, provider quality, or outcome."
)


class WorkflowError(RuntimeError):
    pass


class BeforeService:
    def __init__(
        self,
        *,
        offline: bool = True,
        repository: EncounterRepository | None = None,
        operation_cache: OperationCache | None = None,
    ) -> None:
        self.offline = offline
        self.repository = repository or EncounterRepository()
        self.operation_cache = operation_cache
        self.providers = {row["provider_id"]: _provider(row) for row in _load("providers.json")}
        self.encounter_fixtures = {row["fixture_id"]: row for row in _load("encounters.json")}
        self.rule = _load("rules/tx-neurotoxin.json")
        self.keys: dict[str, str] = {}
        self.webhook_subscriptions: list[dict[str, str]] = []
        self.webhook_outbox: list[dict[str, Any]] = []
        self.rule_proposals: list[dict[str, Any]] = []

    @staticmethod
    def _canonical_hash(payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _transition(self, record: EncounterRecord, target: EncounterState, action: str, actor_role: str, reason: str, payload: Any | None = None) -> EncounterRecord:
        if record.state == target.value:
            return record
        if target.value not in ALLOWED_TRANSITIONS.get(record.state, set()):
            raise WorkflowError(f"Invalid transition {record.state} -> {target.value}.")
        event = AuditEvent(
            id=f"SYN-AUDIT-{len(record.audit_events) + 1:03d}-{record.id}",
            encounter_id=record.id,
            action=action,
            from_state=record.state,
            to_state=target.value,
            actor_role=actor_role,
            reason=reason,
            payload_hash=self._canonical_hash(payload or {}),
        )
        record.state = target.value
        record.version += 1
        record.audit_events.append(asdict(event))
        event_types = {
            "gate_blocked": "encounter.blocked",
            "gate_review_required": "encounter.held",
            "medical_director_attested": "encounter.ready",
            "alert_candidate_raised": "alert.candidate.raised",
        }
        if action in event_types:
            webhook_payload = {"event": event_types[action], "encounter_id": record.id, "state": target.value, "audit_event_id": event.id}
            raw = json.dumps(webhook_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            for subscription in self.webhook_subscriptions:
                signature = hmac.new(subscription["secret"].encode("utf-8"), raw, hashlib.sha256).hexdigest()
                self.webhook_outbox.append({"url": subscription["url"], "payload": webhook_payload, "signature": f"sha256={signature}", "delivery_status": "CACHED_OFFLINE" if self.offline else "PENDING"})
        return record

    def seed(self) -> list[dict[str, Any]]:
        self.repository.reset()
        names = {
            "rn-clear": "Jordan Example",
            "aesthetician-blocked": "Ava Chen",
            "rn-review-low-confidence": "Taylor Example",
        }
        records: list[dict[str, Any]] = []
        for fixture_id, row in self.encounter_fixtures.items():
            record = EncounterRecord(
                id=row["encounter_id"],
                fixture_id=fixture_id,
                patient_display_name=names[fixture_id],
                provider_id=row["provider_id"],
                procedure=row["procedure"],
                jurisdiction=row["jurisdiction"],
                scheduled_on=row["scheduled_on"],
            )
            self._transition(record, EncounterState.EVIDENCE_PENDING, "encounter_opened", "Clinic Operator", "Synthetic encounter seeded", row)
            self.repository.save(record)
            records.append(record.to_dict())
        return records

    def create_encounter(self, fixture_id: str = "rn-clear") -> dict[str, Any]:
        if fixture_id not in self.encounter_fixtures:
            raise WorkflowError("Only committed synthetic fixture IDs are accepted.")
        source = self.encounter_fixtures[fixture_id]
        suffix = len(self.repository.list()) + 1
        record = EncounterRecord(
            id=f"SYN-ENC-API-{suffix:03d}", fixture_id=fixture_id, patient_display_name="Synthetic API Patient",
            provider_id=source["provider_id"], procedure=source["procedure"], jurisdiction=source["jurisdiction"], scheduled_on=source["scheduled_on"],
        )
        self._transition(record, EncounterState.EVIDENCE_PENDING, "encounter_opened", "API Sandbox", "Synthetic encounter created", source)
        self.repository.save(record)
        return record.to_dict()

    def register_webhook(self, url: str) -> dict[str, Any]:
        if not url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
            raise WorkflowError("Webhook URL must use HTTPS or a localhost demonstration target.")
        subscription = {"id": f"SYN-WEBHOOK-{len(self.webhook_subscriptions) + 1:03d}", "url": url, "secret": "whsec_" + secrets.token_urlsafe(18)}
        self.webhook_subscriptions.append(subscription)
        return subscription

    def webhook_deliveries(self) -> list[dict[str, Any]]:
        return list(self.webhook_outbox)

    def propose_rule(self, proposal: dict[str, Any], actor_role: str = "Rule Author") -> dict[str, Any]:
        if not proposal.get("citation_urls"):
            raise WorkflowError("A rule proposal requires at least one primary-source citation URL.")
        item = {"id": f"SYN-RULE-PROPOSAL-{len(self.rule_proposals) + 1:03d}", "status": "PROPOSED", "proposal": proposal, "proposed_by": actor_role, "proposed_at": now_iso()}
        self.rule_proposals.append(item)
        return item

    def review_rule(self, proposal_id: str, decision: str, actor_role: str = "Medical Director") -> dict[str, Any]:
        item = next((row for row in self.rule_proposals if row["id"] == proposal_id), None)
        if not item or item["status"] != "PROPOSED":
            raise WorkflowError("A proposed rule change was not found.")
        normalized = decision.upper()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise WorkflowError("Rule review decision must be APPROVED or REJECTED.")
        item.update({"status": normalized, "reviewed_by": actor_role, "reviewed_at": now_iso()})
        return item

    def activate_rule(self, proposal_id: str, actor_role: str = "Rule Administrator") -> dict[str, Any]:
        item = next((row for row in self.rule_proposals if row["id"] == proposal_id), None)
        if not item or item["status"] != "APPROVED":
            raise WorkflowError("Only a human-approved rule proposal can become effective.")
        item.update({"status": "EFFECTIVE", "activated_by": actor_role, "effective_at": now_iso(), "snapshot_sha256": self._canonical_hash(item["proposal"])})
        return item

    def list_encounters(self) -> list[dict[str, Any]]:
        return [row.to_dict() for row in self.repository.list()]

    def get_encounter(self, encounter_id: str) -> dict[str, Any]:
        return self.repository.get(encounter_id).to_dict()

    def _gate_inputs(self, record: EncounterRecord):
        row = dict(self.encounter_fixtures[record.fixture_id])
        provider = self.providers[record.provider_id]
        provider_fields = {key.removeprefix("provider."): value for key, value in record.evidence_overrides.items() if key.startswith("provider.")}
        encounter_fields = {key: value for key, value in record.evidence_overrides.items() if not key.startswith("provider.")}
        if provider_fields:
            provider = replace(provider, **provider_fields)
        row.update(encounter_fields)
        return provider, _encounter(row)

    def evaluate(self, encounter_id: str, *, actor_role: str = "Clinic Operator") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if record.state in {EncounterState.REMEDIATION.value, EncounterState.HUMAN_REVIEW.value}:
            self._transition(record, EncounterState.EVIDENCE_PENDING, "gate_rerun_requested", actor_role, "Evidence remediated without direct database editing")
        provider, encounter = self._gate_inputs(record)
        decision = evaluate_gate(provider, encounter, self.rule)
        serialized = {
            "encounter_id": decision.encounter_id,
            "verdict": decision.verdict.value,
            "determination_scope": decision.determination_scope,
            "findings": [{**asdict(finding), "status": finding.status.value, "citation_urls": list(finding.citation_urls)} for finding in decision.findings],
            "rule_snapshot_json": decision.rule_snapshot_json,
            "rule_snapshot_sha256": decision.rule_snapshot_sha256,
            "evaluated_at": "2026-08-24T19:55:00+00:00" if self.offline else now_iso(),
        }
        record.gate_decision = serialized
        self._transition(record, EncounterState.GATE_EVALUATED, "gate_evaluated", "Deterministic Gate", decision.determination_scope, serialized)
        if decision.verdict.value == "BLOCKED":
            self._transition(record, EncounterState.REMEDIATION, "gate_blocked", "Deterministic Gate", "One or more deterministic checks blocked the safety record", serialized)
        elif decision.verdict.value == "REVIEW":
            self._transition(record, EncounterState.HUMAN_REVIEW, "gate_review_required", "Deterministic Gate", "Ambiguous or low-confidence evidence requires human review", serialized)
        self.repository.save(record)
        return serialized

    def remediate(self, encounter_id: str, changes: dict[str, Any], *, actor_role: str = "Medical Director") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if record.state not in {EncounterState.REMEDIATION.value, EncounterState.HUMAN_REVIEW.value}:
            raise WorkflowError("Remediation requires a held or human-review encounter.")
        if "provider_id" in changes:
            provider_id = str(changes.pop("provider_id"))
            if provider_id not in self.providers:
                raise WorkflowError("Unknown synthetic provider.")
            record.provider_id = provider_id
        record.evidence_overrides.update(changes)
        self._transition(record, EncounterState.EVIDENCE_PENDING, "evidence_remediated", actor_role, "Documented remediation attached; source fixture remains unchanged", changes)
        self.repository.save(record)
        return record.to_dict()

    def extract_with_nutrient(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        result = asdict(NutrientClient(self.offline, self.operation_cache).run())
        if result["review_required"]:
            task = ReviewTask(
                id=f"SYN-REVIEW-NUTRIENT-{record.id}", encounter_id=record.id, kind="LOW_CONFIDENCE_EXTRACTION",
                assigned_role=result["assigned_role"], status="OPEN", reason="Required product lot field is low-confidence",
                source_ref=result["source_ref"],
            )
            record.review_tasks.append(asdict(task))
            self._transition(record, EncounterState.HUMAN_REVIEW, "low_confidence_routed", "Nutrient DWS", "Low-confidence required field routed to Medical Director", result)
        self.repository.save(record)
        return result

    def resolve_review(self, encounter_id: str, task_id: str, *, resolution: str, actor_role: str = "Medical Director") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        task = next((item for item in record.review_tasks if item["id"] == task_id), None)
        if not task:
            raise WorkflowError("Review task not found.")
        task["status"] = "RESOLVED"
        task["resolution"] = resolution
        task["resolved_by"] = actor_role
        task["resolved_at"] = now_iso()
        self._transition(record, EncounterState.EVIDENCE_PENDING, "human_review_resolved", actor_role, "Named human resolved the evidence uncertainty", task)
        self.repository.save(record)
        return task

    def compile_consent(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if not record.gate_decision or record.gate_decision["verdict"] != "CLEAR" or record.state != EncounterState.GATE_EVALUATED.value:
            raise WorkflowError("A CLEAR Gate decision with no unresolved review is required before consent compilation.")
        result = asdict(DoctavianClient(self.offline, self.operation_cache).run())
        result["rule_snapshot_sha256"] = record.gate_decision["rule_snapshot_sha256"]
        record.consent = result
        self._transition(record, EncounterState.CONSENT_COMPILED, "consent_compiled_and_signed", "Patient + Injector", "Doctavian treatment-party signatures captured", result)
        self.repository.save(record)
        return result

    def record_comprehension(self, encounter_id: str, answers: list[dict[str, Any]], *, confidence: str = "HIGH") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if not record.gate_decision or not record.consent:
            raise WorkflowError("Consent and a frozen Gate snapshot are required before teach-back.")
        score = sum(bool(item.get("correct")) for item in answers)
        threshold = len(answers)
        passed = score >= threshold and confidence != "LOW"
        attempt = 1 + (record.comprehension or {}).get("attempt", 0)
        result = {
            "question_set_version": "TX-NEUROTOXIN-TEACHBACK-1",
            "rule_snapshot_sha256": record.gate_decision["rule_snapshot_sha256"],
            "attempt": attempt, "answers": answers, "score": score, "threshold": threshold,
            "confidence": confidence, "passed": passed, "recorded_at": now_iso(),
        }
        record.comprehension = result
        if not passed:
            task = ReviewTask(
                id=f"SYN-REVIEW-COMPREHENSION-{attempt}-{record.id}", encounter_id=record.id, kind="COMPREHENSION_REMEDIATION",
                assigned_role="Injector", status="OPEN", reason="Teach-back did not meet the versioned threshold or was low-confidence",
                source_ref=result["rule_snapshot_sha256"],
            )
            record.review_tasks.append(asdict(task))
            self._transition(record, EncounterState.HUMAN_REVIEW, "comprehension_held", "Teach-back Gate", "Failed or uncertain teach-back requires explanation and re-ask", result)
        else:
            if record.state == EncounterState.HUMAN_REVIEW.value:
                for task in record.review_tasks:
                    if task["kind"] == "COMPREHENSION_REMEDIATION" and task["status"] == "OPEN":
                        task.update({"status": "RESOLVED", "resolved_by": "Injector", "resolved_at": now_iso()})
                self._transition(record, EncounterState.CONSENT_COMPILED, "comprehension_remediated", "Injector", "Risks re-explained and teach-back passed", result)
            else:
                self._transition(record, EncounterState.CONSENT_COMPILED, "comprehension_passed", "Teach-back Gate", "Versioned teach-back threshold met", result)
        self.repository.save(record)
        return result

    def capture_baseline(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if not record.comprehension or not record.comprehension["passed"] or record.state != EncounterState.CONSENT_COMPILED.value:
            raise WorkflowError("Passing comprehension is required before baseline progression.")
        result = asdict(PerfectCorpClient(self.offline, self.operation_cache).run())
        record.baseline = result
        self._transition(record, EncounterState.BASELINE_CAPTURED, "baseline_captured", "Clinic Operator", "Standardized SD baseline captured; not diagnosis", result)
        self.repository.save(record)
        return result

    def assemble_evidence_record(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if record.state != EncounterState.BASELINE_CAPTURED.value:
            raise WorkflowError("Baseline capture is required before evidence-record assembly.")
        result = asdict(FoxitClient(self.offline, self.operation_cache).run())
        result["encounter_id"] = record.id
        record.evidence_record = result
        self._transition(record, EncounterState.AWAITING_ATTESTATION, "evidence_record_assembled", "Foxit Assembly Agent", "Reversible assembly complete; agent stopped before human signature", result)
        self.repository.save(record)
        return result

    def attest(self, encounter_id: str, *, actor_role: str = "Medical Director") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if record.state != EncounterState.AWAITING_ATTESTATION.value:
            raise WorkflowError("Evidence record must be awaiting attestation.")
        result = {"attestation_id": f"SYN-ATTEST-{record.id}", "signed_by_role": actor_role, "status": "SIGNED", "signed_at": now_iso()}
        record.attestation = result
        self._transition(record, EncounterState.READY_FOR_PROCEDURE, "medical_director_attested", actor_role, "Human eSign completed at the irreversible boundary", result)
        self.repository.save(record)
        return result

    def scan_alerts(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        result = asdict(SerpApiClient(self.offline, self.operation_cache).run())
        record.alert_candidates.append(result)
        if record.state == EncounterState.READY_FOR_PROCEDURE.value:
            task = ReviewTask(
                id=f"SYN-REVIEW-ALERT-{record.id}", encounter_id=record.id, kind="ALERT_CANDIDATE",
                assigned_role="Medical Director", status="OPEN", reason="A live-data candidate may be material to the prepared encounter",
                source_ref=result["source_url"],
            )
            record.review_tasks.append(asdict(task))
            self._transition(record, EncounterState.HUMAN_REVIEW, "alert_candidate_raised", "SerpApi", "Candidate only; no automated conclusion", result)
        self.repository.save(record)
        return result

    def decide_alert(self, encounter_id: str, *, decision: str, actor_role: str = "Medical Director") -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        task = next((item for item in reversed(record.review_tasks) if item["kind"] == "ALERT_CANDIDATE" and item["status"] == "OPEN"), None)
        if not task:
            raise WorkflowError("No open alert candidate review.")
        normalized = decision.upper()
        if normalized not in {"CONFIRMED", "DISMISSED"}:
            raise WorkflowError("Alert decision must be CONFIRMED or DISMISSED.")
        task.update({"status": "RESOLVED", "resolution": normalized, "resolved_by": actor_role, "resolved_at": now_iso()})
        if normalized == "DISMISSED":
            self._transition(record, EncounterState.READY_FOR_PROCEDURE, "alert_candidate_dismissed", actor_role, "Named human dismissed the search candidate", task)
        self.repository.save(record)
        return task

    def seal_receipt(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        if record.state != EncounterState.READY_FOR_PROCEDURE.value:
            raise WorkflowError("Only a procedure-ready encounter can produce a safety receipt.")
        if not record.gate_decision or record.gate_decision["verdict"] != "CLEAR":
            raise WorkflowError("Receipt invariant failed: CLEAR Gate decision missing.")
        if any(task["status"] == "OPEN" for task in record.review_tasks):
            raise WorkflowError("Receipt invariant failed: unresolved human review remains.")
        payload = {
            "receipt_id": f"SYN-RECEIPT-{record.id}", "encounter_id": record.id,
            "determination_scope": DETERMINATION_SCOPE, "boundary": RECEIPT_BOUNDARY,
            "gate_decision_sha256": self._canonical_hash(record.gate_decision),
            "rule_snapshot_sha256": record.gate_decision["rule_snapshot_sha256"],
            "consent_document_id": record.consent["document_id"], "baseline_capture_id": record.baseline["capture_id"],
            "evidence_record_ref": record.evidence_record["document_ref"],
            "attestation_id": record.attestation["attestation_id"], "cache_manifest": cache_manifest(),
            "sealed_at": "2026-08-24T20:00:00+00:00" if self.offline else now_iso(),
        }
        receipt_hash = self._canonical_hash(payload)
        dns_host = f"_before.{payload['receipt_id'].lower()}"
        dns = asdict(
            NameComClient(
                self.offline,
                self.operation_cache,
                host=dns_host,
                digest=receipt_hash,
            ).run()
        )
        receipt = {**payload, "receipt_hash": receipt_hash, "dns_verification": dns, "verification_path": f"/receipt/{payload['receipt_id']}"}
        record.receipt = receipt
        self._transition(record, EncounterState.SEALED, "receipt_sealed", "BEFORE Receipt Service", RECEIPT_BOUNDARY, receipt)
        self.repository.save(record)
        return receipt

    def get_receipt(self, receipt_id: str) -> dict[str, Any]:
        for record in self.repository.list():
            if record.receipt and record.receipt["receipt_id"] == receipt_id:
                return record.receipt
        raise KeyError(receipt_id)

    def verify_receipt(self, receipt_hash: str) -> dict[str, Any]:
        for record in self.repository.list():
            if record.receipt and record.receipt["receipt_hash"] == receipt_hash:
                payload = {key: value for key, value in record.receipt.items() if key not in {"receipt_hash", "dns_verification", "verification_path"}}
                recomputed = self._canonical_hash(payload)
                return {"verified": recomputed == receipt_hash, "stored_hash": receipt_hash, "recomputed_hash": recomputed, "receipt_id": record.receipt["receipt_id"], "boundary": RECEIPT_BOUNDARY}
        return {"verified": False, "stored_hash": None, "recomputed_hash": None, "receipt_id": None, "boundary": RECEIPT_BOUNDARY}

    def reproduce_decision(self, encounter_id: str) -> dict[str, Any]:
        record = self.repository.get(encounter_id)
        original = record.gate_decision
        if not original:
            raise WorkflowError("No stored Gate decision.")
        provider, encounter = self._gate_inputs(record)
        rule = json.loads(original["rule_snapshot_json"])
        rerun = evaluate_gate(provider, encounter, rule)
        recomputed = {
            "encounter_id": rerun.encounter_id, "verdict": rerun.verdict.value,
            "determination_scope": rerun.determination_scope,
            "findings": [{**asdict(finding), "status": finding.status.value, "citation_urls": list(finding.citation_urls)} for finding in rerun.findings],
            "rule_snapshot_json": rerun.rule_snapshot_json, "rule_snapshot_sha256": rerun.rule_snapshot_sha256,
        }
        comparable_original = {key: value for key, value in original.items() if key != "evaluated_at"}
        return {"identical": comparable_original == recomputed, "original": comparable_original, "recomputed": recomputed}

    def issue_sandbox_key(self) -> dict[str, Any]:
        token = "bfr_sbx_" + secrets.token_urlsafe(15)
        expires = datetime.now(UTC) + timedelta(days=7)
        self.keys[token] = expires.isoformat()
        return {"key": token, "scope": "synthetic-data-only", "rate_limit": "60 requests/minute", "expires_at": expires.isoformat()}

    def run_hero_path(self) -> dict[str, Any]:
        self.seed()
        encounter_id = "SYN-ENC-BLOCKED-002"
        timeline: list[dict[str, Any]] = []
        timeline.append({"step": "blocked", "result": self.evaluate(encounter_id)})
        complete = {
            "provider_id": "SYN-PROV-RN-002", "delegation_document_present": True,
            "protocol_signed_and_dated": True, "delegating_physician_active": True,
            "patient_specific_order_present": True, "order_contains_drug_dose_strength_route": True,
            "practitioner_patient_relationship_established": True, "adequate_medical_record_present": True,
            "performer_identity_disclosed": True, "bls_person_present": True,
            "supervisor_immediately_available": True, "physician_emergency_appointment_available": True,
        }
        self.remediate(encounter_id, complete)
        timeline.append({"step": "gate_clear", "result": self.evaluate(encounter_id)})
        extraction = self.extract_with_nutrient(encounter_id)
        timeline.append({"step": "nutrient_review", "result": extraction})
        self.resolve_review(encounter_id, f"SYN-REVIEW-NUTRIENT-{encounter_id}", resolution="Lot confirmed from synthetic source document")
        timeline.append({"step": "gate_clear_after_review", "result": self.evaluate(encounter_id)})
        timeline.append({"step": "consent", "result": self.compile_consent(encounter_id)})
        wrong = [{"question_id": "risk", "answer": "I do not know", "correct": False}, {"question_id": "alternative", "answer": "Delay treatment", "correct": True}]
        timeline.append({"step": "teach_back_held", "result": self.record_comprehension(encounter_id, wrong)})
        correct = [{"question_id": "risk", "answer": "The effect can spread and needs urgent care if breathing is affected", "correct": True}, {"question_id": "alternative", "answer": "I can delay or decline treatment", "correct": True}]
        timeline.append({"step": "teach_back_passed", "result": self.record_comprehension(encounter_id, correct)})
        timeline.append({"step": "baseline", "result": self.capture_baseline(encounter_id)})
        timeline.append({"step": "foxit_pause", "result": self.assemble_evidence_record(encounter_id)})
        timeline.append({"step": "human_attestation", "result": self.attest(encounter_id)})
        timeline.append({"step": "alert_reversion", "result": self.scan_alerts(encounter_id)})
        timeline.append({"step": "alert_dismissed", "result": self.decide_alert(encounter_id, decision="DISMISSED")})
        timeline.append({"step": "receipt", "result": self.seal_receipt(encounter_id)})
        return {"encounter": self.get_encounter(encounter_id), "timeline": timeline, "offline": self.offline}
