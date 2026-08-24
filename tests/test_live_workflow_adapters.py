from __future__ import annotations

import hashlib
import json
from pathlib import Path

from before.app import sponsor_clients
from before.app.cache import OperationCache
from before.app.integrations import NutrientClient, SerpApiClient

def _write_synthetic_pdf(path: Path) -> None:
    payload = b"%PDF-1.4 synthetic"
    path.write_bytes(payload)
    path.with_name(path.name + ".synthetic.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "synthetic": True,
                "contains_real_people_or_businesses": False,
                "contains_prohibited_identifiers": False,
                "artifact_sha256": hashlib.sha256(payload).hexdigest(),
            }
        ),
        encoding="utf-8",
    )


def _nutrient_payload() -> dict[str, object]:
    return {
        "output": {
            "elements": [
                {"text": "MANUFACTURER: Fictional Therapeutics", "confidence": 0.98, "bounds": [10, 20, 30, 40]},
                {"text": "PRODUCT: EXAMPLETOX - NOT A REAL PRODUCT", "confidence": 0.97, "bounds": [10, 50, 30, 40]},
                {"text": "LOT: INVENTED-LOT-0007", "confidence": 0.61, "bounds": [10, 80, 30, 40]},
                {"text": "EXPIRES: 2027-10-31", "confidence": 0.91, "bounds": [10, 110, 30, 40]},
            ]
        },
        "metrics": {"pagesProcessed": 1},
    }


def test_nutrient_live_response_maps_to_typed_review_and_exact_offline_replay(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "synthetic-product.pdf"
    _write_synthetic_pdf(source)
    calls = 0

    def raw(document: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        assert document == source
        return _nutrient_payload()

    monkeypatch.setattr(sponsor_clients, "_nutrient_parse_live", raw)
    cache = OperationCache(tmp_path / "cache")
    live = NutrientClient(False, cache, source).run()
    monkeypatch.setattr(
        sponsor_clients,
        "_nutrient_parse_live",
        lambda document: (_ for _ in ()).throw(AssertionError("offline replay attempted network")),
    )
    replay = NutrientClient(True, cache, source).run()

    assert live == replay
    assert calls == 1
    assert live.fields["lot"] == "INVENTED-LOT-0007"
    assert live.confidence["lot"] == "LOW"
    assert live.review_required is True
    assert live.assigned_role == "Medical Director"
    assert live.page_coordinates["lot"] == [10.0, 80.0, 30.0, 40.0]


def test_serpapi_live_results_remain_candidates_and_exactly_replay_offline(
    monkeypatch, tmp_path: Path
) -> None:
    calls: list[str] = []

    def raw(query: str, num: int) -> dict[str, object]:
        calls.append(query)
        return {
            "organic_results": [
                {
                    "title": "Synthetic-scope source for human review",
                    "link": "https://example.invalid/source/" + str(len(calls)),
                    "snippet": "Public guidance; no conclusion about a real clinic.",
                }
            ]
        }

    monkeypatch.setattr(sponsor_clients, "_serpapi_search_live", raw)
    cache = OperationCache(tmp_path / "cache")
    live = SerpApiClient(False, cache).run()
    monkeypatch.setattr(
        sponsor_clients,
        "_serpapi_search_live",
        lambda query, num: (_ for _ in ()).throw(AssertionError("offline replay attempted network")),
    )
    replay = SerpApiClient(True, cache).run()

    assert live == replay
    assert calls == SerpApiClient.queries
    assert live.status == "CANDIDATE"
    assert live.candidate_id.startswith("SYN-ALERT-")
    assert "human" in live.boundary.lower()
    assert "SYNTHETIC" in live.matched_entity
