"""Typed, cache-first sponsor integration adapters.

Every adapter uses committed synthetic fixture data to seed `.cache/<vendor>/`.
Offline mode never attempts a network call. Live activation is deliberately
refused until the corresponding endpoint and credentials are configured; no API
shape is invented merely to make a badge appear connected.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar


ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = ROOT / ".cache"
T = TypeVar("T")


class IntegrationError(RuntimeError):
    pass


class CacheMiss(IntegrationError):
    pass


@dataclass(frozen=True)
class ExtractionResult:
    vendor: str
    document_type: str
    fields: dict[str, Any]
    confidence: dict[str, str]
    page_coordinates: dict[str, list[float]]
    redacted_before_egress: bool
    review_required: bool
    assigned_role: str | None
    source_ref: str
    extractions: list[dict[str, Any]]


@dataclass(frozen=True)
class AlertCandidateResult:
    vendor: str
    candidate_id: str
    query: str
    matched_entity: str
    source_url: str
    published_at: str
    status: str
    boundary: str
    queries: list[str]


@dataclass(frozen=True)
class ConsentResult:
    vendor: str
    document_id: str
    template_version: str
    branches: list[str]
    disclosures: list[str]
    signers: list[str]
    status: str


@dataclass(frozen=True)
class BaselineResult:
    vendor: str
    capture_id: str
    mode: str
    concerns: dict[str, int]
    overlay_ref: str
    vto_used: bool
    boundary: str


@dataclass(frozen=True)
class EvidenceRecordResult:
    vendor: str
    document_id: str
    document_ref: str
    prompt: str
    assembled_sections: list[str]
    status: str
    next_human_role: str


@dataclass(frozen=True)
class DnsReceiptResult:
    vendor: str
    domain: str
    txt_name: str
    txt_value: str
    verified_through: str
    mutable: bool
    operations: list[str]



SENSITIVE_FIELD_NAMES = {"patient_id", "patient_name", "date_of_birth", "address", "phone", "email", "license_number"}


def redact_for_egress(value: Any) -> Any:
    """Remove synthetic identifiers using the same boundary required for PHI."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_FIELD_NAMES else redact_for_egress(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_for_egress(item) for item in value]
    return value

class CachedAdapter(Generic[T]):
    vendor: str
    fixture: dict[str, Any]
    result_type: type[T]

    def __init__(self, offline: bool = True) -> None:
        self.offline = offline

    @property
    def cache_path(self) -> Path:
        return CACHE_ROOT / self.vendor / "hero.json"

    def seed_cache(self) -> Path:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.fixture, indent=2), encoding="utf-8")
        return self.cache_path

    def replay(self) -> T:
        if not self.cache_path.exists():
            raise CacheMiss(f"Missing {self.vendor} cache. Run `python -m before.seed`.")
        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        return self.result_type(**payload)

    def run(self) -> T:
        if self.offline:
            return self.replay()
        raise IntegrationError(
            f"{self.vendor} live activation is not configured. Cached replay remains available."
        )


class NutrientClient(CachedAdapter[ExtractionResult]):
    vendor = "nutrient"
    result_type = ExtractionResult
    fixture = {
        "vendor": "Nutrient DWS",
        "document_type": "product_packaging",
        "fields": {"manufacturer": "Fictional Therapeutics", "product": "EXAMPLETOX — NOT A REAL PRODUCT", "lot": "INVENTED-LOT-0007", "expires_on": "2027-10-31"},
        "confidence": {"manufacturer": "HIGH", "product": "HIGH", "lot": "LOW", "expires_on": "MEDIUM"},
        "page_coordinates": {"lot": [0.52, 0.31, 0.76, 0.39]},
        "redacted_before_egress": True,
        "review_required": True,
        "assigned_role": "Medical Director",
        "source_ref": "fixtures/documents/05-product-packaging-low-confidence.json",
        "extractions": [
            {"document_type": "credential", "source_ref": "fixtures/providers.json", "confidence": "HIGH", "review_required": False},
            {"document_type": "patient_intake", "source_ref": "fixtures/documents/01-intake.json", "confidence": "HIGH", "review_required": False},
            {"document_type": "product_packaging", "source_ref": "fixtures/documents/05-product-packaging-low-confidence.json", "confidence": "LOW", "review_required": True}
        ],
    }


