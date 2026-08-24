from __future__ import annotations

from pathlib import Path

from before.app import sponsor_clients
from before.app.cache import OperationCache


def test_serpapi_echoed_credentials_are_redacted_before_cache(monkeypatch, tmp_path: Path) -> None:
    secret = "synthetic-secret-that-must-not-reach-cache"
    monkeypatch.setattr(
        sponsor_clients,
        "_serpapi_search_live",
        lambda query, num: {
            "search_parameters": {"q": query, "api_key": secret},
            "search_metadata": {
                "google_url": f"https://example.invalid/search?q=synthetic&api_key={secret}&num={num}"
            },
            "organic_results": [],
        },
    )
    cache_root = tmp_path / "cache"
    result = sponsor_clients.serpapi_search(
        "synthetic query",
        offline=False,
        cache=OperationCache(cache_root),
    )

    assert "api_key" not in result["search_parameters"]
    assert "api_key=[REDACTED]" in result["search_metadata"]["google_url"]
    for path in cache_root.rglob("*"):
        if path.is_file():
            assert secret.encode("utf-8") not in path.read_bytes()
