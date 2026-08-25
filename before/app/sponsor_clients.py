"""Public cache-first clients for live sponsor operations.

Every function accepts `offline=True` for exact replay. Product code imports this
module; only this module may call the private transports in `live.py`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .cache import OperationCache, file_sha256
from .live import (
    SKIN_CONCERNS,
    LiveCallError,
    alert_candidates,
    summarise_parse,
    _doctavian_create_envelope_live,
    _doctavian_generate_live,
    _doctavian_send_envelope_live,
    _doctavian_upload_data_live,
    _doctavian_upload_template_live,
    _foxit_upload_live,
    _namecom_publish_receipt_live,
    _namecom_read_receipt_live,
    _nutrient_build_pdf_live,
    _nutrient_parse_live,
    _perfectcorp_result_bundle_live,
    _perfectcorp_skin_analysis_live,
    _perfectcorp_upload_live,
    _serpapi_search_live,
    parse_perfectcorp_scores,
)


DEFAULT_CACHE = OperationCache()


def _cache(cache: OperationCache | None) -> OperationCache:
    return cache or DEFAULT_CACHE


def _scrub_perfectcorp_task(value: Any) -> Any:
    """Remove short-lived signed result URLs before persisting task responses."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED_SIGNED_URL]" if key.lower() == "url" else _scrub_perfectcorp_task(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub_perfectcorp_task(item) for item in value]
    return value

