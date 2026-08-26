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
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Generic, TypeVar

from . import sponsor_clients
from .cache import OperationCache, OperationCacheError, OperationCacheMiss


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
    template_urn: str = ""
    data_urn: str = ""
    generated_document_urn: str = ""
    envelope_id: str = ""
    signature_status: str = "PENDING"
    boundary: str = "Treatment-party consent only; not a legality or safety certification."


@dataclass(frozen=True)
class BaselineResult:
    vendor: str
    capture_id: str
    mode: str
    concerns: dict[str, int]
    overlay_ref: str
    vto_used: bool
    boundary: str
    overall_score: float | None = None
    skin_age: int | None = None
    mask_refs: list[str] = field(default_factory=list)
    source_ref: str = ""
    image_ref: str = ""


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
    published: bool = False
    matches: bool = False
    fqdn: str | None = None
    caveat: str = ""



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

    def __init__(self, offline: bool = True, operation_cache: OperationCache | None = None) -> None:
        self.offline = offline
        self.operation_cache = operation_cache

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
            if self.operation_cache is None:
                return self.replay()
            try:
                return self._run_operation(offline=True)
            except OperationCacheMiss:
                return self.replay()
        try:
            return self._run_operation(offline=False)
        except IntegrationError:
            raise
        except (sponsor_clients.LiveCallError, OperationCacheError, OSError, KeyError, TypeError, ValueError) as exc:
            raise IntegrationError(f"{self.vendor} live operation failed: {exc}") from exc

    def _run_operation(self, *, offline: bool) -> T:
        if offline:
            return self.replay()
        raise IntegrationError(
            f"{self.vendor} live activation is not configured. Cached replay remains available."
        )


