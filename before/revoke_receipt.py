"""Seal a receipt, then revoke it over DNS when an alert lands afterwards.

The gap this closes
-------------------
Time-Out's central claim is that ready is reversible: a confirmed FDA warning letter
or board action moves an encounter back to human review. That holds right up to the
moment a receipt is issued. After that the patient is holding a record saying the
checks passed, and nothing tells them if it later stopped being true.

Certificates solved this a long time ago — a certificate has a status separate from
its contents. A Time-Out receipt now gets the same treatment, published on the
clinic's own domain:

    _timeout.<receipt-id>.<clinic>        the receipt digest  — "is this the receipt issued?"
    _status.<receipt-id>.<clinic>         the receipt status  — "is it still good?"

Those are different questions. Conflating them is how a stale record ends up looking
authoritative.

    python -m before.revoke_receipt --show
    python -m before.revoke_receipt --seal
    python -m before.revoke_receipt --revoke "FDA warning letter 723267, lot reconciliation"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".cache" / "namecom" / "receipt-status.json"
SITE_COPY = ROOT / "before" / "site" / "data" / "receipt-status.json"
FIXTURE = ROOT / "fixtures" / "namecom" / "receipt-status.json"


def _clinic_domain() -> str:
    onboarding = json.loads(
        (ROOT / ".cache" / "namecom" / "clinic-onboarding.json").read_text(encoding="utf-8"))
    domain = onboarding.get("provisioned")
    if not domain:
        raise SystemExit("No clinic domain provisioned. Run before.onboard_clinic --register.")
    return domain


def _receipt_id() -> str:
    return json.loads(
        (ROOT / "before" / "site" / "data" / "receipt.json").read_text(encoding="utf-8")
    )["receipt_id"]


def _save(record: dict[str, Any]) -> None:
    for path in (EVIDENCE, SITE_COPY, FIXTURE):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def show() -> dict[str, Any]:
    from before.app import live
    domain, receipt = _clinic_domain(), _receipt_id()
    return {"domain": domain, "receipt_id": receipt,
            "status": live._namecom_read_status_live(domain, receipt)}


def seal() -> dict[str, Any]:
    from before.app import live
    domain, receipt = _clinic_domain(), _receipt_id()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    published = live._namecom_publish_status_live(domain, receipt, "VALID", at=now)
    state = live._namecom_read_status_live(domain, receipt)
    record = {"domain": domain, "receipt_id": receipt, "sealed_at": now,
              "operation": published.get("operation"), "status": state,
              "boundary": (
                  "A status record says whether this receipt is still current. It does not "
                  "certify that the procedure was safe, and it stays mutable by whoever owns "
                  "the domain.")}
    _save(record)
    return record


def revoke(reason: str) -> dict[str, Any]:
    from before.app import live
    domain, receipt = _clinic_domain(), _receipt_id()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    # Reason is written into a TXT answer, so keep it to one unambiguous token run.
    safe_reason = "-".join(reason.split())[:120]
    published = live._namecom_publish_status_live(domain, receipt, "REVOKED", safe_reason, now)
    state = live._namecom_read_status_live(domain, receipt)
    record = {"domain": domain, "receipt_id": receipt, "revoked_at": now,
              "reason": reason, "operation": published.get("operation"), "status": state,
              "boundary": (
                  "Revocation is a named human's decision after confirming an alert candidate. "
                  "The search result never revokes anything by itself.")}
    _save(record)
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true")
    g.add_argument("--seal", action="store_true")
    g.add_argument("--revoke", metavar="REASON")
    args = ap.parse_args()

    result = show() if args.show else seal() if args.seal else revoke(args.revoke)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
