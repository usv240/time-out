"""Foxit assembly agent.

Starts from a plain prompt, performs every reversible document operation through the
official Foxit PDF API MCP server, then STOPS at the irreversible boundary. The
Medical Director's attestation is handed to a human through eSign as a separate,
explicit step — never taken by the agent.

The planner is deterministic on purpose. A safety record should be assembled the
same way every time; no model chooses the steps, and no model touches the content.

Run:   python -m before.foxit_agent "assemble the safety record for encounter SYN-ENC-BLOCKED-002"
       python -m before.foxit_agent --offline      (replays the cached run)
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "output" / "pdf" / "foxit-source"
MANIFEST = SOURCE_DIR / "manifest.synthetic.json"
OUTPUT_PDF = ROOT / "output" / "pdf" / "time-out-safety-record.pdf"
CACHE_DIR = ROOT / ".cache" / "foxit"
RUN_LOG = CACHE_DIR / "agent-run.json"

WATERMARK = "SYNTHETIC - NOT FOR CLINICAL USE"
PROMPT_PATTERN = re.compile(r"encounter\s+([A-Z0-9-]+)", re.IGNORECASE)


class AgentError(RuntimeError):
    pass


@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]
    ms: int


@dataclass
class AgentRun:
    prompt: str
    encounter_id: str
    plan: list[str]
    calls: list[ToolCall] = field(default_factory=list)
    output_pdf: str | None = None
    output_sha256: str | None = None
    properties: dict[str, Any] | None = None
    paused_at_boundary: bool = False
    next_human_action: str = "Medical Director reviews and signs the attestation via Foxit eSign."
    boundary_note: str = (
        "The agent performs only reversible assembly. It never signs. "
        "Treatment-party signatures collected by Doctavian are never reused here."
    )
    started_at: str = ""
    finished_at: str = ""


# ----------------------------------------------------------------- planning

def plan(prompt: str) -> tuple[str, list[str]]:
    """Map a plain prompt to a fixed, inspectable plan. No model involved."""
    match = PROMPT_PATTERN.search(prompt)
    if not match:
        raise AgentError("Prompt must name an encounter, e.g. 'assemble the safety record for encounter SYN-ENC-BLOCKED-002'.")
    encounter_id = match.group(1).upper()
    steps = [
        "upload_document x3   — the three synthetic source sections",
        "pdf-combine (REST)   — one record, in manifest order; MCP pdf_merge has a field-mapping bug",
        "pdf-watermark (REST) — mark every page SYNTHETIC; MCP pdf_watermark has field-mapping bugs",
        "get_pdf_properties   — read metadata into the manifest",
        "download_document    — save the assembled record locally",
        "STOP                 — hand attestation to a human (eSign)",
    ]
    return encounter_id, steps


def _sections() -> list[Path]:
    if not MANIFEST.exists():
        raise AgentError("Source bundle missing. Run: python -m before.build_foxit_source_bundle")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = [SOURCE_DIR / s["file"] for s in manifest.get("sections", [])]
    if not files:
        files = sorted(SOURCE_DIR.glob("0*.pdf"))
    missing = [f for f in files if not f.exists()]
    if missing:
        raise AgentError(f"Missing section PDFs: {[m.name for m in missing]}")
    return files


# ----------------------------------------------------------------- MCP glue

def _parse(result: Any) -> dict[str, Any]:
    """Tool results arrive as content blocks; find the JSON payload inside."""
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {"value": data}
        except json.JSONDecodeError:
            return {"text": text}
    return {}


def _redact(args: dict[str, Any]) -> dict[str, Any]:
    return {k: ("<base64 %d bytes>" % len(v) if k == "fileContent" else v) for k, v in args.items()}


async def _call(session, run: AgentRun, tool: str, **args) -> dict[str, Any]:
    t0 = time.perf_counter()
    raw = await session.call_tool(tool, arguments=args)
    data = _parse(raw)
    if getattr(raw, "isError", False):
        raise AgentError(f"{tool} failed: {json.dumps(data)[:300]}")
    run.calls.append(ToolCall(tool, _redact(args), data, int((time.perf_counter() - t0) * 1000)))
    return data


async def _await_document(session, run: AgentRun, data: dict[str, Any]) -> str:
    """Long operations return a task; poll until a documentId appears."""
    doc = data.get("documentId") or (data.get("result") or {}).get("documentId")
    if doc:
        return doc
    task = data.get("taskId") or (data.get("result") or {}).get("taskId")
    if not task:
        raise AgentError(f"No documentId or taskId in result: {json.dumps(data)[:300]}")
    for _ in range(40):
        await asyncio.sleep(2)
        status = await _call(session, run, "get_task_result", taskId=task)
        doc = status.get("documentId") or (status.get("result") or {}).get("documentId") \
            or (status.get("resultDocumentId"))
        if doc:
            return doc
        if str(status.get("status", "")).upper() in {"FAILED", "ERROR"}:
            raise AgentError(f"Task failed: {json.dumps(status)[:300]}")
    raise AgentError("Timed out waiting for Foxit task.")



# -------------------------------------------------------- REST merge (workaround)

FOXIT_HOST = os.environ.get("FOXIT_CLOUD_API_HOST", "https://na1.fusion.foxit.com/pdf-services")
MERGE_WORKAROUND_NOTE = (
    "pdf_merge in the TypeScript Foxit MCP server sends `documents` where the PDF "
    "Services API requires `documentInfos` (server returns VALIDATION_ERROR). Merge is "
    "routed through the same host's REST endpoint until upstream fixes the mapping. "
    "All other operations run through MCP."
)


def _rest_headers() -> dict[str, str]:
    return {
        "client_id": os.environ["FOXIT_CLOUD_API_CLIENT_ID"],
        "client_secret": os.environ["FOXIT_CLOUD_API_CLIENT_SECRET"],
    }


def _rest_merge(run: AgentRun, ids: list[str]) -> str:
    """POST pdf-combine, poll the task, return the merged documentId."""
    from before.app.live import _requests  # noqa: WPS433

    t0 = time.perf_counter()
    resp = _requests().post(
        f"{FOXIT_HOST}/api/documents/enhance/pdf-combine",
        headers={**_rest_headers(), "Content-Type": "application/json"},
        json={"documentInfos": [{"documentId": i} for i in ids]},
        timeout=60,
    )
    if resp.status_code >= 400:
        raise AgentError(f"pdf-combine failed HTTP {resp.status_code}: {resp.text[:200]}")
    task = resp.json().get("taskId")
    doc = resp.json().get("documentId")
    polls = 0
    while not doc and task and polls < 40:
        time.sleep(2); polls += 1
        status = _requests().get(f"{FOXIT_HOST}/api/tasks/{task}", headers=_rest_headers(), timeout=30).json()
        doc = status.get("resultDocumentId") or status.get("documentId")
        if str(status.get("status", "")).upper() in {"FAILED", "ERROR"}:
            raise AgentError(f"pdf-combine task failed: {json.dumps(status)[:200]}")
    if not doc:
        raise AgentError("pdf-combine did not produce a document.")
    run.calls.append(ToolCall(
        "REST pdf-combine (MCP pdf_merge workaround)",
        {"documentInfos": ids, "why": MERGE_WORKAROUND_NOTE},
        {"documentId": doc, "taskId": task, "polls": polls},
        int((time.perf_counter() - t0) * 1000),
    ))
    return doc



WATERMARK_WORKAROUND_NOTE = (
    "pdf_watermark in the TypeScript Foxit MCP server has three field mismatches with the "
    "PDF Services API (opacity scale, opacity type, and `content` vs `text`). Watermarking is "
    "routed through the same host's REST endpoint until upstream fixes the mapping."
)


def _rest_task(run: AgentRun, label: str, path: str, body: dict[str, Any], note: str) -> str:
    """POST an enhance operation, poll its task, return the result documentId."""
    from before.app.live import _requests  # noqa: WPS433

    t0 = time.perf_counter()
    resp = _requests().post(
        f"{FOXIT_HOST}{path}",
        headers={**_rest_headers(), "Content-Type": "application/json"},
        json=body, timeout=60,
    )
    if resp.status_code >= 400:
        raise AgentError(f"{label} failed HTTP {resp.status_code}: {resp.text[:200]}")
    task = resp.json().get("taskId"); doc = resp.json().get("documentId"); polls = 0
    while not doc and task and polls < 40:
        time.sleep(2); polls += 1
        status = _requests().get(f"{FOXIT_HOST}/api/tasks/{task}", headers=_rest_headers(), timeout=30).json()
        doc = status.get("resultDocumentId") or status.get("documentId")
        if str(status.get("status", "")).upper() in {"FAILED", "ERROR"}:
            raise AgentError(f"{label} task failed: {json.dumps(status)[:200]}")
    if not doc:
        raise AgentError(f"{label} did not produce a document.")
    safe = {k: v for k, v in body.items() if k != "documentInfos"}
    safe["why"] = note
    run.calls.append(ToolCall(label, safe, {"documentId": doc, "taskId": task, "polls": polls},
                              int((time.perf_counter() - t0) * 1000)))
    return doc


def _rest_watermark(run: AgentRun, document_id: str) -> str:
    return _rest_task(
        run, "REST pdf-watermark (MCP pdf_watermark workaround)",
        "/api/documents/enhance/pdf-watermark",
        {"documentId": document_id, "config": {
            "type": "TEXT", "text": WATERMARK, "opacity": 35, "rotation": 30,
            "fontSize": 42, "color": "#B3261E", "position": "CENTER"}},
        WATERMARK_WORKAROUND_NOTE,
    )


# ------------------------------------------------------------------- run

async def _run_live(prompt: str) -> AgentRun:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    for key in ("FOXIT_CLOUD_API_CLIENT_ID", "FOXIT_CLOUD_API_CLIENT_SECRET"):
        if not os.environ.get(key):
            raise AgentError(f"{key} is not set. Live assembly needs Foxit credentials.")

    encounter_id, steps = plan(prompt)
    run = AgentRun(prompt=prompt, encounter_id=encounter_id, plan=steps, started_at=_now())
    env = dict(os.environ)
    env.setdefault("FOXIT_CLOUD_API_HOST", "https://na1.fusion.foxit.com/pdf-services")
    env["DOTENV_CONFIG_QUIET"] = "true"
    params = StdioServerParameters(
        command="npx", args=["-y", "@foxitsoftware/foxit-pdf-api-mcp-server"], env=env
    )

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # 1. upload the three synthetic sections
            ids: list[str] = []
            for path in _sections():
                data = await _call(
                    session, run, "upload_document",
                    fileContent=base64.b64encode(path.read_bytes()).decode("ascii"),
                    fileName=path.name,
                )
                ids.append(await _await_document(session, run, data))

            # 2. merge, in manifest order (REST — see MERGE_WORKAROUND_NOTE)
            merged = _rest_merge(run, ids)

            # 3. watermark every page — the record must never pass as clinical (REST, see note)
            marked = _rest_watermark(run, merged)

            # 4. read properties into the manifest
            run.properties = await _call(session, run, "get_pdf_properties", documentId=marked, includePageInfo=True)

            # 5. save locally
            OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
            await _call(session, run, "download_document", documentId=marked, outputPath=str(OUTPUT_PDF))

    if not OUTPUT_PDF.exists():
        raise AgentError("Assembled PDF was not written.")
    run.output_pdf = str(OUTPUT_PDF.relative_to(ROOT))
    run.output_sha256 = hashlib.sha256(OUTPUT_PDF.read_bytes()).hexdigest()

    # 6. STOP. This is the irreversible boundary.
    run.paused_at_boundary = True
    run.finished_at = _now()
    return run


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def save(run: AgentRun) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(json.dumps(asdict(run), indent=2), encoding="utf-8")
    return RUN_LOG


FIXTURE_RUN = ROOT / "fixtures" / "foxit" / "agent-run.json"


def _find(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = _find(value, key)
            if found is not None:
                return found
    if isinstance(node, list):
        for item in node:
            found = _find(item, key)
            if found is not None:
                return found
    return None


def replay() -> AgentRun:
    """Replay the committed run. `.cache` wins if present; the fixture always exists."""
    source = RUN_LOG if RUN_LOG.exists() else FIXTURE_RUN
    if not source.exists():
        raise AgentError("No Foxit run available to replay.")
    data = json.loads(source.read_text(encoding="utf-8"))
    data["calls"] = [ToolCall(**c) for c in data["calls"]]
    return AgentRun(**data)


def run(prompt: str, offline: bool = False) -> AgentRun:
    if offline:
        return replay()
    result = asyncio.run(_run_live(prompt))
    save(result)
    return result


# ------------------------------------------------------------------ eSign

def request_attestation(pdf: Path = OUTPUT_PDF, dry_run: bool = True) -> dict[str, Any]:
    """Hand the assembled record to the Medical Director for signature.

    This is the ONE step the agent never performs on its own. `dry_run=True`
    prepares the request without sending, so the signing email is only ever
    triggered deliberately by a person.
    """
    signer = os.environ.get("FOXIT_ESIGN_MEDICAL_DIRECTOR_EMAIL", "").strip()
    if not signer:
        raise AgentError("FOXIT_ESIGN_MEDICAL_DIRECTOR_EMAIL is not set.")
    if not pdf.exists():
        raise AgentError("Assemble the record first.")
    envelope = {
        "folderName": f"Time-Out attestation — {pdf.stem}",
        "document": pdf.name,
        "document_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "signer_role": "Medical Director",
        "signer_email": signer,
        "action": "SIGN",
        "note": "Synthetic encounter. Attestation confirms the checks recorded before treatment; it certifies nothing about safety or outcome.",
    }
    if dry_run:
        return {"sent": False, "prepared": envelope}

    from before.app.live import _requests, _env, _check  # noqa: WPS433

    headers = {"client_id": _env("FOXIT_CLIENT_ID"), "client_secret": _env("FOXIT_CLIENT_SECRET")}
    with pdf.open("rb") as handle:
        response = _requests().post(
            "https://api.foxit.com/esign/api/folders",
            headers=headers,
            data={"folderName": envelope["folderName"], "signerEmail": signer, "signerRole": "Medical Director"},
            files={"file": (pdf.name, handle, "application/pdf")},
            timeout=90,
        )
    _check(response, "Foxit eSign create folder")
    payload = response.json()
    return {"sent": True, "prepared": envelope, "response": payload}


# ------------------------------------------------------------------- CLI

if __name__ == "__main__":
    argv = sys.argv[1:]
    offline = "--offline" in argv
    prompt = next((a for a in argv if not a.startswith("--")), "assemble the safety record for encounter SYN-ENC-BLOCKED-002")
    result = run(prompt, offline=offline)
    print(json.dumps({
        "encounter_id": result.encounter_id,
        "plan": result.plan,
        "tool_calls": [(c.tool, c.ms) for c in result.calls],
        "output_pdf": result.output_pdf,
        "output_sha256": result.output_sha256,
        "pages": _find(result.properties, "pageCount"),
        "paused_at_boundary": result.paused_at_boundary,
        "next_human_action": result.next_human_action,
    }, indent=2))
