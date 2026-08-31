"""Live sponsor API calls.

Every function here performs a real network request against a sponsor API and
returns the raw response payload. Callers are responsible for mapping the payload
onto a typed result and for caching it.

Design rules (see AGENTS.md):
  * Nothing here decides legality or performs clinical arithmetic.
  * Every call has an explicit timeout and raises a typed error on failure.
  * Responses are returned verbatim so the caller can cache them for offline replay.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TIMEOUT = 45


class LiveCallError(RuntimeError):
    """A sponsor API was reachable but did not return a usable response."""


class NotConfigured(LiveCallError):
    """Required credentials are absent from the environment."""

def _requests():
    """Import lazily so the offline demo never needs a network library installed."""
    try:
        import requests  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise NotConfigured("Live sponsor calls need `pip install requests`.") from exc
    return requests



def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise NotConfigured(f"{name} is not set in the environment.")
    return value


def _check(response, vendor: str) -> None:
    if response.status_code >= 400:
        raise LiveCallError(
            f"{vendor} returned HTTP {response.status_code}: {response.text[:300]}"
        )


# ---------------------------------------------------------------- Nutrient DWS

def _nutrient_parse_live(document: Path) -> dict[str, Any]:
    """Parse a document into spatial elements with per-element confidence.

    Returns the DWS payload verbatim. Confidence values drive human-review
    routing upstream; this function never decides what is acceptable.
    """
    key = _env("NUTRIENT_EXTRACTION_API_KEY")
    with document.open("rb") as handle:
        response = _requests().post(
            "https://api.nutrient.io/extraction/parse",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (document.name, handle, "application/pdf")},
            timeout=TIMEOUT,
        )
    _check(response, "Nutrient parse")
    return response.json()


def _nutrient_build_pdf_live(html: str, filename: str = "index.html") -> bytes:
    """Render HTML to PDF through the DWS Processor API."""
    key = _env("NUTRIENT_PROCESSOR_API_KEY")
    response = _requests().post(
        "https://api.nutrient.io/build",
        headers={"Authorization": f"Bearer {key}"},
        files={
            "instructions": (None, '{"parts":[{"html":"%s"}]}' % filename),
            filename: (filename, html.encode("utf-8"), "text/html"),
        },
        timeout=TIMEOUT,
    )
    _check(response, "Nutrient build")
    return response.content


def summarise_parse(payload: dict[str, Any], floor: float = 0.80) -> dict[str, Any]:
    """Reduce a parse payload to the fields the Gate needs.

    `floor` is the confidence below which an element must be seen by a human.
    The threshold lives here, in code — never in a model prompt.
    """
    elements = payload.get("output", {}).get("elements", []) or []
    scored = [
        {
            "text": element.get("text", "")[:200],
            "role": element.get("role"),
            "confidence": element.get("confidence"),
            "page": (element.get("page") or {}).get("pageNumber"),
            "bounds": element.get("bounds"),
        }
        for element in elements
        if isinstance(element.get("confidence"), (int, float))
    ]
    low = [item for item in scored if item["confidence"] < floor]
    return {
        "elements_total": len(elements),
        "elements_scored": len(scored),
        "confidence_floor": floor,
        "low_confidence_count": len(low),
        "review_required": bool(low),
        "lowest": min((item["confidence"] for item in scored), default=None),
        "low_confidence_elements": low[:10],
        "pages_processed": payload.get("metrics", {}).get("pagesProcessed"),
    }


# --------------------------------------------------------------------- SerpApi

def _serpapi_search_live(query: str, num: int = 5) -> dict[str, Any]:
    """Run a live search. Results are alert *candidates* only.

    A hit never establishes that a product is counterfeit, that a licence is
    invalid, or that the law has changed. A named human confirms or dismisses.
    """
    response = _requests().get(
        "https://serpapi.com/search",
        params={
            "engine": "google",
            "q": query,
            "num": num,
            "api_key": _env("SERPAPI_KEY"),
        },
        timeout=TIMEOUT,
    )
    _check(response, "SerpApi")
    return response.json()


def alert_candidates(payload: dict[str, Any], query: str) -> list[dict[str, Any]]:
    """Map raw search results onto unconfirmed alert candidates."""
    return [
        {
            "title": result.get("title"),
            "source_url": result.get("link"),
            "snippet": result.get("snippet"),
            "published_at": result.get("date"),
            "query": query,
            "status": "CANDIDATE",
            "boundary": "Search result only. A named human must confirm or dismiss it.",
        }
        for result in payload.get("organic_results", [])[:5]
    ]


# -------------------------------------------------------------------- name.com

def _namecom_auth() -> tuple[str, str]:
    return _env("NAMECOM_USERNAME"), _env("NAMECOM_TOKEN")


def _namecom_publish_receipt_live(host: str, digest: str) -> dict[str, Any]:
    """Publish a receipt digest as a DNS TXT record — idempotently.

    If a TXT record already exists for `host`, it is updated in place rather than
    duplicated. Sandbox DNS does not propagate publicly, so verification reads the
    record back through the API. A TXT record is mutable by its owner: this is a
    verification channel, not an immutable notary.
    """
    base = _env("NAMECOM_BASE_URL")
    domain = _env("NAMECOM_REGISTRY_DOMAIN")
    body = {"host": host, "type": "TXT", "answer": f"before-receipt-v1 sha256={digest}", "ttl": 300}
    existing = _namecom_read_receipt_live(host)
    if existing and existing.get("id"):
        response = _requests().put(
            f"{base}/core/v1/domains/{domain}/records/{existing['id']}",
            auth=_namecom_auth(), json=body, timeout=TIMEOUT,
        )
        _check(response, "name.com update record")
        payload = response.json(); payload["operation"] = "updated"; return payload
    response = _requests().post(
        f"{base}/core/v1/domains/{domain}/records",
        auth=_namecom_auth(), json=body, timeout=TIMEOUT,
    )
    _check(response, "name.com create record")
    payload = response.json(); payload["operation"] = "created"; return payload


def _namecom_read_receipt_live(host: str) -> dict[str, Any] | None:
    """Read a published receipt record back through the sandbox API."""
    base = _env("NAMECOM_BASE_URL")
    domain = _env("NAMECOM_REGISTRY_DOMAIN")
    response = _requests().get(
        f"{base}/core/v1/domains/{domain}/records",
        auth=_namecom_auth(),
        timeout=TIMEOUT,
    )
    if response.status_code == 401:
        raise NotConfigured(
            "name.com token is not active yet (sandbox tokens take 15+ minutes). Retry later."
        )
    _check(response, "name.com list records")
    for record in response.json().get("records", []):
        if record.get("host") == host and record.get("type") == "TXT":
            return record
    return None


def _verify_receipt_live(host: str, digest: str) -> dict[str, Any]:
    """Confirm the published record still matches the digest we hold."""
    record = _namecom_read_receipt_live(host)
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


# ---- clinic onboarding: give every clinic its own verification domain --------
#
# Publishing every receipt under one domain we control is a trust weakness we
# already state out loud: the patient still has to trust us. The fix is a
# provisioning step at clinic onboarding — search for a domain that belongs to the
# clinic, confirm it is actually purchasable, register it, then publish that
# clinic's receipts underneath it. A patient then verifies against their own
# clinic's domain, and we are no longer in the trust path.

def _namecom_search_live(keyword: str, tlds: list[str] | None = None) -> dict[str, Any]:
    """Suggest verification domains for a clinic name."""
    response = _requests().post(
        f"{_env('NAMECOM_BASE_URL').rstrip('/')}/core/v1/domains:search",
        auth=_namecom_auth(),
        json={"keyword": keyword, "tldFilter": tlds or ["com", "org", "health", "care"]},
        timeout=TIMEOUT,
    )
    _check(response, "name.com domain search")
    return response.json()


def _namecom_check_availability_live(domains: list[str]) -> dict[str, Any]:
    """Confirm a candidate is purchasable before anyone is shown a price."""
    response = _requests().post(
        f"{_env('NAMECOM_BASE_URL').rstrip('/')}/core/v1/domains:checkAvailability",
        auth=_namecom_auth(),
        json={"domainNames": domains},
        timeout=TIMEOUT,
    )
    _check(response, "name.com availability check")
    return response.json()


def _namecom_register_live(domain: str, years: int = 1) -> dict[str, Any]:
    """Register a clinic's verification domain in the name.com sandbox.

    Registration is the one irreversible step in this flow, so it is never called
    from a page a visitor can click — only from the onboarding script, deliberately.
    """
    response = _requests().post(
        f"{_env('NAMECOM_BASE_URL').rstrip('/')}/core/v1/domains",
        auth=_namecom_auth(),
        json={"domain": {"domainName": domain}, "years": years, "purchasePrice": None},
        timeout=TIMEOUT,
    )
    _check(response, "name.com domain registration")
    return response.json()


def _namecom_list_domains_live() -> dict[str, Any]:
    """Which verification domains this account already holds."""
    response = _requests().get(
        f"{_env('NAMECOM_BASE_URL').rstrip('/')}/core/v1/domains",
        auth=_namecom_auth(), timeout=TIMEOUT,
    )
    _check(response, "name.com list domains")
    return response.json()


# ---- receipt status: DNS as the revocation channel ---------------------------
#
# The product's central claim is that ready is reversible — a confirmed FDA alert
# or board action moves an encounter back to human review. That works right up to
# the moment a receipt is issued. After that the patient is holding a piece of paper
# that says the checks passed, and nothing tells them if it later stopped being true.
#
# Certificates solved this with revocation lists. A receipt gets a status record
# alongside its digest record, so the digest answers "is this the receipt that was
# issued?" and the status answers "is it still good?". Those are different questions
# and conflating them is how a stale record ends up looking authoritative.

STATUS_PREFIX = "_status"


def _status_host(receipt_id: str) -> str:
    return f"{STATUS_PREFIX}.{receipt_id.lower()}"


def _namecom_find_record(domain: str, host: str) -> dict[str, Any] | None:
    response = _requests().get(
        f"{_env('NAMECOM_BASE_URL').rstrip('/')}/core/v1/domains/{domain}/records",
        auth=_namecom_auth(), timeout=TIMEOUT,
    )
    _check(response, "name.com list records")
    for record in response.json().get("records", []):
        if record.get("host") == host and record.get("type") == "TXT":
            return record
    return None


def _namecom_publish_status_live(
    domain: str, receipt_id: str, status: str, reason: str = "", at: str = "",
) -> dict[str, Any]:
    """Publish or update a receipt's status. VALID on seal, REVOKED when reopened.

    Written in place rather than appended: a receipt has one current status, and two
    conflicting TXT answers would be worse than none.
    """
    if status not in {"VALID", "REVOKED"}:
        raise IntegrationError(f"Unsupported receipt status: {status}")
    base = _env("NAMECOM_BASE_URL").rstrip("/")
    host = _status_host(receipt_id)
    answer = f"timeout-status-v1 status={status}"
    if reason:
        answer += f" reason={reason}"
    if at:
        answer += f" at={at}"
    body = {"host": host, "type": "TXT", "answer": answer, "ttl": 300}

    existing = _namecom_find_record(domain, host)
    if existing and existing.get("id"):
        response = _requests().put(
            f"{base}/core/v1/domains/{domain}/records/{existing['id']}",
            auth=_namecom_auth(), json=body, timeout=TIMEOUT,
        )
        _check(response, "name.com update status record")
        payload = response.json(); payload["operation"] = "updated"
    else:
        response = _requests().post(
            f"{base}/core/v1/domains/{domain}/records",
            auth=_namecom_auth(), json=body, timeout=TIMEOUT,
        )
        _check(response, "name.com create status record")
        payload = response.json(); payload["operation"] = "created"
    payload["status"] = status
    return payload


def _namecom_read_status_live(domain: str, receipt_id: str) -> dict[str, Any]:
    """Ask the clinic's own domain whether a receipt is still good.

    A missing record is deliberately NOT reported as valid. An unpublished receipt
    and a good one must never look the same to a patient.
    """
    record = _namecom_find_record(domain, _status_host(receipt_id))
    if record is None:
        return {
            "found": False,
            "status": "UNKNOWN",
            "note": "No status record published for this receipt. Absence is not validity.",
        }
    answer = str(record.get("answer", ""))
    fields = dict(
        part.split("=", 1) for part in answer.split() if "=" in part
    )
    return {
        "found": True,
        "status": fields.get("status", "UNKNOWN"),
        "reason": fields.get("reason", ""),
        "at": fields.get("at", ""),
        "fqdn": record.get("fqdn"),
        "answer": answer,
    }


# ---------------------------------------------------------------- Perfect Corp

PERFECTCORP_BASE = "https://yce-api-01.makeupar.com/s2s/v2.0"

# Their detector rejects large images with `error_src_face_too_small` because it
# downsamples internally. 1024px wide with a tight face crop is the working size.
PERFECTCORP_TARGET_WIDTH = 1024

SKIN_CONCERNS = [
    "wrinkle", "texture", "pore", "redness", "oiliness", "eye_bag",
    "firmness", "acne", "moisture", "radiance",
    "droopy_upper_eyelid", "droopy_lower_eyelid",
]


def _perfectcorp_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_env('PERFECTCORP_API_KEY')}",
        "Content-Type": "application/json",
    }


def prepare_face(source: Path, destination: Path) -> tuple[int, int]:
    """Crop to the face and resize to the width their detector accepts."""
    from PIL import Image

    image = Image.open(source).convert("RGB")
    width, height = image.size
    tight = image.crop(
        (int(width * 0.22), int(height * 0.05), int(width * 0.78), int(height * 0.88))
    )
    scaled = tight.resize(
        (PERFECTCORP_TARGET_WIDTH, int(PERFECTCORP_TARGET_WIDTH * tight.height / tight.width)),
        Image.LANCZOS,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    scaled.save(destination, quality=95)
    return scaled.size


def _perfectcorp_upload_live(image: Path) -> str:
    """Reserve an upload slot and PUT the bytes. Returns their file id."""
    size = image.stat().st_size
    response = _requests().post(
        f"{PERFECTCORP_BASE}/file/skin-analysis",
        headers=_perfectcorp_headers(),
        json={"files": [{"content_type": "image/jpeg", "file_name": image.name, "file_size": size}]},
        timeout=TIMEOUT,
    )
    _check(response, "Perfect Corp upload slot")
    entry = response.json()["data"]["files"][0]
    slot = entry["requests"][0]
    put = _requests().put(slot["url"], data=image.read_bytes(), headers=slot["headers"], timeout=180)
    _check(put, "Perfect Corp S3 upload")
    return entry["file_id"]


def _perfectcorp_skin_analysis_live(
    file_id: str, concerns: list[str] | None = None, poll_seconds: int = 4, max_polls: int = 30
) -> dict[str, Any]:
    """Submit the analysis task and poll until it resolves.

    Returns the raw task payload. Scores are a documentation and communication
    aid — never a diagnosis, and never an input to the Gate's legal reasoning.
    """
    submit = _requests().post(
        f"{PERFECTCORP_BASE}/task/skin-analysis",
        headers=_perfectcorp_headers(),
        json={"src_file_id": file_id, "dst_actions": concerns or SKIN_CONCERNS},
        timeout=TIMEOUT,
    )
    _check(submit, "Perfect Corp task submit")
    task_id = submit.json()["data"]["task_id"]

    import time

    for _ in range(max_polls):
        time.sleep(poll_seconds)
        poll = _requests().get(
            f"{PERFECTCORP_BASE}/task/skin-analysis/{task_id}",
            headers=_perfectcorp_headers(),
            timeout=TIMEOUT,
        )
        _check(poll, "Perfect Corp task poll")
        data = poll.json().get("data", {})
        status = data.get("status") or data.get("task_status")
        if status == "error":
            raise LiveCallError(f"Perfect Corp analysis failed: {data.get('error')}")
        if status in {"success", "done"}:
            return data
    raise LiveCallError("Perfect Corp analysis did not resolve within the polling window.")


def _perfectcorp_result_bundle_live(task_data: dict[str, Any]) -> bytes:
    """Download the raw analysis result bundle from its short-lived URL."""
    url = (task_data.get("results") or task_data.get("result") or {}).get("url")
    if not url:
        raise LiveCallError("Perfect Corp returned no result bundle.")
    response = _requests().get(url, timeout=120)
    _check(response, "Perfect Corp result bundle")
    return response.content


def parse_perfectcorp_scores(blob: bytes) -> dict[str, Any]:
    """Parse a cached Perfect Corp result bundle without network access."""
    import io
    import zipfile

    archive = zipfile.ZipFile(io.BytesIO(blob))
    payload = json.loads(archive.read("skinanalysisResult/score_info.json"))
    concerns = {
        name: entry["ui_score"]
        for name, entry in payload.items()
        if isinstance(entry, dict) and "ui_score" in entry
    }
    overall = payload.get("all", {})
    return {
        "scores": concerns,
        "overall": overall.get("score") if isinstance(overall, dict) else None,
        "skin_age": payload.get("skin_age"),
        "raw": payload,
        "masks": [name for name in archive.namelist() if name.endswith("_output.png")],
        "scope": "Baseline and communication aid. Not a diagnosis.",
    }

# ----------------------------------------------------------------- Doctavian


def _doctavian_headers() -> dict[str, str]:
    """Both credentials, every call. The bearer refreshes itself.

    Doctavian checks the api key before it looks at the bearer, so a missing key
    reports ApiKeyNotFound no matter how good the token is. The bearer lasts about an
    hour; before.doctavian_auth keeps the refresh token and renews silently rather
    than failing mid-run.
    """
    from before.doctavian_auth import bearer  # noqa: WPS433

    return {
        "Authorization": f"Bearer {bearer()}",
        "x-api-key": _env("DOCTAVIAN_API_KEY"),
        "X-Origin": os.getenv("DOCTAVIAN_ORIGIN", "https://app.mavenmule.com"),
    }


def _doctavian_base() -> str:
    return _env("DOCTAVIAN_BASE_URL").rstrip("/")


def _doctavian_upload_live(document: Path, storage_type: str, content_type: str) -> dict[str, Any]:
    """Upload a synthetic document template or merge-data file."""
    endpoint = "template" if storage_type == "document-template" else "data"
    with document.open("rb") as handle:
        response = _requests().post(
            f"{_doctavian_base()}/v1/documents/{endpoint}/upload",
            headers={**_doctavian_headers(), "X-Storage-Type": storage_type},
            files={"file": (document.name, handle, content_type)},
            timeout=TIMEOUT,
        )
    _check(response, f"Doctavian {endpoint} upload")
    return response.json()


def _doctavian_upload_template_live(document: Path) -> dict[str, Any]:
    return _doctavian_upload_live(
        document,
        storage_type="document-template",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _doctavian_upload_data_live(payload: dict[str, Any]) -> dict[str, Any]:
    response = _requests().post(
        f"{_doctavian_base()}/v1/documents/data/upload",
        headers={**_doctavian_headers(), "X-Storage-Type": "document-data"},
        files={
            "file": (
                "consent-data.synthetic.json",
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                "application/json",
            )
        },
        timeout=TIMEOUT,
    )
    _check(response, "Doctavian data upload")
    return response.json()


def _doctavian_generate_live(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a synthetic consent into Doctavian Storage."""
    response = _requests().post(
        f"{_doctavian_base()}/v1/documents/document/generate",
        headers={**_doctavian_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=TIMEOUT,
    )
    _check(response, "Doctavian document generation")
    return response.json()


def _doctavian_create_envelope_live(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a two-signer envelope; this does not imply either person signed."""
    response = _requests().post(
        f"{_doctavian_base()}/v1/signatures/envelope/create",
        headers={**_doctavian_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=TIMEOUT,
    )
    _check(response, "Doctavian envelope create")
    return response.json()


def _doctavian_send_envelope_live(envelope_id: str) -> dict[str, Any]:
    """Send an existing envelope to its treatment-party recipients."""
    response = _requests().get(
        f"{_doctavian_base()}/v1/signatures/envelope/{envelope_id}/send",
        headers=_doctavian_headers(),
        timeout=TIMEOUT,
    )
    _check(response, "Doctavian envelope send")
    if not response.content:
        return {"envelopeId": envelope_id, "status": "SENT"}
    try:
        return response.json()
    except ValueError:
        return {"envelopeId": envelope_id, "status": "SENT", "response": response.text[:200]}

# --------------------------------------------------------------------- Foxit

# api.foxit.com sits behind a Cloudflare challenge; the fusion host their own MCP
# server targets accepts plain credentials.
FOXIT_BASE = "https://na1.fusion.foxit.com/pdf-services"


def _foxit_headers() -> dict[str, str]:
    return {
        "client_id": _env("FOXIT_CLIENT_ID"),
        "client_secret": _env("FOXIT_CLIENT_SECRET"),
    }


def _foxit_upload_live(document: Path) -> str:
    """Upload a document for assembly. Returns Foxit's document id."""
    with document.open("rb") as handle:
        response = _requests().post(
            f"{FOXIT_BASE}/api/documents/upload",
            headers=_foxit_headers(),
            files={"file": (document.name, handle, "application/pdf")},
            timeout=TIMEOUT,
        )
    _check(response, "Foxit upload")
    return response.json()["documentId"]
