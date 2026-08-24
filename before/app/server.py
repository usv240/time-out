"""Dependency-free HTTP server for the BEFORE public site and API contract."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .cache import OperationCache
from .integrations import CacheMiss, IntegrationError, seed_all_caches
from .service import BeforeService, WorkflowError


SITE_ROOT = Path(__file__).resolve().parents[1] / "site"
ARTIFACT_ROOT = Path(__file__).resolve().parents[2] / "output" / "pdf"
ROUTE_FILES = {
    "/": "index.html",
    "/try": "try.html",
    "/api": "api.html",
    "/evidence": "evidence.html",
    "/how-it-works": "how-it-works.html",
}
PHI_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
)


class BeforeHandler(BaseHTTPRequestHandler):
    service = BeforeService(offline=True)
    requests_by_ip: dict[str, deque[float]] = defaultdict(deque)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Before-Sandbox", "synthetic-data-only")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str, remedy: str) -> None:
        self._json(status, {"error": {"code": code, "message": message, "remedy": remedy}})

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise WorkflowError("Request body exceeds the 1 MB synthetic sandbox limit.")
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("JSON body must be an object.")
        if self._contains_phi(payload):
            raise WorkflowError("Possible real personal data detected. The sandbox accepts synthetic data only.")
        return payload

    @classmethod
    def _contains_phi(cls, value: Any) -> bool:
        if isinstance(value, dict):
            return any(cls._contains_phi(item) for item in value.values())
        if isinstance(value, list):
            return any(cls._contains_phi(item) for item in value)
        if not isinstance(value, str) or value.startswith("SYN-"):
            return False
        return any(pattern.search(value) for pattern in PHI_PATTERNS)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return False
        token = header.removeprefix("Bearer ").strip()
        expires = self.service.keys.get(token)
        if not expires:
            return False
        from datetime import UTC, datetime
        return datetime.fromisoformat(expires) > datetime.now(UTC)

    def _rate_limited(self) -> bool:
        ip = self.client_address[0]
        now = time.monotonic()
        window = self.requests_by_ip[ip]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= 60:
            return True
        window.append(now)
        return False

    def _serve_file(self, path: Path, root: Path = SITE_ROOT) -> None:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root.resolve())
        except (FileNotFoundError, ValueError):
            self._error(404, "NOT_FOUND", "Static resource not found.", "Check the route and retry.")
            return
        body = resolved.read_bytes()
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith(("text/", "application/javascript", "application/json")) else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self._rate_limited():
            self._error(429, "RATE_LIMITED", "Synthetic sandbox limit is 60 requests per minute.", "Wait one minute and retry.")
            return
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path in ROUTE_FILES:
                self._serve_file(SITE_ROOT / ROUTE_FILES[path])
            elif path == "/artifacts/synthetic-safety-evidence-record.pdf":
                self._serve_file(ARTIFACT_ROOT / "synthetic-safety-evidence-record.pdf", ARTIFACT_ROOT)
            elif path.startswith("/assets/") or path.startswith("/data/") or path in {"/styles.css", "/product.css", "/integration-proof.css", "/shell.js", "/app.js", "/console.js", "/console-v2.js", "/api-page.js", "/receipt.js", "/receipt-v2.js"}:
                self._serve_file(SITE_ROOT / path.lstrip("/"))
            elif path == "/v1/encounters":
                self._json(200, {"items": self.service.list_encounters(), "synthetic": True})
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)", path):
                self._json(200, self.service.get_encounter(match.group(1)))
            elif match := re.fullmatch(r"/v1/receipts/([^/]+)", path):
                self._json(200, self.service.get_receipt(match.group(1)))
            elif path == "/v1/rules/TX/NEUROTOXIN_INJECTION":
                self._json(200, self.service.rule)
            elif match := re.fullmatch(r"/receipt/([^/]+)", path):
                self._serve_file(SITE_ROOT / "receipt.html")
            else:
                self._error(404, "NOT_FOUND", "Route not found.", "Open /api for the supported endpoint list.")
        except KeyError:
            self._error(404, "NOT_FOUND", "Synthetic record not found.", "Reset the demo and retry with a seeded identifier.")
        except (WorkflowError, CacheMiss, IntegrationError) as exc:
            self._error(409, "WORKFLOW_CONFLICT", str(exc), "Review the encounter state and cached integration setup.")

    def do_POST(self) -> None:
        if self._rate_limited():
            self._error(429, "RATE_LIMITED", "Synthetic sandbox limit is 60 requests per minute.", "Wait one minute and retry.")
            return
        path = urlparse(self.path).path.rstrip("/")
        try:
            body = self._body()
            public_paths = {"/v1/sandbox-keys", "/v1/demo/reset", "/v1/demo/run", "/v1/encounters/demo/evaluate", "/v1/receipts/verify"}
            protected_paths = path.startswith("/v1/") and path not in public_paths
            if protected_paths and not self._authorized():
                self._error(401, "UNAUTHORIZED", "A valid synthetic sandbox bearer key is required.", "POST /v1/sandbox-keys, then retry with Authorization: Bearer bfr_sbx_...")
                return
            if path == "/v1/sandbox-keys":
                self._json(201, self.service.issue_sandbox_key())
            elif path == "/v1/encounters":
                self._json(201, self.service.create_encounter(body.get("fixture_id", "rn-clear")))
            elif path == "/v1/webhooks":
                self._json(201, self.service.register_webhook(body.get("url", "")))
            elif path == "/v1/rule-proposals":
                self._json(201, self.service.propose_rule(body.get("proposal", {}), actor_role=body.get("actor_role", "Rule Author")))
            elif match := re.fullmatch(r"/v1/rule-proposals/([^/]+)/review", path):
                self._json(200, self.service.review_rule(match.group(1), body.get("decision", ""), actor_role=body.get("actor_role", "Medical Director")))
            elif match := re.fullmatch(r"/v1/rule-proposals/([^/]+)/activate", path):
                self._json(200, self.service.activate_rule(match.group(1), actor_role=body.get("actor_role", "Rule Administrator")))
            elif path == "/v1/demo/reset":
                self._json(200, {"items": self.service.seed(), "offline": self.service.offline})
            elif path == "/v1/demo/run":
                self._json(200, self.service.run_hero_path())
            elif path == "/v1/encounters/demo/evaluate":
                encounter_id = "SYN-ENC-BLOCKED-002"
                self.service.seed()
                self._json(200, self.service.evaluate(encounter_id))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/evaluate", path):
                self._json(200, self.service.evaluate(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/remediate", path):
                self._json(200, self.service.remediate(match.group(1), body.get("changes", {}), actor_role=body.get("actor_role", "Medical Director")))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/evidence", path):
                self._json(200, self.service.extract_with_nutrient(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/review/([^/]+)/resolve", path):
                self._json(200, self.service.resolve_review(match.group(1), match.group(2), resolution=body.get("resolution", "Confirmed from synthetic source"), actor_role=body.get("actor_role", "Medical Director")))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/consent", path):
                self._json(200, self.service.compile_consent(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/comprehension", path):
                self._json(200, self.service.record_comprehension(match.group(1), body.get("answers", []), confidence=body.get("confidence", "HIGH")))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/baseline", path):
                self._json(200, self.service.capture_baseline(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/evidence-record", path):
                self._json(200, self.service.assemble_evidence_record(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/attest", path):
                self._json(200, self.service.attest(match.group(1), actor_role=body.get("actor_role", "Medical Director")))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/alerts/scan", path):
                self._json(200, self.service.scan_alerts(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/alerts/decide", path):
                self._json(200, self.service.decide_alert(match.group(1), decision=body.get("decision", "DISMISSED"), actor_role=body.get("actor_role", "Medical Director")))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/receipt", path):
                self._json(201, self.service.seal_receipt(match.group(1)))
            elif match := re.fullmatch(r"/v1/encounters/([^/]+)/reproduce", path):
                self._json(200, self.service.reproduce_decision(match.group(1)))
            elif path == "/v1/receipts/verify":
                self._json(200, self.service.verify_receipt(body.get("receipt_hash", "")))
            else:
                self._error(404, "NOT_FOUND", "Route not found.", "Open /api for the supported endpoint list.")
        except json.JSONDecodeError:
            self._error(400, "INVALID_JSON", "Request body is not valid JSON.", "Send a JSON object with Content-Type application/json.")
        except KeyError:
            self._error(404, "NOT_FOUND", "Synthetic record not found.", "Reset the demo and retry with a seeded identifier.")
        except (WorkflowError, CacheMiss, IntegrationError) as exc:
            self._error(409, "WORKFLOW_CONFLICT", str(exc), "Review the encounter state and cached integration setup.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the BEFORE synthetic site and API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--offline", action="store_true", help="Replay all sponsor integrations from .cache only.")
    args = parser.parse_args()
    if args.offline:
        seed_all_caches()
    BeforeHandler.service = BeforeService(
        offline=args.offline,
        operation_cache=OperationCache() if args.offline else None,
    )
    BeforeHandler.service.seed()
    server = ThreadingHTTPServer((args.host, args.port), BeforeHandler)
    print(f"BEFORE running at http://{args.host}:{args.port} (offline={args.offline})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
