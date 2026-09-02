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

    # The README said 87 in three places and 94 in a fourth, all on the same page.
    # A judge who spots two different numbers stops believing the rest of them.
    readme = (root / "README.md").read_text(encoding="utf-8")
    stated = {int(n) for n in re.findall(r"(\d+) (?:checks, offline|offline checks)", readme)}
    assert stated == {actual}, f"README claims {sorted(stated)} offline checks; {actual} exist"


def test_every_artifact_can_be_viewed_without_downloading() -> None:
    """A download-only link is a dead end for most people.

    The artifacts were `download` links, so clicking one saved a JSON file that a judge
    then had to open somewhere else. Each now offers a View button that renders it on
    the page, with Download kept beside it.
    """
    import re
    html = (ROOT / "before" / "site" / "try.html").read_text(encoding="utf-8")
    viewable = set(re.findall(r'class="data-view"[^>]*data-src="/artifacts/([^"]+)"', html))
    linked = set(re.findall(r'href="/artifacts/(sample-[^"]+|[a-z-]+\.pdf)"', html))
    linked -= {"time-out-demo-data.zip"}
    missing = sorted(f for f in linked if f not in viewable and not f.endswith(".zip"))
    assert not missing, f"artifacts that can only be downloaded, never viewed: {missing}"
    assert len(viewable) >= 9, f"expected every artifact viewable, found {len(viewable)}"


def test_no_em_dashes_in_anything_we_ship() -> None:
    """Em dashes were removed from the site copy deliberately; keep them out."""
    site = ROOT / "before" / "site"
    offenders = []
    for path in list(site.glob("*.html")) + list(site.glob("*.js")) + list(site.glob("*.css")):
        text = path.read_text(encoding="utf-8")
        if "\u2014" in text or "&mdash;" in text:
            offenders.append(path.name)
    assert not offenders, f"em dashes are back in: {sorted(offenders)}"


def test_the_jargon_a_non_expert_meets_is_defined_somewhere() -> None:
    """Someone with no clinical or legal background has to be able to follow this.

    BLS appeared twelve times across the site and was never once expanded. The glossary
    marks the first occurrence of each term on each page; this asserts the terms that
    actually appear in the copy have a definition to attach.
    """
    import re
    site = ROOT / "before" / "site"
    glossary = (site / "glossary.js").read_text(encoding="utf-8")
    defined = {t.lower() for t in re.findall(r'^\s*"([^"]+)":', glossary, re.M)}

    prose = " ".join(p.read_text(encoding="utf-8") for p in site.glob("*.html"))
    prose = re.sub(r"<script.*?</script>", " ", prose, flags=re.S)

    must_define = ["BLS", "teach-back", "delegation", "attestation",
                   "neurotoxin", "aesthetician", "Medical Director"]
    missing = [t for t in must_define
               if re.search(rf"\b{re.escape(t)}\b", prose, re.I) and t.lower() not in defined]
    assert not missing, f"terms used in the copy with no plain-English definition: {missing}"


def test_every_page_loads_the_glossary() -> None:
    """A definition that only exists on one page is not much use on the others."""
    site = ROOT / "before" / "site"
    missing = [p.name for p in sorted(site.glob("*.html"))
               if "glossary.js" not in p.read_text(encoding="utf-8")]
    assert not missing, f"pages with no glossary: {missing}"


def test_every_nav_destination_explains_itself() -> None:
    """A nav that names seven pages and explains none of them is a guessing game.

    "Assumptions" and "Evidence" are indistinguishable to someone who has not already
    read the argument, and "Receipt" reads like billing.
    """
    import re
    site = ROOT / "before" / "site"
    guide = (site / "nav-guide.js").read_text(encoding="utf-8")
    described = set(re.findall(r'^\s*"(/[^"]*)":\s*\{', guide, re.M))

    linked = set()
    for page in site.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        nav = re.search(r'<div class="nav-links"[^>]*>(.*?)</div>', html, re.S)
        if nav:
            # anchors on the home page are sections, not destinations
            linked |= {h for h in re.findall(r'href="([^"]+)"', nav.group(1)) if "#" not in h}

    missing = sorted(linked - described)
    assert not missing, f"nav links with no what/why: {missing}"


def test_no_page_dead_ends() -> None:
    """Every page routes onward to two others, so a reader never has to use Back."""
    import re
    guide = (ROOT / "before" / "site" / "nav-guide.js").read_text(encoding="utf-8")
    pages = set(re.findall(r'^\s*"(/[^"]*)":\s*\{', guide, re.M))
    nxt = dict(re.findall(r'^\s*"(/[^"]*)":\s*\[([^\]]*)\]', guide, re.M))

    assert set(nxt) == pages, f"pages with no onward route: {sorted(pages - set(nxt))}"
    for src, targets in nxt.items():
        dests = re.findall(r'"([^"]+)"', targets)
        assert len(dests) == 2, f"{src} offers {len(dests)} next steps, expected 2"
        assert src not in dests, f"{src} points at itself"
        assert all(d in pages for d in dests), f"{src} points somewhere undescribed: {dests}"


