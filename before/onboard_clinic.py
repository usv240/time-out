"""Provision a clinic's own verification domain: search → availability → register → DNS.

Why this exists
---------------
Every receipt used to publish under one domain we control, which leaves the patient
trusting *us* — the exact thing the receipt is supposed to remove. Onboarding a clinic
now provisions a domain that belongs to the clinic, and that clinic's receipts publish
underneath it. The patient verifies against their own clinic's domain.

Four name.com surfaces, each doing work the product depends on:

  search            find a domain that reads as the clinic's own
  checkAvailability confirm it is purchasable before anyone is quoted a price
  register          provision it (sandbox)
  DNS records       publish and read back the receipt digest

Registration is irreversible, so it never runs from a page a visitor can click.

    python -m before.onboard_clinic --clinic "Cedar Park Aesthetics"   # dry run
    python -m before.onboard_clinic --clinic "Cedar Park Aesthetics" --register
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".cache" / "namecom" / "clinic-onboarding.json"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def onboard(clinic: str, register: bool = False) -> dict[str, Any]:
    from before.app import live

    steps: list[dict[str, Any]] = []

    search = live._namecom_search_live(_slug(clinic).replace("-", ""))
    results = search.get("results", [])
    steps.append({
        "step": "search",
        "endpoint": "POST /core/v1/domains:search",
        "why": "Find a domain that reads as the clinic's own, not ours.",
        "returned": len(results),
        "top": [r.get("domainName") for r in results[:5]],
    })

    purchasable = [r for r in results if r.get("purchasable")]
    if not purchasable:
        steps.append({"step": "availability", "note": "nothing purchasable returned"})
        return {"clinic": clinic, "steps": steps, "provisioned": None}

    candidates = [r["domainName"] for r in purchasable[:3]]
    avail = live._namecom_check_availability_live(candidates)
    avail_results = avail.get("results", [])
    steps.append({
        "step": "availability",
        "endpoint": "POST /core/v1/domains:checkAvailability",
        "why": "Search suggests; availability is what we are willing to promise.",
        "checked": candidates,
        "purchasable": [r.get("domainName") for r in avail_results if r.get("purchasable")],
        "price_usd": next((r.get("purchasePrice") for r in avail_results if r.get("purchasable")), None),
    })

    chosen = next((r["domainName"] for r in avail_results if r.get("purchasable")), None)
    provisioned = None

    if chosen and register:
        reg = live._namecom_register_live(chosen)
        provisioned = chosen
        steps.append({
            "step": "register",
            "endpoint": "POST /core/v1/domains",
            "why": "The clinic owns the domain its patients verify against.",
            "domain": chosen,
            "expires": (reg.get("domain") or {}).get("expireDate"),
        })
    else:
        steps.append({
            "step": "register",
            "endpoint": "POST /core/v1/domains",
            "why": "The clinic owns the domain its patients verify against.",
            "would_register": chosen,
            "skipped": "Registration is irreversible; pass --register to perform it.",
        })

    steps.append({
        "step": "publish",
        "endpoint": "POST/PUT /core/v1/domains/{domain}/records",
        "why": "Each sealed receipt's SHA-256 becomes a TXT record under that domain, "
               "then is read back through the API to confirm it landed.",
        "already_live": True,
    })

    record = {
        "clinic": clinic,
        "surfaces_used": ["search", "checkAvailability", "register", "DNS records"],
        "steps": steps,
        "provisioned": provisioned,
        "boundary": (
            "Sandbox registrations do not resolve publicly and a TXT record stays mutable "
            "by whoever owns the domain. Giving the clinic the domain removes us from the "
            "trust path; it does not make the record a notarised one."
        ),
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clinic", required=True, help="synthetic clinic name")
    ap.add_argument("--register", action="store_true", help="actually register (irreversible)")
    args = ap.parse_args()

    result = onboard(args.clinic, register=args.register)
    for s in result["steps"]:
        head = f"{s['step']:13} {s.get('endpoint', '')}"
        print(head)
        for k, v in s.items():
            if k in ("step", "endpoint"):
                continue
            print(f"    {k}: {v}")
    print(f"\nprovisioned: {result['provisioned'] or '(dry run)'}")
    print(f"evidence:    {EVIDENCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
