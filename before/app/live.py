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

import requests

ROOT = Path(__file__).resolve().parents[2]
TIMEOUT = 45


class LiveCallError(RuntimeError):
    """A sponsor API was reachable but did not return a usable response."""


class NotConfigured(LiveCallError):
    """Required credentials are absent from the environment."""


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise NotConfigured(f"{name} is not set in the environment.")
    return value


def _check(response: requests.Response, vendor: str) -> None:
    if response.status_code >= 400:
        raise LiveCallError(
            f"{vendor} returned HTTP {response.status_code}: {response.text[:300]}"
        )


# ---------------------------------------------------------------- Nutrient DWS

def nutrient_parse(document: Path) -> dict[str, Any]:
    """Parse a document into spatial elements with per-element confidence.

    Returns the DWS payload verbatim. Confidence values drive human-review
    routing upstream; this function never decides what is acceptable.
    """
    key = _env("NUTRIENT_EXTRACTION_API_KEY")
    with document.open("rb") as handle:
        response = requests.post(
            "https://api.nutrient.io/extraction/parse",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (document.name, handle, "application/pdf")},
            timeout=TIMEOUT,
        )
    _check(response, "Nutrient parse")
    return response.json()


def nutrient_build_pdf(html: str, filename: str = "index.html") -> bytes:
    """Render HTML to PDF through the DWS Processor API."""
    key = _env("NUTRIENT_PROCESSOR_API_KEY")
    response = requests.post(
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

def serpapi_search(query: str, num: int = 5) -> dict[str, Any]:
    """Run a live search. Results are alert *candidates* only.

    A hit never establishes that a product is counterfeit, that a licence is
    invalid, or that the law has changed. A named human confirms or dismisses.
    """
    response = requests.get(
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
            "query": query,
            "status": "CANDIDATE",
            "boundary": "Search result only. A named human must confirm or dismiss it.",
        }
        for result in payload.get("organic_results", [])[:5]
    ]


# -------------------------------------------------------------------- name.com

def _namecom_auth() -> tuple[str, str]:
    return _env("NAMECOM_USERNAME"), _env("NAMECOM_TOKEN")


def namecom_publish_receipt(host: str, digest: str) -> dict[str, Any]:
    """Publish a receipt digest as a DNS TXT record.

    Sandbox DNS does not propagate publicly, so verification reads the record
    back through the API. A TXT record is mutable by its owner: this is a
    verification channel, not an immutable notary.
    """
    base = _env("NAMECOM_BASE_URL")
    domain = _env("NAMECOM_REGISTRY_DOMAIN")
    response = requests.post(
        f"{base}/core/v1/domains/{domain}/records",
        auth=_namecom_auth(),
        json={
            "host": host,
            "type": "TXT",
            "answer": f"before-receipt-v1 sha256={digest}",
            "ttl": 300,
        },
        timeout=TIMEOUT,
    )
    _check(response, "name.com create record")
    return response.json()


def namecom_read_receipt(host: str) -> dict[str, Any] | None:
    """Read a published receipt record back through the sandbox API."""
    base = _env("NAMECOM_BASE_URL")
    domain = _env("NAMECOM_REGISTRY_DOMAIN")
    response = requests.get(
        f"{base}/core/v1/domains/{domain}/records",
        auth=_namecom_auth(),
        timeout=TIMEOUT,
    )
    _check(response, "name.com list records")
    for record in response.json().get("records", []):
        if record.get("host") == host and record.get("type") == "TXT":
            return record
    return None


def verify_receipt(host: str, digest: str) -> dict[str, Any]:
    """Confirm the published record still matches the digest we hold."""
    record = namecom_read_receipt(host)
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


def perfectcorp_upload(image: Path) -> str:
    """Reserve an upload slot and PUT the bytes. Returns their file id."""
    size = image.stat().st_size
    response = requests.post(
        f"{PERFECTCORP_BASE}/file/skin-analysis",
        headers=_perfectcorp_headers(),
        json={"files": [{"content_type": "image/jpeg", "file_name": image.name, "file_size": size}]},
        timeout=TIMEOUT,
    )
    _check(response, "Perfect Corp upload slot")
    entry = response.json()["data"]["files"][0]
    slot = entry["requests"][0]
    put = requests.put(slot["url"], data=image.read_bytes(), headers=slot["headers"], timeout=180)
    _check(put, "Perfect Corp S3 upload")
    return entry["file_id"]


def perfectcorp_skin_analysis(
    file_id: str, concerns: list[str] | None = None, poll_seconds: int = 4, max_polls: int = 30
) -> dict[str, Any]:
    """Submit the analysis task and poll until it resolves.

    Returns the raw task payload. Scores are a documentation and communication
    aid — never a diagnosis, and never an input to the Gate's legal reasoning.
    """
    submit = requests.post(
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
        poll = requests.get(
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


def perfectcorp_scores(task_data: dict[str, Any], cache_dir: Path | None = None) -> dict[str, Any]:
    """Download the result bundle and return the per-concern scores."""
    import io
    import zipfile

    url = (task_data.get("results") or task_data.get("result") or {}).get("url")
    if not url:
        raise LiveCallError("Perfect Corp returned no result bundle.")
    blob = requests.get(url, timeout=120).content

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "skin-analysis.zip").write_bytes(blob)

    archive = zipfile.ZipFile(io.BytesIO(blob))
    payload = json.loads(archive.read("skinanalysisResult/score_info.json"))

    # Per-concern entries carry `ui_score`; `all`, `skin_age` and `resize_image`
    # are summary keys with different shapes.
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
        "masks": [n for n in archive.namelist() if n.endswith("_output.png")],
        "scope": "Baseline and communication aid. Not a diagnosis.",
    }


# --------------------------------------------------------------------- Foxit

# api.foxit.com sits behind a Cloudflare challenge; the fusion host their own MCP
# server targets accepts plain credentials.
FOXIT_BASE = "https://na1.fusion.foxit.com/pdf-services"


def _foxit_headers() -> dict[str, str]:
    return {
        "client_id": _env("FOXIT_CLIENT_ID"),
        "client_secret": _env("FOXIT_CLIENT_SECRET"),
    }


def foxit_upload(document: Path) -> str:
    """Upload a document for assembly. Returns Foxit's document id."""
    with document.open("rb") as handle:
        response = requests.post(
            f"{FOXIT_BASE}/api/documents/upload",
            headers=_foxit_headers(),
            files={"file": (document.name, handle, "application/pdf")},
            timeout=TIMEOUT,
        )
    _check(response, "Foxit upload")
    return response.json()["documentId"]