def _scrub_serpapi_payload(value: Any) -> Any:
    """Remove credentials SerpApi may echo inside request and pagination URLs."""
    if isinstance(value, dict):
        return {
            key: _scrub_serpapi_payload(item)
            for key, item in value.items()
            if key.lower() != "api_key"
        }
    if isinstance(value, list):
        return [_scrub_serpapi_payload(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"(?i)([?&]api_key=)[^&\s]+", r"\1[REDACTED]", value)
    return value

def nutrient_parse(document: Path, *, offline: bool = False, cache: OperationCache | None = None) -> dict[str, Any]:
    descriptor = {"document_sha256": file_sha256(document), "document_name": document.name}
    return _cache(cache).json(
        vendor="nutrient",
        operation="extraction-parse",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _nutrient_parse_live(document),
    )


def nutrient_build_pdf(
    html: str,
    filename: str = "index.html",
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> bytes:
    descriptor = {
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "filename": filename,
    }
    return _cache(cache).bytes(
        vendor="nutrient",
        operation="processor-build",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _nutrient_build_pdf_live(html, filename),
    )


def serpapi_search(
    query: str,
    num: int = 5,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    return _cache(cache).json(
        vendor="serpapi",
        operation="google-search",
        request_descriptor={"query": query, "num": num, "engine": "google"},
        offline=offline,
        live_call=lambda: _scrub_serpapi_payload(_serpapi_search_live(query, num)),
    )


def namecom_publish_receipt(
    host: str,
    digest: str,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    descriptor = {
        "host": host,
        "digest": digest,
        "registry_domain": os.getenv("NAMECOM_REGISTRY_DOMAIN", "beforereceipts-demo.com"),
    }
    return _cache(cache).json(
        vendor="namecom",
        operation="receipt-txt-create",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _namecom_publish_receipt_live(host, digest),
    )


def namecom_read_receipt(
    host: str,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any] | None:
    descriptor = {
        "host": host,
        "registry_domain": os.getenv("NAMECOM_REGISTRY_DOMAIN", "beforereceipts-demo.com"),
    }
    return _cache(cache).json(
        vendor="namecom",
        operation="receipt-txt-read",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _namecom_read_receipt_live(host),
    )


def verify_receipt(
    host: str,
    digest: str,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    record = namecom_read_receipt(host, offline=offline, cache=cache)
    if record is None:
        return {"published": False, "matches": False, "reason": "No TXT record found."}
    answer = str(record.get("answer", ""))
    return {
        "published": True,
        "matches": f"sha256={digest}" in answer,
        "fqdn": record.get("fqdn"),
        "answer": answer,
        "caveat": (
            "Sandbox DNS does not propagate publicly and a TXT record is mutable "
            "by its owner. This is a verification channel, not a notary."
        ),
    }


def perfectcorp_upload(
    image: Path,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> str:
    descriptor = {"image_sha256": file_sha256(image), "bytes": image.stat().st_size}
    return _cache(cache).json(
        vendor="perfectcorp",
        operation="skin-analysis-upload",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _perfectcorp_upload_live(image),
    )


def perfectcorp_skin_analysis(
    file_id: str,
    concerns: list[str] | None = None,
    poll_seconds: int = 4,
    max_polls: int = 30,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    requested_concerns = concerns or SKIN_CONCERNS
    operation_cache = _cache(cache)
    task_descriptor = {"file_id": file_id, "concerns": requested_concerns}
    bundle_descriptor = {"file_id": file_id, "concerns": requested_concerns, "kind": "raw-result-zip"}

    def capture_task_and_bundle() -> dict[str, Any]:
        raw = _perfectcorp_skin_analysis_live(file_id, requested_concerns, poll_seconds, max_polls)
        operation_cache.bytes(
            vendor="perfectcorp",
            operation="skin-analysis-result-bundle",
            request_descriptor=bundle_descriptor,
            offline=False,
            live_call=lambda: _perfectcorp_result_bundle_live(raw),
        )
        sanitized = _scrub_perfectcorp_task(raw)
        sanitized["_bundle_descriptor"] = bundle_descriptor
        return sanitized

    return operation_cache.json(
        vendor="perfectcorp",
        operation="skin-analysis-task",
        request_descriptor=task_descriptor,
        offline=offline,
        live_call=capture_task_and_bundle,
    )


def perfectcorp_scores(
    task_data: dict[str, Any],
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    descriptor = task_data.get("_bundle_descriptor")
    if not isinstance(descriptor, dict):
        raise ValueError("Perfect Corp task data does not reference a cached result bundle.")
    blob = _cache(cache).bytes(
        vendor="perfectcorp",
        operation="skin-analysis-result-bundle",
        request_descriptor=descriptor,
        offline=True,
        live_call=lambda: (_ for _ in ()).throw(AssertionError("result bundle must already be cached")),
    )
    return parse_perfectcorp_scores(blob)


def _scrub_doctavian_payload(value: Any) -> Any:
    """Do not persist recipient addresses, bearer-like values, or signed URLs."""
    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if "email" in lowered or "token" in lowered or lowered == "authorization":
                scrubbed[key] = "[REDACTED]"
            elif "url" in lowered and isinstance(item, str):
                scrubbed[key] = "[REDACTED_URL]"
            else:
                scrubbed[key] = _scrub_doctavian_payload(item)
        return scrubbed
    if isinstance(value, list):
        return [_scrub_doctavian_payload(item) for item in value]
    if isinstance(value, str) and value.startswith(("http://", "https://")) and re.search(r"(?i)[?&](?:token|signature|key)=", value):
        return "[REDACTED_URL]"
    return value


def doctavian_upload_template(
    document: Path,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    descriptor = {"document_sha256": file_sha256(document), "template_version": "TX-NEUROTOXIN-CONSENT-1"}
    return _cache(cache).json(
        vendor="doctavian",
        operation="template-upload",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _scrub_doctavian_payload(_doctavian_upload_template_live(document)),
    )


def doctavian_upload_data(
    payload: dict[str, Any],
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    descriptor = {"payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "synthetic": True}
    return _cache(cache).json(
        vendor="doctavian",
        operation="data-upload",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _scrub_doctavian_payload(_doctavian_upload_data_live(payload)),
    )


def doctavian_generate(
    template_urn: str,
    data_urn: str,
    encounter_id: str,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    payload = {
        "externalContext": {"id": encounter_id},
        "template": {
            "name": "tx-neurotoxin-consent-v1.docx",
            "urn": template_urn,
            "fileFormat": "docx",
            "loadMethod": "Storage",
            "options": {},
        },
        "data": {"loadMethod": "Storage", "urn": data_urn},
        "document": {
            "name": f"BEFORE-{encounter_id}-consent",
            "fileFormat": "pdf",
            "deliveryMethod": "Storage",
            "path": "root",
            "locale": "en",
            "timezone": "UTC",
            "options": {},
        },
    }
    return _cache(cache).json(
        vendor="doctavian",
        operation="document-generate",
        request_descriptor={"template_urn": template_urn, "data_urn": data_urn, "encounter_id": encounter_id},
        offline=offline,
        live_call=lambda: _scrub_doctavian_payload(_doctavian_generate_live(payload)),
    )


def doctavian_create_envelope(
    document_urn: str,
    encounter_id: str,
    recipients: list[dict[str, str]],
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    recipient_payload = [
        {
            "referenceSignerId": item["reference_signer_id"],
            "name": item["name"],
            "email": item["email"],
            "role": "signer",
            "mandatory": True,
        }
        for item in recipients
    ]
    payload = {
        "documents": [
            {
                "referenceDocumentId": "consent",
                "name": f"BEFORE-{encounter_id}-consent.pdf",
                "urn": document_urn,
                "loadMethod": "Storage",
            }
        ],
        "recipients": recipient_payload,
        "fields": [
            {
                "type": "signature",
                "required": True,
                "referenceSignerId": "patient",
                "referenceDocumentId": "consent",
                "anchorString": "_SIG_PATIENT_",
            },
            {
                "type": "signature",
                "required": True,
                "referenceSignerId": "injector",
                "referenceDocumentId": "consent",
                "anchorString": "_SIG_INJECTOR_",
            },
        ],
        "envelope": {
            "subject": "BEFORE synthetic treatment consent",
            "message": "Synthetic hackathon demonstration. No real patient or procedure.",
            "externalContext": {"id": encounter_id},
        },
    }
    recipient_descriptor = [
        {
            "reference_signer_id": item["reference_signer_id"],
            "name": item["name"],
            "email_sha256": hashlib.sha256(item["email"].encode("utf-8")).hexdigest(),
        }
        for item in recipients
    ]
    return _cache(cache).json(
        vendor="doctavian",
        operation="envelope-create",
        request_descriptor={"document_urn": document_urn, "encounter_id": encounter_id, "recipients": recipient_descriptor},
        offline=offline,
        live_call=lambda: _scrub_doctavian_payload(_doctavian_create_envelope_live(payload)),
    )


def doctavian_send_envelope(
    envelope_id: str,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    return _cache(cache).json(
        vendor="doctavian",
        operation="envelope-send",
        request_descriptor={"envelope_id": envelope_id},
        offline=offline,
        live_call=lambda: _scrub_doctavian_payload(_doctavian_send_envelope_live(envelope_id)),
    )


def foxit_upload(
    document: Path,
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> str:
    descriptor = {"document_sha256": file_sha256(document), "document_name": document.name}
    return _cache(cache).json(
        vendor="foxit",
        operation="document-upload",
        request_descriptor=descriptor,
        offline=offline,
        live_call=lambda: _foxit_upload_live(document),
    )
