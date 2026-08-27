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


def test_hero_check_rows_match_the_live_gate_check_ids():
    """The landing hero renders one row per check. If a row's data-check does not
    match a Gate check_id, that row sits on WAITING forever for every visitor —
    which is exactly what happened with disciplinary_status vs board_status."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    html = (root / "before" / "site" / "index.html").read_text(encoding="utf-8")
    rows = set(re.findall(r'data-check="([a-z_]+)"', html))
    gate = (root / "shared" / "gate" / "evaluator.py").read_text(encoding="utf-8")
    known = set(re.findall(r'check_id="([a-z_]+)"', gate)) | set(
        re.findall(r'"check_id":\s*"([a-z_]+)"', gate)
    )
    if not known:  # evaluator names them differently; fall back to the committed decision
        import json
        decision = json.loads((root / "before" / "site" / "data" / "demo-decision.json").read_text(encoding="utf-8"))
        known = {f["check_id"] for f in decision["findings"]}
    assert rows, "no check rows found on the landing page"
    assert rows <= known, f"landing rows not produced by the Gate: {sorted(rows - known)}"
