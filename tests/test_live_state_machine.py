from __future__ import annotations

import hashlib
import json
from pathlib import Path

from before.app import sponsor_clients
from before.app.cache import OperationCache
from before.app.integrations import NutrientClient
from before.app.service import BeforeService

def _write_synthetic_pdf(path: Path) -> None:
    payload = b"%PDF-1.4 synthetic"
    path.write_bytes(payload)
    path.with_name(path.name + ".synthetic.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "synthetic": True,
                "contains_real_people_or_businesses": False,
                "contains_prohibited_identifiers": False,
                "artifact_sha256": hashlib.sha256(payload).hexdigest(),
            }
        ),
        encoding="utf-8",
    )


def test_frozen_nutrient_response_routes_encounter_to_named_human_review(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "synthetic-product.pdf"
    _write_synthetic_pdf(source)
    monkeypatch.setenv("NUTRIENT_SOURCE_PDF", str(source))
    payload = {
        "output": {
            "elements": [
                {"text": "MANUFACTURER: Fictional Therapeutics", "confidence": 0.98},
                {"text": "PRODUCT: EXAMPLETOX - NOT A REAL PRODUCT", "confidence": 0.97},
                {"text": "LOT: INVENTED-LOT-0007", "confidence": 0.62, "bounds": [1, 2, 3, 4]},
                {"text": "EXPIRES: 2027-10-31", "confidence": 0.96},
            ]
        },
        "metrics": {"pagesProcessed": 1},
    }
    monkeypatch.setattr(sponsor_clients, "_nutrient_parse_live", lambda document: payload)
    cache = OperationCache(tmp_path / "cache")
    NutrientClient(False, cache, source).run()
    monkeypatch.setattr(
        sponsor_clients,
        "_nutrient_parse_live",
        lambda document: (_ for _ in ()).throw(AssertionError("offline state machine attempted network")),
    )

    service = BeforeService(offline=True, operation_cache=cache)
    service.seed()
    encounter_id = "SYN-ENC-BLOCKED-002"
    service.evaluate(encounter_id)
    service.remediate(
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
    assert service.evaluate(encounter_id)["verdict"] == "CLEAR"
    extraction = service.extract_with_nutrient(encounter_id)
    encounter = service.get_encounter(encounter_id)

    assert extraction["confidence"]["lot"] == "LOW"
    assert encounter["state"] == "HUMAN_REVIEW"
    assert encounter["review_tasks"][-1]["assigned_role"] == "Medical Director"
    assert encounter["audit_events"][-1]["action"] == "low_confidence_routed"
