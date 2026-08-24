from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from before.app import sponsor_clients
from before.app.cache import OperationCache
from before.app.integrations import IntegrationError, NameComClient, PerfectCorpClient


def _perfectcorp_bundle() -> bytes:
    payload = {
        "wrinkle": {"ui_score": 23},
        "texture": {"ui_score": 31},
        "redness": {"ui_score": 17},
        "all": {"score": 76.5},
        "skin_age": 39,
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("skinanalysisResult/score_info.json", json.dumps(payload))
        archive.writestr("skinanalysisResult/wrinkle_output.png", b"synthetic-mask")
    return output.getvalue()


def test_perfectcorp_caches_raw_bundle_redacts_signed_url_and_replays(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "synthetic-face.jpg"
    image.write_bytes(b"synthetic jpeg bytes")
    signed_secret = "signed-result-token-must-not-persist"
    calls = {"upload": 0, "task": 0, "bundle": 0}

    def upload(source: Path) -> str:
        calls["upload"] += 1
        return "SYN-FILE-001"

    def task(file_id: str, concerns: list[str], poll_seconds: int, max_polls: int) -> dict[str, object]:
        calls["task"] += 1
        return {
            "status": "success",
            "results": {"url": f"https://example.invalid/result.zip?token={signed_secret}"},
        }

    def bundle(task_data: dict[str, object]) -> bytes:
        calls["bundle"] += 1
        return _perfectcorp_bundle()

    monkeypatch.setattr(sponsor_clients, "_perfectcorp_upload_live", upload)
    monkeypatch.setattr(sponsor_clients, "_perfectcorp_skin_analysis_live", task)
    monkeypatch.setattr(sponsor_clients, "_perfectcorp_result_bundle_live", bundle)
    cache = OperationCache(tmp_path / "cache")

    file_id = sponsor_clients.perfectcorp_upload(image, offline=False, cache=cache)
    task_data = sponsor_clients.perfectcorp_skin_analysis(file_id, offline=False, cache=cache)
    live_scores = sponsor_clients.perfectcorp_scores(task_data, offline=False, cache=cache)
    monkeypatch.setattr(sponsor_clients, "_perfectcorp_upload_live", lambda source: pytest.fail("network"))
    monkeypatch.setattr(sponsor_clients, "_perfectcorp_skin_analysis_live", lambda *args: pytest.fail("network"))
    monkeypatch.setattr(sponsor_clients, "_perfectcorp_result_bundle_live", lambda data: pytest.fail("network"))
    replay_file_id = sponsor_clients.perfectcorp_upload(image, offline=True, cache=cache)
    replay_task = sponsor_clients.perfectcorp_skin_analysis(replay_file_id, offline=True, cache=cache)
    replay_scores = sponsor_clients.perfectcorp_scores(replay_task, offline=True, cache=cache)

    assert calls == {"upload": 1, "task": 1, "bundle": 1}
    assert file_id == replay_file_id
    assert task_data == replay_task
    assert live_scores == replay_scores
    assert live_scores["overall"] == 76.5
    assert task_data["results"]["url"] == "[REDACTED_SIGNED_URL]"
    assert all(signed_secret.encode() not in path.read_bytes() for path in (tmp_path / "cache").rglob("*") if path.is_file())


def test_perfectcorp_adapter_refuses_unproven_face_before_transport(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "synthetic-face.jpg"
    source.write_bytes(b"unproven")
    monkeypatch.setattr(sponsor_clients, "perfectcorp_upload", lambda *args, **kwargs: pytest.fail("transport"))
    with pytest.raises(IntegrationError, match="provenance"):
        PerfectCorpClient(False, OperationCache(tmp_path / "cache"), source).run()


def test_namecom_publishes_actual_digest_then_reads_back_and_replays(monkeypatch, tmp_path: Path) -> None:
    host = "_before.syn-receipt-test"
    digest = "a" * 64
    calls = {"publish": 0, "read": 0}

    def publish(receipt_host: str, receipt_digest: str) -> dict[str, object]:
        calls["publish"] += 1
        assert (receipt_host, receipt_digest) == (host, digest)
        return {"host": host, "type": "TXT", "answer": f"before-receipt-v1 sha256={digest}"}

    def read(receipt_host: str) -> dict[str, object]:
        calls["read"] += 1
        return {
            "host": receipt_host,
            "type": "TXT",
            "answer": f"before-receipt-v1 sha256={digest}",
            "fqdn": f"{receipt_host}.beforereceipts-demo.com.",
        }

    monkeypatch.setattr(sponsor_clients, "_namecom_publish_receipt_live", publish)
    monkeypatch.setattr(sponsor_clients, "_namecom_read_receipt_live", read)
    cache = OperationCache(tmp_path / "cache")
    live = NameComClient(False, cache, host, digest).run()
    monkeypatch.setattr(sponsor_clients, "_namecom_publish_receipt_live", lambda *args: pytest.fail("network"))
    monkeypatch.setattr(sponsor_clients, "_namecom_read_receipt_live", lambda *args: pytest.fail("network"))
    replay = NameComClient(True, cache, host, digest).run()

    assert calls == {"publish": 1, "read": 1}
    assert live == replay
    assert live.published is True
    assert live.matches is True
    assert live.txt_value.endswith(digest)
    assert live.mutable is True
    assert "notary" in live.caveat.lower()
