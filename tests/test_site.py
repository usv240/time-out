from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from pathlib import Path

from before.gate_demo import _encounter, _load, _provider
from shared.gate import evaluate_gate


ROOT = Path(__file__).resolve().parents[1]


class SiteFixtureTests(unittest.TestCase):
    def test_seeded_site_decision_matches_the_real_gate(self):
        providers = {row["provider_id"]: _provider(row) for row in _load("providers.json")}
        encounter_row = next(row for row in _load("encounters.json") if row["fixture_id"] == "aesthetician-blocked")
        decision = evaluate_gate(
            providers[encounter_row["provider_id"]],
            _encounter(encounter_row),
            _load("rules/tx-neurotoxin.json"),
        )
        site_decision = json.loads((ROOT / "before" / "site" / "data" / "demo-decision.json").read_text(encoding="utf-8"))
        expected_findings = json.loads(
            json.dumps([{**asdict(finding), "status": finding.status.value} for finding in decision.findings])
        )
        self.assertEqual(decision.encounter_id, site_decision["encounter_id"])
        self.assertEqual(decision.verdict.value, site_decision["verdict"])
        self.assertEqual(decision.determination_scope, site_decision["determination_scope"])
        self.assertEqual(decision.rule_snapshot_sha256, site_decision["rule_snapshot_sha256"])
        self.assertEqual(expected_findings, site_decision["findings"])


if __name__ == "__main__":
    unittest.main()
