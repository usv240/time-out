"""One-command offline verification of the complete synthetic hero path."""

from __future__ import annotations

import json

from before.app.integrations import seed_all_caches
from before.app.service import BeforeService


def main() -> None:
    seed_all_caches()
    service = BeforeService(offline=True)
    result = service.run_hero_path()
    receipt = result["timeline"][-1]["result"]
    verification = service.verify_receipt(receipt["receipt_hash"])
    output = {
        "offline": True,
        "final_state": result["encounter"]["state"],
        "timeline_steps": [item["step"] for item in result["timeline"]],
        "audit_events": len(result["encounter"]["audit_events"]),
        "receipt_id": receipt["receipt_id"],
        "receipt_verified": verification["verified"],
    }
    print(json.dumps(output, indent=2))
    if output["final_state"] != "SEALED" or not output["receipt_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