class SerpApiClient(CachedAdapter[AlertCandidateResult]):
    vendor = "serpapi"
    result_type = AlertCandidateResult
    fixture = {
        "vendor": "SerpApi",
        "candidate_id": "SYN-ALERT-001",
        "query": "site:fda.gov neurotoxin warning letter Texas",
        "matched_entity": "EXAMPLETOX — SYNTHETIC MATCH",
        "source_url": "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/pure-indulgence-aesthetics-723267-04012026",
        "published_at": "2026-04-01",
        "status": "CANDIDATE",
        "boundary": "Search result only. A named human must confirm or dismiss it.",
        "queries": ["site:fda.gov neurotoxin warning letter Texas", "site:tmb.state.tx.us cosmetic procedure disciplinary action"],
    }


class DoctavianClient(CachedAdapter[ConsentResult]):
    vendor = "doctavian"
    result_type = ConsentResult
    fixture = {
        "vendor": "Doctavian",
        "document_id": "SYN-DOC-CONSENT-001",
        "template_version": "TX-NEUROTOXIN-CONSENT-1",
        "branches": ["NEUROTOXIN_INJECTION", "DELEGATED_RN", "NO_PATIENT_FLAGS"],
        "disclosures": ["expected temporary effect", "alternatives", "material risks", "who will perform the procedure"],
        "signers": ["Synthetic Patient", "Synthetic Injector"],
        "status": "SIGNED",
    }


class PerfectCorpClient(CachedAdapter[BaselineResult]):
    vendor = "perfectcorp"
    result_type = BaselineResult
    fixture = {
        "vendor": "Perfect Corp YouCam",
        "capture_id": "SYN-BASELINE-001",
        "mode": "SD",
        "concerns": {"acne": 12, "dark_circle": 22, "eye_bag": 14, "firmness": 76, "moisture": 61, "oiliness": 28, "pores": 19, "radiance": 72, "redness": 16, "spots": 18, "texture": 31, "uneven_tone": 23, "wrinkles": 24, "sensitivity": 11},
        "overlay_ref": "fixtures/synthetic-patient-face.svg",
        "vto_used": True,
        "boundary": "Baseline and communication aid only. Not diagnosis.",
    }


class FoxitClient(CachedAdapter[EvidenceRecordResult]):
    vendor = "foxit"
    result_type = EvidenceRecordResult
    fixture = {
        "vendor": "Foxit PDF Services + eSign",
        "document_id": "SYN-EVIDENCE-RECORD-001",
        "document_ref": "output/pdf/synthetic-safety-evidence-record.pdf",
        "prompt": "assemble the safety record for encounter SYN-ENC-BLOCKED-002",
        "assembled_sections": ["gate decision", "rule snapshot", "evidence index", "consent signatures", "baseline"],
        "status": "AWAITING_HUMAN_SIGNATURE",
        "next_human_role": "Medical Director",
    }


class NameComClient(CachedAdapter[DnsReceiptResult]):
    vendor = "namecom"
    result_type = DnsReceiptResult
    fixture = {
        "vendor": "name.com CORE sandbox",
        "domain": "before-synthetic.test",
        "txt_name": "_before.SYN-RECEIPT-001",
        "txt_value": "PENDING_RECEIPT_HASH",
        "verified_through": "name.com sandbox API",
        "mutable": True,
        "operations": ["domain search", "availability check", "sandbox registration", "TXT create", "TXT read-back"],
    }


ALL_ADAPTERS = (NutrientClient, SerpApiClient, DoctavianClient, PerfectCorpClient, FoxitClient, NameComClient)


def seed_all_caches() -> list[str]:
    return [str(adapter().seed_cache().relative_to(ROOT)) for adapter in ALL_ADAPTERS]


def cache_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    for adapter in ALL_ADAPTERS:
        path = adapter().cache_path
        if path.exists():
            manifest[adapter.vendor] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest
