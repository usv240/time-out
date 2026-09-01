from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from pathlib import Path

from before.gate_demo import _encounter, _load, _provider
from shared.gate import evaluate_gate


ROOT = Path(__file__).resolve().parents[1]


class SiteFixtureTests(unittest.TestCase):
    def test_seeded_site_decision_matches_the_real_gate(self):
        providers = {row["provider_id"]: _provider(row) for row in _load("providers.json")}
        encounter_row = next(row for row in _load("encounters.json") if row["fixture_id"] == "aesthetician-blocked")
        decision = evaluate_gate(
            providers[encounter_row["provider_id"]],
            _encounter(encounter_row),
            _load("rules/tx-neurotoxin.json"),
        )
        site_decision = json.loads((ROOT / "before" / "site" / "data" / "demo-decision.json").read_text(encoding="utf-8"))
        expected_findings = json.loads(
            json.dumps([{**asdict(finding), "status": finding.status.value} for finding in decision.findings])
        )
        self.assertEqual(decision.encounter_id, site_decision["encounter_id"])
        self.assertEqual(decision.verdict.value, site_decision["verdict"])
        self.assertEqual(decision.determination_scope, site_decision["determination_scope"])
        self.assertEqual(decision.rule_snapshot_sha256, site_decision["rule_snapshot_sha256"])
        self.assertEqual(expected_findings, site_decision["findings"])


if __name__ == "__main__":
    unittest.main()


def test_hero_check_rows_match_the_deployed_gate_contract():
    """Every check row on the landing page must correspond to a check_id the
    deployed Xano Gate actually returns. A row whose key does not match sits on
    WAITING forever for every visitor — which is what happened when the row was
    keyed disciplinary_status while Xano returns board_status."""
    import json
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    html = (root / "before" / "site" / "index.html").read_text(encoding="utf-8")
    rows = set(re.findall(r'data-check="([a-z_]+)"', html))
    contract = json.loads(
        (root / "fixtures" / "xano-gate-contract.json").read_text(encoding="utf-8")
    )
    known = set(contract["check_ids"])

    assert rows, "no check rows found on the landing page"
    assert rows <= known, f"landing rows the deployed Gate never returns: {sorted(rows - known)}"
    assert known <= rows, f"Gate checks with no row on the page: {sorted(known - rows)}"


def test_every_page_is_reachable_from_every_other_page() -> None:
    """No page may become an orphan.

    /receipt.html was reachable only through a link the console injected after a
    successful run, so a visitor who never completed a run could not find the patient
    receipt at all — and that page is where the skin baseline and the published DNS
    record are shown. /how-it-works.html was missing from the landing page for the
    same reason.
    """
    import re
    site = ROOT / "before" / "site"
    pages = {"try.html", "receipt.html", "how-it-works.html", "assumptions.html",
             "api.html", "evidence.html"}
    for page in sorted(pages | {"index.html"}):
        html = (site / page).read_text(encoding="utf-8")
        nav = re.search(r'<div class="nav-links"[^>]*>(.*?)</div>', html, re.S)
        assert nav, f"{page} has no nav-links block"
        linked = set(re.findall(r'href="/([a-z0-9-]+\.html)"', nav.group(1)))
        missing = pages - linked - {page}
        assert not missing, f"{page} nav does not link to {sorted(missing)}"


def test_every_local_asset_url_carries_a_content_version() -> None:
    """Stale CSS against fresh markup is a silent, visible break.

    Assets are served with max-age=3600. A deploy once shipped a collapsible tool
    list while returning browsers still held the previous stylesheet, so the section
    rendered as bare <details> elements with no expand affordance. Versioned URLs
    make that impossible; run `python -m before.stamp_assets` after changing CSS/JS.
    """
    import re
    site = ROOT / "before" / "site"
    unversioned = []
    for page in sorted(site.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="(\.?/[^"]+\.(?:css|js))(\?v=[0-9a-f]+)?"', html):
            if not m.group(2):
                unversioned.append(f"{page.name}: {m.group(1)}")
    assert not unversioned, (
        "unversioned asset URLs (run python -m before.stamp_assets): " + ", ".join(unversioned))


def test_asset_versions_match_the_files_they_point_at() -> None:
    """A stale stamp is worse than none — it pins visitors to old bytes."""
    import re
    from before.stamp_assets import digest        # one hash function, not two
    site = ROOT / "before" / "site"
    stale = []
    for page in sorted(site.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        for path, ver in re.findall(r'(?:href|src)="(\.?/[^"?]+\.(?:css|js))\?v=([0-9a-f]+)"', html):
            asset = site / path.lstrip("./").lstrip("/")
            if not asset.is_file():
                continue
            actual = digest(asset)
            if actual != ver:
                stale.append(f"{page.name}: {path} stamped {ver}, file is {actual}")
    assert not stale, ("stale asset stamps (run python -m before.stamp_assets): " + ", ".join(stale))


def test_assumptions_page_only_cites_tests_that_exist() -> None:
    """The page's whole argument is that every claim is pinned by a named test.

    If one is renamed or deleted the page quietly becomes a lie, which is worse than
    not having made the claim.
    """
    import re
    root = ROOT
    html = (root / "before" / "site" / "assumptions.html").read_text(encoding="utf-8")
    cited = set(re.findall(r"<code>(test_[a-z0-9_]+)</code>", html))
    assert cited, "the assumptions page cites no tests"
    defined = set()
    for path in (root / "tests").glob("*.py"):
        defined |= set(re.findall(r"def (test_[a-z0-9_]+)", path.read_text(encoding="utf-8")))
    missing = sorted(cited - defined)
    assert not missing, f"assumptions.html cites tests that do not exist: {missing}"


def test_claimed_test_counts_match_reality() -> None:
    """The assumptions page argues that every claim is pinned by a test.

    A stale count on that page undermines the argument it is making, and it drifts
    every time a test is added — which is often.
    """
    import re
    root = ROOT
    actual = len(re.findall(
        r"def (test_[a-z0-9_]+)",
        "\n".join(p.read_text(encoding="utf-8") for p in (root / "tests").glob("test_*.py"))))

    page = (root / "before" / "site" / "assumptions.html").read_text(encoding="utf-8")
    claimed = {int(n) for n in re.findall(r"(\d+) tests", page)}
    assert claimed, "the assumptions page states no test count"
    assert claimed == {actual}, (
        f"assumptions.html claims {sorted(claimed)} tests; {actual} are defined")