def test_every_page_loads_the_nav_guide() -> None:
    site = ROOT / "before" / "site"
    missing = [p.name for p in sorted(site.glob("*.html"))
               if "nav-guide.js" not in p.read_text(encoding="utf-8")]
    assert not missing, f"pages with an unexplained nav: {missing}"


def _section_key(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in (("&rsquo;", "'"), ("\u2019", "'"), ("&amp;", "&"),
                         ("&mdash;", "\u2014"), ("&nbsp;", " ")):
        text = text.replace(entity, char)
    # Mirrors key() in section-guide.js: an allow-list, because hyphens and
    # apostrophes are part of words here ("fastest-growing", "don't").
    text = re.sub(r"[^a-z0-9'\- ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()[:54]


def test_every_section_says_what_it_is_and_why() -> None:
    """A heading alone does not tell a non-expert why a section exists.

    "Could this be a company" and "In the open" are meaningful only to someone who has
    already read the argument. Keys are heading text, so a reworded heading fails here
    instead of quietly losing its explanation.
    """
    import re
    site = ROOT / "before" / "site"
    guide = (site / "section-guide.js").read_text(encoding="utf-8")
    described = set(re.findall(r'^\s*"([^"]+)":\s*\[', guide, re.M))

    missing = []
    for page in sorted(site.glob("*.html")):
        html = re.sub(r"<script.*?</script>", " ",
                      page.read_text(encoding="utf-8"), flags=re.S)
        for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.S):
            key = _section_key(m.group(1))
            if key and key not in described:
                missing.append(f"{page.name}: {key!r}")
    assert not missing, f"sections with no what/why: {missing}"


def test_section_explanations_are_bound_exactly_once() -> None:
    """Two handlers on one button toggle twice per click and cancel out.

    app.js, console-v2.js and receipt-v2.js each already delegate .info-btn from the
    document, so section-guide.js must stand down on the pages that load them.
    """
    site = ROOT / "before" / "site"
    owns = ("app.js", "console-v2.js", "receipt-v2.js")
    for page in sorted(site.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        assert "section-guide.js" in html, f"{page.name} has unexplained sections"
        loaded = [s for s in owns if f'src="/{s}' in html]
        assert len(loaded) <= 1, f"{page.name} binds .info-btn {len(loaded)} times: {loaded}"


def test_the_hero_rail_cannot_float_over_the_verdict() -> None:
    """The stats rail and the verdict card are siblings inside .hero.

    A sticky rail's containing block is therefore the whole section, so past roughly
    500px of scroll it detached and printed "13,000" straight through the PASS/FAIL
    column of the result card.
    """
    css = (ROOT / "before" / "site" / "product.css").read_text(encoding="utf-8")
    rule = [line for line in css.splitlines()
            if ".hero-stats{" in line.replace(" ", "") and "grid-column" in line]
    assert rule, "the .hero-stats grid rule moved; re-check this"
    assert "sticky" not in rule[0], f"the hero rail is sticky again: {rule[0].strip()}"


def test_every_page_has_a_title_tag() -> None:
    """The em dash pass rewrote "<title>A - B</title>" to "A · B" and took the tags
    with the dash. All seven pages then had no title at all: the browser treats stray
    text in <head> as the start of <body>, so it rendered as copy in the top-left
    corner, and every tab, bookmark and link preview showed the bare URL instead.
    """
    import re
    for page in sorted((ROOT / "before" / "site").glob("*.html")):
        html = page.read_text(encoding="utf-8")
        head = html[: html.find("</head>")]
        titles = re.findall(r"<title>(.*?)</title>", head, re.S)
        assert len(titles) == 1, f"{page.name} has {len(titles)} titles in <head>"
        assert titles[0].strip(), f"{page.name} has an empty title"

        # Nothing else may sit loose in <head>: that is what put text on the page.
        inert = re.sub(r"<script.*?</script>|<style.*?</style>|<title>.*?</title>",
                       " ", head, flags=re.S)
        stray = [t.strip() for t in re.split(r"<[^>]+>", inert) if t.strip()]
        assert not stray, f"{page.name} has bare text in <head>, it will render: {stray}"


def test_light_is_the_default_theme() -> None:
    """A judge on a dark-mode laptop was shown the dark site before seeing the light one.

    Light is now the default: an absent stored preference means light, not "follow the
    OS". "system" is still reachable from the toggle, but it has to be stored
    explicitly, because removing the key no longer means what it used to.
    """
    import re
    site = ROOT / "before" / "site"

    for page in sorted(site.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        boot = re.search(r'localStorage\.getItem\("before-theme"\)([^<]{0,120})', html)
        assert boot, f"{page.name} has no theme boot script"
        assert '|| "light"' in boot.group(0) or '||"light"' in boot.group(0), (
            f"{page.name} does not default to light: {boot.group(0)[:90]}")

    for name in ("app.js", "shell.js"):
        js = (site / name).read_text(encoding="utf-8")
        assert 'localStorage.getItem("before-theme") || "light"' in js, (
            f"{name} still falls back to a theme other than light")
        assert 'localStorage.removeItem("before-theme")' not in js, (
            f"{name} removes the stored theme; an absent key now means light, so "
            f'choosing "system" would silently become light')
