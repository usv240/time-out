"""Run the three committed synthetic Gate scenarios without external services."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from shared.gate import Confidence, EncounterEvidence, ProviderEvidence, evaluate_gate


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def _provider(row: dict) -> ProviderEvidence:
    keep = {key: value for key, value in row.items() if key != "display_name" and key != "license_number"}
    keep["license_expires_on"] = date.fromisoformat(keep["license_expires_on"])
    keep["license_confidence"] = Confidence(keep["license_confidence"])
    return ProviderEvidence(**keep)


def _encounter(row: dict) -> EncounterEvidence:
    keep = {key: value for key, value in row.items() if key not in {"fixture_id", "provider_id"}}
    keep["scheduled_on"] = date.fromisoformat(keep["scheduled_on"])
    keep["product_lot_confidence"] = Confidence(keep["product_lot_confidence"])
    keep["comprehension_confidence"] = Confidence(keep["comprehension_confidence"])
    return EncounterEvidence(**keep)


def main() -> None:
    providers = {row["provider_id"]: _provider(row) for row in _load("providers.json")}
    rule = _load("rules/tx-neurotoxin.json")
    output = []
    for row in _load("encounters.json"):
        decision = evaluate_gate(providers[row["provider_id"]], _encounter(row), rule)
        output.append(
            {
                "fixture_id": row["fixture_id"],
                "encounter_id": decision.encounter_id,
                "verdict": decision.verdict.value,
                "determination_scope": decision.determination_scope,
                "rule_snapshot_sha256": decision.rule_snapshot_sha256,
                "findings": [
                    {**asdict(finding), "status": finding.status.value}
                    for finding in decision.findings
                ],
            }
        )
    print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
