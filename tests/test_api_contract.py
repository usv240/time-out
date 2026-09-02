from __future__ import annotations

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from before.app.integrations import seed_all_caches
from before.app.server import BeforeHandler
from before.app.service import BeforeService


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_all_caches()
        BeforeHandler.service = BeforeService(offline=True)
        BeforeHandler.service.seed()
        BeforeHandler.requests_by_ip.clear()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), BeforeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method: str, path: str, payload: dict | None = None, token: str | None = None):
        data = json.dumps(payload or {}).encode("utf-8") if method == "POST" else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(self.base + path, data=data, method=method, headers=headers)
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read()) if "application/json" in response.headers.get("Content-Type", "") else response.read()

    def test_public_routes_and_seeded_gate_are_working(self):
        for route in ("/", "/try", "/api", "/evidence", "/how-it-works"):
            with self.subTest(route=route):
                request = Request(self.base + route)
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(200, response.status)
        status, result = self.request("POST", "/v1/encounters/demo/evaluate")
        self.assertEqual(200, status)
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual(7, len(result["findings"]))

    def test_instant_sandbox_key_and_synthetic_encounter_creation(self):
        status, key = self.request("POST", "/v1/sandbox-keys")
        self.assertEqual(201, status)
        self.assertTrue(key["key"].startswith("bfr_sbx_"))
        status, encounter = self.request("POST", "/v1/encounters", {"fixture_id": "rn-clear"}, token=key["key"])
        self.assertEqual(201, status)
        self.assertTrue(encounter["id"].startswith("SYN-ENC-API-"))

    def test_phi_like_input_is_rejected(self):
        request = Request(
            self.base + "/v1/encounters",
            data=json.dumps({"fixture_id": "rn-clear", "email": "real.person@example.com"}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(409, caught.exception.code)

    def test_rule_updates_require_human_review_before_activation(self):
        service = BeforeService(offline=True)
        proposal = service.propose_rule({"change": "Synthetic wording clarification", "citation_urls": ["https://statutes.capitol.texas.gov/docs/OC/pdf/OC.157.pdf"]})
        with self.assertRaises(Exception):
            service.activate_rule(proposal["id"])
        reviewed = service.review_rule(proposal["id"], "APPROVED")
        self.assertEqual("APPROVED", reviewed["status"])
        effective = service.activate_rule(proposal["id"])
        self.assertEqual("EFFECTIVE", effective["status"])
        self.assertEqual(64, len(effective["snapshot_sha256"]))

    def test_webhooks_are_hmac_signed_and_cached_offline(self):
        service = BeforeService(offline=True)
        service.seed()
        subscription = service.register_webhook("https://example.invalid/before-events")
        self.assertTrue(subscription["secret"].startswith("whsec_"))
        service.evaluate("SYN-ENC-BLOCKED-002")
        delivery = service.webhook_deliveries()[0]
        self.assertEqual("encounter.blocked", delivery["payload"]["event"])
        self.assertTrue(delivery["signature"].startswith("sha256="))
        self.assertEqual("CACHED_OFFLINE", delivery["delivery_status"])


if __name__ == "__main__":
    unittest.main()


def test_published_curl_matches_the_endpoint_the_page_calls() -> None:
    """The landing page prints a curl command as an invitation.

    If the printed URL and the URL the site actually calls ever drift, a judge who
    copies the command gets a different answer from the one on screen.
    """
    import re
    from pathlib import Path
    site = Path(__file__).resolve().parents[1] / "before" / "site"
    index = (site / "index.html").read_text(encoding="utf-8")
    js = (site / "api-page.js").read_text(encoding="utf-8")

    printed = re.search(r"curl -X POST (https://\S+)", index)
    assert printed, "no curl command printed on the landing page"
    url = printed.group(1).rstrip("\\")
    assert url.endswith("/v1/encounters/demo/evaluate"), url
    assert "encounters/demo/evaluate" in js, "the page calls a different endpoint than it prints"


def test_the_optional_key_never_becomes_a_credential() -> None:
    """The API is open on purpose, and a key must not quietly start gating it.

    A generated tag labels a caller's rows in the audit log. It grants nothing. If a
    future change made any endpoint require it, the demo would stop being verifiable
    by anyone who had not first asked us for something.
    """
    import json
    import urllib.request

    base = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1"

    def post(path, body=None, headers=None):
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        req = urllib.request.Request(
            base + path, data=json.dumps(body or {}).encode(), method="POST", headers=h)
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read())

    status, issued = post("/keys", {"label": "contract-test"})
    assert status == 200
    assert issued["key"].startswith("tok_demo_"), issued["key"]
    assert issued["required"] is False, "the key is documented as optional; it must stay optional"

    # The same call has to succeed three ways: with the key, with rubbish, with nothing.
    for label, headers in (("issued key", {"X-Time-Out-Key": issued["key"]}),
                           ("nonsense key", {"X-Time-Out-Key": "not-a-real-key"}),
                           ("no key", None)):
        code, body = post("/encounters/demo/evaluate", {}, headers)
        assert code == 200, f"{label} was rejected with {code}"
        assert body["verdict"] in {"CLEAR", "BLOCKED", "REVIEW"}, label


def test_the_api_refuses_bad_input_the_way_the_docs_say() -> None:
    """/api documents each of these responses. If the API stops behaving that way,
    the page becomes a lie, which is worse than not having documented it."""
    import json
    import urllib.error
    import urllib.request

    base = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1"

    def call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            base + path, data=data, method=method,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    code, body = call("GET", "/encounters/SYN-ENC-does-not-exist")
    assert code == 404 and body["code"] == "ERROR_CODE_NOT_FOUND", (code, body)

    code, body = call("POST", "/encounters", {})
    assert code == 400 and body["payload"]["param"] == "clinic_id", (code, body)

    code, body = call("POST", "/keys", {"label": "someone@example.com"})
    assert code == 400 and "email" in body["message"], (code, body)

    code, body = call("POST", "/keys", {"label": "x" * 300})
    assert code == 400 and "64 characters" in body["message"], (code, body)