def _confidence_label(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "LOW"
    if value >= 0.90:
        return "HIGH"
    if value >= 0.80:
        return "MEDIUM"
    return "LOW"


def _normalise_bounds(value: Any) -> list[float]:
    if isinstance(value, list) and len(value) >= 4:
        return [float(item) for item in value[:4]]
    if isinstance(value, dict):
        keys = ("left", "top", "width", "height")
        if all(isinstance(value.get(key), (int, float)) for key in keys):
            return [float(value[key]) for key in keys]
    return []


def _verify_synthetic_egress_document(source: Path) -> None:
    manifest_path = source.with_name(source.name + ".synthetic.json")
    if not manifest_path.exists():
        raise IntegrationError("Synthetic egress manifest is missing; sponsor transmission refused.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("synthetic") is not True:
        raise IntegrationError("Egress manifest does not attest synthetic-only data.")
    if manifest.get("contains_real_people_or_businesses") is not False:
        raise IntegrationError("Egress manifest does not exclude real people or businesses.")
    if manifest.get("contains_prohibited_identifiers") is not False:
        raise IntegrationError("Egress manifest does not exclude prohibited identifiers.")
    if manifest.get("artifact_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        raise IntegrationError("Synthetic egress manifest digest does not match the document.")


def _verify_synthetic_face(source: Path) -> None:
    manifest_path = source.parent / "synthetic-patient-02.provenance.json"
    if not manifest_path.exists():
        raise IntegrationError("Synthetic face provenance manifest is missing; sponsor transmission refused.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest.get("analysis_input", {})
    expected_path = str(source.relative_to(ROOT)).replace("\\", "/") if source.is_relative_to(ROOT) else source.name
    if manifest.get("synthetic") is not True or manifest.get("contains_real_people") is not False:
        raise IntegrationError("Face provenance does not attest a fictional synthetic subject.")
    if entry.get("file") != expected_path:
        raise IntegrationError("Face provenance does not match the selected analysis input.")
    if entry.get("sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        raise IntegrationError("Synthetic face digest does not match its provenance manifest.")

def _typed_packaging_fields(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], dict[str, list[float]]]:
    elements = payload.get("output", {}).get("elements", []) or []
    text = "\n".join(str(element.get("text", "")) for element in elements)
    patterns = {
        "manufacturer": r"MANUFACTURER\s*:\s*([^\n]+)",
        "product": r"PRODUCT\s*:\s*([^\n]+)",
        "lot": r"LOT\s*:\s*([^\s\n]+)",
        "expires_on": r"EXPIRES\s*:\s*(\d{4}-\d{2}-\d{2})",
    }
    fields: dict[str, Any] = {}
    confidence: dict[str, str] = {}
    coordinates: dict[str, list[float]] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        fields[field] = match.group(1).strip() if match else None
        label = field.replace("expires_on", "expires").split("_")[0].upper()
        matching_element = next(
            (element for element in elements if label in str(element.get("text", "")).upper()),
            None,
        )
        score = matching_element.get("confidence") if matching_element else None
        confidence[field] = _confidence_label(score)
        if matching_element:
            bounds = _normalise_bounds(matching_element.get("bounds"))
            if bounds:
                coordinates[field] = bounds
    return fields, confidence, coordinates

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

    def __init__(
        self,
        offline: bool = True,
        operation_cache: OperationCache | None = None,
        source_document: Path | None = None,
    ) -> None:
        super().__init__(offline=offline, operation_cache=operation_cache)
        configured = os.getenv("NUTRIENT_SOURCE_PDF", "").strip()
        self.source_document = source_document or (
            Path(configured)
            if configured
            else ROOT / "output" / "pdf" / "synthetic-product-packaging-low-confidence.pdf"
        )

    def _run_operation(self, *, offline: bool) -> ExtractionResult:
        source = self.source_document.resolve()
        if not source.exists():
            if offline:
                raise OperationCacheMiss("Synthetic Nutrient source PDF is not built.")
            raise IntegrationError(f"Synthetic Nutrient source PDF does not exist: {source}")
        if source.suffix.lower() != ".pdf" or "synthetic" not in source.name.lower():
            raise IntegrationError("Nutrient egress is restricted to an explicitly synthetic PDF fixture.")
        _verify_synthetic_egress_document(source)
        raw = sponsor_clients.nutrient_parse(source, offline=offline, cache=self.operation_cache)
        summary = sponsor_clients.summarise_parse(raw)
        fields, confidence, coordinates = _typed_packaging_fields(raw)
        review_required = summary["review_required"] or any(
            value is None or confidence[key] == "LOW" for key, value in fields.items()
        )
        relative_source = (
            str(source.relative_to(ROOT)).replace("\\", "/")
            if source.is_relative_to(ROOT)
            else source.name
        )
        confidence_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        return ExtractionResult(
            vendor="Nutrient DWS",
            document_type="product_packaging",
            fields=fields,
            confidence=confidence,
            page_coordinates=coordinates,
            redacted_before_egress=True,
            review_required=review_required,
            assigned_role="Medical Director" if review_required else None,
            source_ref=relative_source,
            extractions=[
                {
                    "document_type": "product_packaging",
                    "source_ref": relative_source,
                    "confidence": min(confidence.values(), key=confidence_order.get),
                    "review_required": review_required,
                    "elements_total": summary["elements_total"],
                    "pages_processed": summary["pages_processed"],
                }
            ],
        )

class SerpApiClient(CachedAdapter[AlertCandidateResult]):
    vendor = "serpapi"
    result_type = AlertCandidateResult
    fixture = {
        "vendor": "SerpApi",
        "candidate_id": "SYN-ALERT-001",
        "query": "site:fda.gov botulinum toxin safety communication",
        "matched_entity": "EXAMPLETOX - SYNTHETIC ENCOUNTER SCOPE",
        "source_url": "https://www.fda.gov/news-events/press-announcements/fda-warns-companies-over-illegal-marketing-botox-and-related-products",
        "published_at": "2026-04-01",
        "status": "CANDIDATE",
        "boundary": "Search result only. A named human must confirm or dismiss it.",
        "queries": ["site:fda.gov botulinum toxin safety communication", "site:tmb.state.tx.us nonsurgical medical cosmetic procedure rules"],
    }

    queries = [
        "site:fda.gov botulinum toxin safety communication",
        "site:tmb.state.tx.us nonsurgical medical cosmetic procedure rules",
    ]

    def _run_operation(self, *, offline: bool) -> AlertCandidateResult:
        candidates: list[dict[str, Any]] = []
        for query in self.queries:
            raw = sponsor_clients.serpapi_search(
                query,
                5,
                offline=offline,
                cache=self.operation_cache,
            )
            candidates.extend(sponsor_clients.alert_candidates(raw, query))
        candidate = next((item for item in candidates if item.get("source_url")), None)
        if candidate is None:
            raise IntegrationError("SerpApi returned no source-backed alert candidate for human review.")
        source_url = str(candidate["source_url"])
        return AlertCandidateResult(
            vendor="SerpApi",
            candidate_id="SYN-ALERT-" + hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12].upper(),
            query=str(candidate["query"]),
            matched_entity="EXAMPLETOX - SYNTHETIC ENCOUNTER SCOPE",
            source_url=source_url,
            published_at=str(candidate.get("published_at") or "UNCONFIRMED"),
            status="CANDIDATE",
            boundary="Search result only. A named human must confirm or dismiss it.",
            queries=list(self.queries),
        )

class DoctavianClient(CachedAdapter[ConsentResult]):
    vendor = "doctavian"
    result_type = ConsentResult
    template_path = ROOT / "before" / "doctavian" / "tx-neurotoxin-consent-v1.docx"
    fixture_data_path = ROOT / "before" / "doctavian" / "consent-data.synthetic.json"
    fixture = {
        "vendor": "Doctavian",
        "document_id": "SYN-DOC-CONSENT-001",
        "template_version": "TX-NEUROTOXIN-CONSENT-1",
        "branches": ["NEUROTOXIN_INJECTION", "DELEGATED_RN", "NO_PATIENT_FLAGS"],
        "disclosures": ["temporary effect and alternatives", "material risks", "who will perform the procedure", "unresolved holds"],
        "signers": ["Synthetic Patient", "Synthetic Injector"],
        "status": "AWAITING_SIGNATURES",
        "template_urn": "urn:synthetic:doctavian:template:tx-neurotoxin-consent-1",
        "data_urn": "urn:synthetic:doctavian:data:syn-enc-clear-001",
        "generated_document_urn": "urn:synthetic:doctavian:document:syn-doc-consent-001",
        "envelope_id": "SYN-ENVELOPE-CONSENT-001",
        "signature_status": "PENDING",
        "boundary": "Patient and injector consent only. Medical director attestation is a separate Foxit event.",
    }

    def __init__(
        self,
        offline: bool = True,
        operation_cache: OperationCache | None = None,
        consent_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(offline=offline, operation_cache=operation_cache)
        self.consent_data = consent_data or json.loads(self.fixture_data_path.read_text(encoding="utf-8"))

    @staticmethod
    def _identifier(payload: Any, names: tuple[str, ...], label: str) -> str:
        def find(value: Any, target: str) -> str | None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.lower() == target and isinstance(item, (str, int)) and str(item):
                        return str(item)
                for item in value.values():
                    match = find(item, target)
                    if match:
                        return match
            elif isinstance(value, list):
                for item in value:
                    match = find(item, target)
                    if match:
                        return match
            return None

        for name in names:
            match = find(payload, name.lower())
            if match:
                return match
        raise IntegrationError(f"Doctavian response did not include {label}.")

    def _run_operation(self, *, offline: bool) -> ConsentResult:
        if not self.template_path.exists():
            raise IntegrationError("Generated Doctavian DOCX template is missing. Run `python before/build_doctavian_consent.py`.")
        encounter = (self.consent_data.get("Encounter") or [{}])[0]
        encounter_id = str(encounter.get("EncounterId") or "SYN-ENC-CLEAR-001")
        template_response = sponsor_clients.doctavian_upload_template(
            self.template_path, offline=offline, cache=self.operation_cache
        )
        template_urn = self._identifier(template_response, ("urn", "templateUrn", "template_urn", "id"), "a template URN")
        data_response = sponsor_clients.doctavian_upload_data(
            self.consent_data, offline=offline, cache=self.operation_cache
        )
        data_urn = self._identifier(data_response, ("urn", "dataUrn", "data_urn", "id"), "a data URN")
        generated = sponsor_clients.doctavian_generate(
            template_urn, data_urn, encounter_id, offline=offline, cache=self.operation_cache
        )
        document_urn = self._identifier(
            generated, ("urn", "documentUrn", "document_urn", "id"), "a generated document URN"
        )
        patient_email = os.getenv("DOCTAVIAN_PATIENT_EMAIL", "synthetic-patient@example.invalid").strip()
        injector_email = os.getenv("DOCTAVIAN_INJECTOR_EMAIL", "synthetic-injector@example.invalid").strip()
        if not offline and (patient_email.endswith(".invalid") or injector_email.endswith(".invalid")):
            raise IntegrationError("Controlled synthetic Doctavian recipient emails are not configured.")
        recipients = [
            {"reference_signer_id": "patient", "name": "Synthetic Patient", "email": patient_email},
            {"reference_signer_id": "injector", "name": "Synthetic Injector", "email": injector_email},
        ]
        envelope = sponsor_clients.doctavian_create_envelope(
            document_urn, encounter_id, recipients, offline=offline, cache=self.operation_cache
        )
        envelope_id = self._identifier(envelope, ("envelopeId", "envelope_id", "id"), "an envelope ID")
        sponsor_clients.doctavian_send_envelope(
            envelope_id, offline=offline, cache=self.operation_cache
        )
        disclosures = [
            str(item.get("Title"))
            for item in encounter.get("RequiredDisclosures", [])
            if isinstance(item, dict) and item.get("Title")
        ]
        branches = [str(encounter.get("ProcedureDisplayName") or "NEUROTOXIN_INJECTION")]
        if encounter.get("AuthorityPathway") == "DELEGATED":
            branches.append("DELEGATED")
        branches.append("PATIENT_FLAG_REVIEW" if encounter.get("PatientFlagReviewRequired") else "NO_PATIENT_FLAGS")
        return ConsentResult(
            vendor="Doctavian",
            document_id="SYN-DOC-" + hashlib.sha256(document_urn.encode("utf-8")).hexdigest()[:12].upper(),
            template_version="TX-NEUROTOXIN-CONSENT-1",
            branches=branches,
            disclosures=disclosures,
            signers=["Synthetic Patient", "Synthetic Injector"],
            status="AWAITING_SIGNATURES",
            template_urn=template_urn,
            data_urn=data_urn,
            generated_document_urn=document_urn,
            envelope_id=envelope_id,
            signature_status="PENDING",
            boundary="Patient and injector consent only. Medical director attestation is a separate Foxit event.",
        )


class PerfectCorpClient(CachedAdapter[BaselineResult]):
    vendor = "perfectcorp"
    result_type = BaselineResult
    fixture = {
        "vendor": "Perfect Corp YouCam",
        "capture_id": "SYN-BASELINE-001",
        "mode": "SD",
        "concerns": {"acne": 12, "dark_circle": 22, "eye_bag": 14, "firmness": 76, "moisture": 61, "oiliness": 28, "pores": 19, "radiance": 72, "redness": 16, "spots": 18, "texture": 31, "uneven_tone": 23, "wrinkles": 24, "sensitivity": 11},
        "overlay_ref": "/assets/perfectcorp/synthetic-patient-02-wrinkle-overlay.png",
        "vto_used": False,
        "boundary": "Baseline and communication aid only. Not diagnosis.",
        "overall_score": 68.0,
        "skin_age": 41,
        "mask_refs": ["wrinkle", "texture", "pore", "redness", "spots"],
        "source_ref": "fixtures/faces/synthetic-patient-02-analysis-input.jpg",
        "image_ref": "/assets/perfectcorp/synthetic-patient-02-analysis-input.jpg",
    }

    def __init__(
        self,
        offline: bool = True,
        operation_cache: OperationCache | None = None,
        source_image: Path | None = None,
    ) -> None:
        super().__init__(offline=offline, operation_cache=operation_cache)
        configured = os.getenv("PERFECTCORP_SOURCE_IMAGE", "").strip()
        self.source_image = source_image or (
            Path(configured)
            if configured
            else ROOT / "fixtures" / "faces" / "synthetic-patient-02-analysis-input.jpg"
        )

    def _run_operation(self, *, offline: bool) -> BaselineResult:
        source = self.source_image.resolve()
        if not source.exists():
            if offline:
                raise OperationCacheMiss("Synthetic Perfect Corp source image is missing.")
            raise IntegrationError(f"Synthetic Perfect Corp source image does not exist: {source}")
        _verify_synthetic_face(source)
        file_id = sponsor_clients.perfectcorp_upload(source, offline=offline, cache=self.operation_cache)
        task = sponsor_clients.perfectcorp_skin_analysis(
            file_id,
            offline=offline,
            cache=self.operation_cache,
        )
        scores = sponsor_clients.perfectcorp_scores(task, offline=offline, cache=self.operation_cache)
        concerns = {
            name: int(round(float(value)))
            for name, value in scores.get("scores", {}).items()
            if isinstance(value, (int, float))
        }
        relative_source = str(source.relative_to(ROOT)).replace("\\", "/") if source.is_relative_to(ROOT) else source.name
        return BaselineResult(
            vendor="Perfect Corp YouCam",
            capture_id="SYN-BASELINE-" + hashlib.sha256(source.read_bytes()).hexdigest()[:12].upper(),
            mode="SD",
            concerns=concerns,
            overlay_ref="/assets/perfectcorp/synthetic-patient-02-wrinkle-overlay.png",
            vto_used=False,
            boundary=str(scores.get("scope") or "Baseline and communication aid. Not a diagnosis."),
            overall_score=float(scores["overall"]) if isinstance(scores.get("overall"), (int, float)) else None,
            skin_age=int(scores["skin_age"]) if isinstance(scores.get("skin_age"), (int, float)) else None,
            mask_refs=list(scores.get("masks", [])),
            source_ref=relative_source,
            image_ref="/assets/perfectcorp/synthetic-patient-02-analysis-input.jpg",
        )


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
        "domain": "timeout-receipts-demo.com",
        "txt_name": "_before.syn-receipt-001",
        "txt_value": "PENDING_RECEIPT_HASH",
        "verified_through": "name.com sandbox API",
        "mutable": True,
        "operations": ["domain search", "availability check", "sandbox registration", "TXT create", "TXT read-back"],
        "published": True,
        "matches": True,
        "fqdn": "_before.syn-receipt-001.timeout-receipts-demo.com.",
        "caveat": "Sandbox DNS does not propagate publicly and the record is owner-mutable; this is not a notary.",
    }

    def __init__(
        self,
        offline: bool = True,
        operation_cache: OperationCache | None = None,
        host: str | None = None,
        digest: str | None = None,
    ) -> None:
        super().__init__(offline=offline, operation_cache=operation_cache)
        self.host = host
        self.digest = digest

    def replay(self) -> DnsReceiptResult:
        result = super().replay()
        if not self.host or not self.digest:
            return result
        domain = "timeout-receipts-demo.com"
        return DnsReceiptResult(
            **{
                **asdict(result),
                "domain": domain,
                "txt_name": self.host,
                "txt_value": f"before-receipt-v1 sha256={self.digest}",
                "fqdn": f"{self.host}.{domain}.",
                "verified_through": "seeded offline replay shaped from the name.com sandbox API",
            }
        )
    def _run_operation(self, *, offline: bool) -> DnsReceiptResult:
        if not self.host or not self.digest:
            if offline:
                raise OperationCacheMiss("Receipt host and digest are required for exact DNS replay.")
            raise IntegrationError("Receipt host and digest are required for name.com publication.")
        sponsor_clients.namecom_publish_receipt(
            self.host,
            self.digest,
            offline=offline,
            cache=self.operation_cache,
        )
        verification = sponsor_clients.verify_receipt(
            self.host,
            self.digest,
            offline=offline,
            cache=self.operation_cache,
        )
        domain = os.getenv("NAMECOM_REGISTRY_DOMAIN", "timeout-receipts-demo.com")
        return DnsReceiptResult(
            vendor="name.com CORE sandbox",
            domain=domain,
            txt_name=self.host,
            txt_value=f"before-receipt-v1 sha256={self.digest}",
            verified_through="name.com sandbox API read-back",
            mutable=True,
            operations=["TXT create", "TXT read-back"],
            published=bool(verification.get("published")),
            matches=bool(verification.get("matches")),
            fqdn=str(verification.get("fqdn") or f"{self.host}.{domain}."),
            caveat=str(verification.get("caveat") or "Sandbox DNS is owner-mutable and does not propagate publicly; this is not a notary."),
        )


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
