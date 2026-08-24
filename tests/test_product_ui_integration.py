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
    console = (ROOT / "before" / "site" / "console-v2.js").read_text(encoding="utf-8")
    receipt = (ROOT / "before" / "site" / "receipt-v2.js").read_text(encoding="utf-8")
    assert "/v1/demo/run" in console
    assert "perfect-proof" in console
    assert "result.image_ref" in console
    assert "result.overlay_ref" in console
    assert "dns.matches" in console
    assert "NAME.COM TXT MATCHED" in receipt
    assert "Boolean(verification.verified)" in receipt
    assert "dns.caveat" in receipt


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
