"""Public cache-first clients for live sponsor operations.

Every function accepts `offline=True` for exact replay. Product code imports this
module; only this module may call the private transports in `live.py`.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from .cache import OperationCache, file_sha256
from .live import (
    SKIN_CONCERNS,
    _foxit_upload_live,
    _namecom_publish_receipt_live,
    _namecom_read_receipt_live,
    _nutrient_build_pdf_live,
    _nutrient_parse_live,
    _perfectcorp_scores_live,
    _perfectcorp_skin_analysis_live,
    _perfectcorp_upload_live,
    _serpapi_search_live,
)


DEFAULT_CACHE = OperationCache()


def _cache(cache: OperationCache | None) -> OperationCache:
    return cache or DEFAULT_CACHE


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
        live_call=lambda: _serpapi_search_live(query, num),
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
        "registry_domain": os.getenv("NAMECOM_REGISTRY_DOMAIN", "unconfigured"),
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
        "registry_domain": os.getenv("NAMECOM_REGISTRY_DOMAIN", "unconfigured"),
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
    return _cache(cache).json(
        vendor="perfectcorp",
        operation="skin-analysis-task",
        request_descriptor={"file_id": file_id, "concerns": requested_concerns},
        offline=offline,
        live_call=lambda: _perfectcorp_skin_analysis_live(file_id, requested_concerns, poll_seconds, max_polls),
    )


def perfectcorp_scores(
    task_data: dict[str, Any],
    *,
    offline: bool = False,
    cache: OperationCache | None = None,
) -> dict[str, Any]:
    return _cache(cache).json(
        vendor="perfectcorp",
        operation="skin-analysis-result",
        request_descriptor={"task_response_sha256": OperationCache.request_sha256(task_data)},
        offline=offline,
        live_call=lambda: _perfectcorp_scores_live(task_data),
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
