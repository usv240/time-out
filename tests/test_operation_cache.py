from __future__ import annotations

import json
from pathlib import Path

import pytest

from before.app.cache import CacheIntegrityError, OperationCache, OperationCacheMiss


def test_online_json_is_frozen_and_offline_never_calls_network(tmp_path: Path) -> None:
    cache = OperationCache(tmp_path)
    calls = 0

    def live() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"status": "ok", "items": [1, 2, 3]}

    descriptor = {"fixture_sha256": "a" * 64, "mode": "SD"}
    assert cache.json(vendor="Example", operation="analyze", request_descriptor=descriptor, offline=False, live_call=live)["status"] == "ok"

    def forbidden() -> dict[str, object]:
        raise AssertionError("offline replay attempted a network call")

    replay = cache.json(vendor="Example", operation="analyze", request_descriptor=descriptor, offline=True, live_call=forbidden)
    assert replay == {"items": [1, 2, 3], "status": "ok"}
    assert calls == 1


def test_binary_cache_is_integrity_checked(tmp_path: Path) -> None:
    cache = OperationCache(tmp_path)
    descriptor = {"document_sha256": "b" * 64}
    assert cache.bytes(vendor="Example", operation="pdf", request_descriptor=descriptor, offline=False, live_call=lambda: b"PDF") == b"PDF"
    payload = next(tmp_path.rglob("*.response.bin"))
    payload.write_bytes(b"tampered")
    with pytest.raises(CacheIntegrityError):
        cache.bytes(vendor="Example", operation="pdf", request_descriptor=descriptor, offline=True, live_call=lambda: b"unused")


def test_exact_request_fingerprint_is_required(tmp_path: Path) -> None:
    cache = OperationCache(tmp_path)
    cache.json(vendor="Example", operation="lookup", request_descriptor={"id": "SYN-1"}, offline=False, live_call=lambda: {"ok": True})
    with pytest.raises(OperationCacheMiss):
        cache.json(vendor="Example", operation="lookup", request_descriptor={"id": "SYN-2"}, offline=True, live_call=lambda: {"ok": False})


def test_metadata_contains_only_digests_not_request_values(tmp_path: Path) -> None:
    cache = OperationCache(tmp_path)
    secret_marker = "must-not-be-persisted"
    cache.json(
        vendor="Example",
        operation="lookup",
        request_descriptor={"synthetic_id": secret_marker},
        offline=False,
        live_call=lambda: {"ok": True},
    )
    metadata = next(tmp_path.rglob("*.metadata.json"))
    content = metadata.read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert secret_marker not in content
    assert len(parsed["request_sha256"]) == 64
    assert parsed["synthetic_only"] is True
