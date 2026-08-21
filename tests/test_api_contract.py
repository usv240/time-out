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
