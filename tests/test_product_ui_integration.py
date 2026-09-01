from __future__ import annotations

import hashlib
import json
from pathlib import Path

from before.app.integrations import seed_all_caches
from before.app.service import BeforeService


ROOT = Path(__file__).resolve().parents[1]


def test_perfectcorp_face_provenance_is_digest_bound_and_ui_assets_exist() -> None:
    manifest = json.loads(
        (ROOT / "fixtures" / "faces" / "synthetic-patient-02.provenance.json").read_text(encoding="utf-8")
    )
    assert manifest["synthetic"] is True
    assert manifest["contains_real_people"] is False
    for key in ("source", "analysis_input"):
        asset = ROOT / manifest[key]["file"]
        assert asset.exists()
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == manifest[key]["sha256"]
    assert (ROOT / "before" / "site" / "assets" / "perfectcorp" / "synthetic-patient-02-analysis-input.jpg").exists()
    assert (ROOT / "before" / "site" / "assets" / "perfectcorp" / "synthetic-patient-02-wrinkle-overlay.png").exists()


def test_complete_ui_contract_exposes_baseline_and_dns_proof() -> None:
    """The hosted pages must only call endpoints that exist on Xano, label every
    step LIVE or CACHED, and surface the sponsor proofs."""
    console = (ROOT / "before" / "site" / "console-v2.js").read_text(encoding="utf-8")
    receipt = (ROOT / "before" / "site" / "receipt-v2.js").read_text(encoding="utf-8")
    # live Gate on a per-visitor encounter; never the local-only /v1/demo/run
    assert "/encounters/demo/evaluate" in console
    assert "/v1/demo/run" not in console
    assert "/v1/receipts/verify" not in receipt
    # honesty labels on every step
    assert "LIVE · Xano" in console and "CACHED" in console
    # sponsor proofs
    assert "perfect-proof" in console and "result.image_ref" in console and "mask_refs" in console
    assert "dns.matches" in console
    assert "foxit-proof" in console and "folderId" in console
    # break it yourself: real remediate + evaluate, plus reset
    assert "/remediate" in console and "/evaluate" in console
    assert "const ATTACKS" in console and "attack-reset" in console
    # audit log from the live GET
    assert "audit_events" in console
    # patient receipt: static committed artifact, bounded language, verification limits
    assert "/data/receipt.json" in receipt
    assert "TXT READ-BACK MATCHED" in receipt
    assert "caveat" in receipt
    assert "/artifacts/time-out-safety-record.pdf" in receipt
    assert "What this proves" in receipt


def test_offline_hero_receipt_is_repeatable_and_txt_matches_actual_hash() -> None:
    seed_all_caches()
    first = BeforeService(offline=True).run_hero_path()
    second = BeforeService(offline=True).run_hero_path()
    first_receipt = first["timeline"][-1]["result"]
    second_receipt = second["timeline"][-1]["result"]
    baseline = next(item["result"] for item in first["timeline"] if item["step"] == "baseline")

    assert first_receipt["receipt_hash"] == second_receipt["receipt_hash"]
    assert first_receipt["receipt_hash"] in first_receipt["dns_verification"]["txt_value"]
    assert first_receipt["dns_verification"]["matches"] is True
    assert baseline["mode"] == "SD"
    assert baseline["vto_used"] is False
    assert baseline["image_ref"].startswith("/assets/perfectcorp/")
    assert baseline["overlay_ref"].startswith("/assets/perfectcorp/")


def test_every_proof_block_spans_the_timeline_row() -> None:
    """A proof block is a child of .timeline-item, whose first track is 40px wide.

    Any block that does not claim `grid-column` lands in that track and renders 40px
    wide with its text wrapped one word per line. Three of them did at once, which
    looked like a rendering glitch rather than a missing selector.

    Only blocks rendered directly inside a timeline row are checked. `.tamper-proof`
    sits inside `.foxit-proof` and `.attestation-proof` lives on the receipt page,
    which is not a grid — neither needs a column.
    """
    import re
    from pathlib import Path
    css = (Path(__file__).resolve().parents[1] / "before" / "site"
           / "integration-proof.css").read_text(encoding="utf-8")
    # Strip comments first: a comment above a rule otherwise gets absorbed into the
    # selector text and silently swallows the class that follows it.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    spanning: set[str] = set()
    for selector, block in re.findall(r"([^{}]+)\{([^}]*)\}", css, re.S):
        if "grid-column" not in block:
            continue
        spanning |= {c.strip().lstrip(".") for c in selector.split(",")
                     if c.strip().startswith(".")}

    timeline_level = {"perfect-proof", "nutrient-proof", "foxit-proof", "dns-receipt-proof"}
    missing = sorted(timeline_level - spanning)
    assert not missing, f"proof blocks with no grid-column will collapse to 40px: {missing}"
