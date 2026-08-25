from __future__ import annotations

from pathlib import Path

from before.app.cache import OperationCache
from before.app import sponsor_clients


def test_serpapi_public_client_caches_then_replays(monkeypatch, tmp_path: Path) -> None:
    calls = 0

    def raw(query: str, num: int) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"search_parameters": {"q": query}, "organic_results": [{"title": "Synthetic result"}]}

    monkeypatch.setattr(sponsor_clients, "_serpapi_search_live", raw)
    cache = OperationCache(tmp_path)
    live = sponsor_clients.serpapi_search("synthetic query", 3, offline=False, cache=cache)
    replay = sponsor_clients.serpapi_search("synthetic query", 3, offline=True, cache=cache)
    assert live == replay
    assert calls == 1


def test_binary_nutrient_build_uses_same_exact_cache(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sponsor_clients, "_nutrient_build_pdf_live", lambda html, filename: b"%PDF-synthetic")
    cache = OperationCache(tmp_path)
    assert sponsor_clients.nutrient_build_pdf("<h1>Synthetic</h1>", offline=False, cache=cache) == b"%PDF-synthetic"
    monkeypatch.setattr(sponsor_clients, "_nutrient_build_pdf_live", lambda html, filename: (_ for _ in ()).throw(AssertionError("network")))
    assert sponsor_clients.nutrient_build_pdf("<h1>Synthetic</h1>", offline=True, cache=cache) == b"%PDF-synthetic"


def test_raw_http_transport_functions_are_private() -> None:
    source = (Path(sponsor_clients.__file__).with_name("live.py")).read_text(encoding="utf-8")
    for operation in (
        "nutrient_parse",
        "nutrient_build_pdf",
        "serpapi_search",
        "namecom_publish_receipt",
        "namecom_read_receipt",
        "perfectcorp_upload",
        "perfectcorp_skin_analysis",
        "perfectcorp_result_bundle",
        "doctavian_upload_template",
        "doctavian_upload_data",
        "doctavian_generate",
        "doctavian_create_envelope",
        "doctavian_send_envelope",
        "foxit_upload",
    ):
        assert f"def _{operation}_live(" in source
        assert f"def {operation}(" not in source


def test_product_code_does_not_import_raw_live_transports() -> None:
    app_root = Path(sponsor_clients.__file__).parent
    offenders = []
    for source_path in app_root.glob("*.py"):
        if source_path.name in {"live.py", "sponsor_clients.py"}:
            continue
        if "from .live import" in source_path.read_text(encoding="utf-8"):
            offenders.append(source_path.name)
    assert offenders == []
