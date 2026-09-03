"""End-to-end smoke test: drive the deployed UI against the deployed backend.

Why this exists
---------------
Sixty-seven unit tests and three offline rehearsals all passed while the two most
important attacks on /try returned HTTP 400 instead of a refusal. Nothing in the
suite clicked a real button against the real Xano backend, so a transport-layer
rejection between the browser and the Gate was invisible: the Gate was correct,
the page was correct, and the request in between never arrived.

This is the test that would have caught it. It needs the network and a deployed
target, so it is not part of the default unit run. Run it before recording the
demo, and after any deploy:

    python -m tests.smoke_live                      # against prod
    python -m tests.smoke_live --base <url>         # against a dev build

Exit code is non-zero if any check fails, so CI can gate on it.

One caveat worth knowing before you trust a red run: static assets are served with
`Cache-Control: max-age=3600`, so for a short window straight after a deploy the CDN
can still hand back the previous build. A failure that appears immediately after
promoting a build, and clears on a re-run a minute later, is that — not a regression.
Re-run before investigating.
"""
from __future__ import annotations

import argparse
import asyncio
import sys

PROD = "https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io"

# Each attack must be refused, and it must be refused for the right reason. Asserting
# only "not CLEAR" would pass even if every attack failed on an unrelated check.
EXPECTED_BLOCK = {
    "Swap in the aesthetician": {"authority_pathway", "delegation_and_supervision"},
    "Delete the delegation protocol": {"delegation_and_supervision"},
    "Skip the patient-specific order": {"delegation_and_supervision"},
    "Use the FDA-flagged lot": {"product_lot"},
    "Skip the teach-back": {"comprehension"},
    "Let BLS lapse, supervisor off-site": {"delegation_and_supervision"},
}

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


async def run(base: str) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1440, "height": 1400})
        page = await ctx.new_page()

        js_errors: list[str] = []
        page.on("pageerror", lambda e: js_errors.append(str(e)[:160]))
        page.on("response", lambda r: js_errors.append(f"HTTP {r.status} {r.url[-60:]}")
                if "xano.io/api" in r.url and r.status >= 400 else None)

        # ---- landing page runs the Gate for real -------------------------------
        print("\n/ (landing)")
        await page.goto(base + "/", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(9000)
        text = await page.evaluate("() => document.body.innerText")
        check("BLOCKED" in text, "hero reaches a verdict")
        # Read the check rows themselves rather than scanning page text: an unrelated
        # status pill reading "AWAITING SCOPE" contains the substring "WAITING".
        rows = await page.evaluate(
            "() => [...document.querySelectorAll('.check-row')].map(r => "
            "[r.dataset.check, r.querySelector('.check-status').textContent.trim()])")
        stuck = [c for c, s in rows if s == "WAITING"]
        check(len(rows) == 7, f"all seven checks rendered (found {len(rows)})")
        check(not stuck, f"every check resolved{' — stuck: ' + ', '.join(stuck) if stuck else ''}")

        # ---- /try: run, then every attack, then reset --------------------------
        print("\n/try.html")
        await page.goto(base + "/try.html", wait_until="networkidle", timeout=90000)
        await page.locator("button", has_text="Run the complete safety workflow").first.click()
        await page.wait_for_timeout(10000)

        n = await page.evaluate("() => document.querySelectorAll('.attack-btn').length")
        check(n == len(EXPECTED_BLOCK), f"all {len(EXPECTED_BLOCK)} attack buttons rendered (found {n})")

        for i in range(n):
            btn = page.locator(".attack-btn").nth(i)
            label = (await btn.inner_text()).split("\n")[0].strip()
            await btn.scroll_into_view_if_needed()
            await btn.click()
            await page.wait_for_timeout(10000)

            state = await page.evaluate("""() => {
                const r = document.querySelector('#attack-result');
                const err = document.querySelector('#console-error, .console-error');
                return { hidden: r.hidden,
                         text: r.innerText.replace(/\\s+/g, ' '),
                         error: err && !err.hidden ? err.innerText.slice(0, 120) : null }; }""")

            check(not state["hidden"] and "TIME OUT" in state["text"], f"{label} -> TIME OUT")
            check(state["error"] is None, f"{label} -> no error shown")
            expected = EXPECTED_BLOCK.get(label, set())
            hit = {c for c in expected if c in state["text"]}
            check(bool(hit), f"{label} -> cites {' or '.join(sorted(expected))}")

        reset = page.locator("#attack-reset")
        await reset.scroll_into_view_if_needed()
        await reset.click()
        await page.wait_for_timeout(10000)
        rt = await page.evaluate("() => document.querySelector('#attack-result').innerText")
        check("CLEAR" in rt, "Reset returns CLEAR")

        # A CLEAR verdict advances the encounter out of REMEDIATION, and the state
        # machine refuses further evidence edits. Attacking after a Reset used to show
        # the stale CLEAR while an error appeared elsewhere — a judge seeing a success
        # that did not happen. The client now opens a fresh encounter and retries.
        again = page.locator(".attack-btn").nth(1)
        await again.scroll_into_view_if_needed()
        await again.click()
        await page.wait_for_timeout(10000)
        after = await page.evaluate("""() => {
            const r = document.querySelector('#attack-result');
            const err = document.querySelector('#console-error, .console-error');
            return { text: r.innerText, error: err && !err.hidden ? err.innerText.slice(0, 120) : null }; }""")
        check("TIME OUT" in after["text"], "an attack still refuses after a Reset")
        check(after["error"] is None, "no error surfaces after a Reset")

        # The composer hands the whole evidence set over; it must survive the same path.
        summary = page.locator("#compose > summary")
        if await summary.count():
            await summary.scroll_into_view_if_needed()
            await summary.click()
            await page.wait_for_timeout(900)
            n_controls = await page.evaluate("() => document.querySelectorAll('#compose-grid [data-key]').length")
            check(n_controls >= 15, f"composer renders its controls ({n_controls})")
            await page.locator("#c-delegation_agreement_id").uncheck()
            run_btn = page.locator("#compose-run")
            await run_btn.scroll_into_view_if_needed()
            await run_btn.click()
            await page.wait_for_timeout(11000)
            composed = await page.evaluate("() => document.querySelector('#compose-result').innerText")
            check("TIME OUT" in composed, "composed evidence without delegation is refused")
        else:
            check(False, "composer present")

        # ---- receipt: the signed attestation and both sponsors' proof ----------
        print("\n/receipt.html")
        await page.goto(base + "/receipt.html", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(6000)
        rec = await page.evaluate("() => document.body.innerText")
        check("SIGNED BY A NAMED HUMAN" in rec, "attestation shows a human signature")
        check("TXT READ-BACK MATCHED" in rec, "name.com DNS read-back matched")
        check("YOUR BASELINE" in rec, "Perfect Corp baseline present")

        # The baseline has to be explorable, not just displayed: one overlay at a time,
        # tied to the score that produced it.
        concerns = page.locator(".concern")
        n_c = await concerns.count()
        check(n_c == 12, f"twelve scored concerns rendered (found {n_c})")
        if n_c:
            await concerns.nth(3).scroll_into_view_if_needed()
            await concerns.nth(3).click()
            await page.wait_for_timeout(800)
            st = await page.evaluate("""() => {
                const vis = [...document.querySelectorAll('.analysis-mask')].filter(m => !m.hidden);
                const sel = document.querySelector('.concern[aria-checked="true"]');
                return { visible: vis.length, sameAsSelected: vis[0]?.dataset.mask === sel?.dataset.concern,
                         caption: (document.querySelector('#mask-caption')?.textContent || '').length }; }""")
            check(st["visible"] == 1, f"exactly one overlay shown (saw {st['visible']})")
            check(st["sameAsSelected"], "the overlay matches the selected concern")
            check(st["caption"] > 10, "the overlay is captioned")
        check("What this proves" in rec, "limits stated on the receipt")
        broken = await page.evaluate(
            "() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length")
        check(broken == 0, f"no broken images on the receipt ({broken} broken)")

        # Revocation channel: the patient must be able to ask whether the receipt is
        # still good, live, against the clinic's own domain.
        btn = page.locator("#check-status")
        if await btn.count():
            await btn.scroll_into_view_if_needed()
            await btn.click()
            await page.wait_for_timeout(12000)
            out = await page.evaluate("() => document.querySelector('#status-out').innerText")
            check(any(w in out for w in ("STILL VALID", "REVOKED")), "live receipt status resolves")
            check("UNKNOWN" not in out, "status is published, not UNKNOWN")
        else:
            check(False, "receipt status button present")

        # ---- reproducibility ---------------------------------------------------
        print("\n/how-it-works.html")
        await page.goto(base + "/how-it-works.html", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(2500)
        v = page.locator("button", has_text="Fetch").first
        if not await v.count():
            v = page.locator("button", has_text="verdict").first
        if await v.count():
            await v.scroll_into_view_if_needed()
            await v.click()
            await page.wait_for_timeout(15000)
        hw = await page.evaluate("() => document.body.innerText")
        check("REPRODUCED" in hw.upper(), "browser re-hash reproduces the server fingerprint")

        # ---- the API page: a claim judges will test with their own hands -------
        print("\n/api.html")
        await page.goto(base + "/api.html", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(3000)
        for sel, label, target in (("#send-request", "Send request", "#response-output"),
                                   ("#get-key", "Instant key", "#key-output")):
            el = page.locator(sel)
            if not await el.count():
                check(False, f"{label} control present")
                continue
            await el.scroll_into_view_if_needed()
            await el.click()
            await page.wait_for_timeout(11000)
            body = await page.evaluate("t => (document.querySelector(t)?.innerText || '')", target)
            check(len(body) > 40, f"{label} returns a live response")
            if sel == "#send-request":
                check("verdict" in body, "the playground returns a real verdict")

        # ---- every page reachable, no sideways scroll, no JS errors ------------
        print("\nwhole site")
        pages = ["/", "/try.html", "/receipt.html", "/how-it-works.html", "/evidence.html", "/api.html"]
        # 768 is an iPad in portrait, and it was the one width nobody tested: the
        # nav hints went inline at 48rem while the nav only collapses at 680px, so
        # between those two the header ran 85px off the right edge. 360 is a common
        # Android width where a 20rem grid minimum could not shrink to fit.
        for w, name in ((360, "small phone"), (390, "phone"), (680, "nav collapse"),
                        (768, "tablet portrait"), (1440, "desktop")):
            await page.set_viewport_size({"width": w, "height": 900})
            worst = 0
            for p in pages:
                await page.goto(base + p, wait_until="networkidle", timeout=90000)
                await page.wait_for_timeout(2500)
                worst = max(worst, await page.evaluate(
                    "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"))
            check(worst <= 2, f"no horizontal scroll at {w}px ({name}), worst {worst}px")

        # Every section explains itself, and the hero rail stays out of the verdict.
        await page.set_viewport_size({"width": 1440, "height": 950})
        gaps = []
        for p in ["/", "/try.html", "/how-it-works.html", "/assumptions.html",
                  "/api.html", "/evidence.html"]:
            await page.goto(base + p, wait_until="networkidle", timeout=90000)
            await page.wait_for_timeout(2200)
            missing = await page.evaluate(
                """() => [...document.querySelectorAll('main h2')]
                     .filter(h => !h.closest('.next-step') && !h.querySelector('.info-btn'))
                     .map(h => h.textContent.trim().slice(0, 40))""")
            gaps += [f"{p}: {m}" for m in missing]
        check(not gaps, f"every section has a what/why button ({len(gaps)} without)")
        for g in gaps:
            print(f"        {g}")

        # The tip that explains the dotted underlines has to be where it is read.
        buried = []
        for p in ["/", "/try.html", "/receipt.html", "/how-it-works.html",
                  "/assumptions.html", "/api.html", "/evidence.html"]:
            await page.goto(base + p, wait_until="networkidle", timeout=90000)
            await page.wait_for_timeout(2200)
            y = await page.evaluate(
                """() => { const h = document.querySelector('.glossary-hint');
                     return h ? Math.round(h.getBoundingClientRect().top + scrollY) : -1; }""")
            if y < 0 or y > 950:
                buried.append(f"{p}: {'absent' if y < 0 else str(y) + 'px down'}")
        check(not buried, f"glossary tip is in the first screen on every page ({len(buried)} not)")
        for entry in buried:
            print(f"        {entry}")

        await page.goto(base + "/", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(1500)
        collided = False
        for y in (500, 900, 1400):
            await page.evaluate(f"() => scrollTo(0, {y})")
            await page.wait_for_timeout(250)
            collided = collided or await page.evaluate(
                """() => { const g = e => e.getBoundingClientRect();
                  const s = g(document.querySelector('.hero-stats'));
                  const v = g(document.querySelector('.evaluation'));
                  return !(s.right <= v.x || s.x >= v.right || s.bottom <= v.y || s.y >= v.bottom); }""")
        check(not collided, "hero stats never overlap the verdict card while scrolling")

        # Clicking "Run this request" must visibly do something where the reader is
        # looking. It answered in 0.6s all along, into a pane 884px below the fold, so
        # the page looked broken.
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(base + "/api.html", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(2000)
        await page.click("main button:has-text('Run this request')")
        await page.wait_for_function(
            "() => /verdict/.test(document.querySelector('#response-output').textContent)",
            timeout=45000)
        await page.wait_for_timeout(2200)
        seen = await page.evaluate(
            """() => { const o = document.querySelector('#response-output');
                 const h = document.querySelector('.site-header').getBoundingClientRect();
                 const b = o.getBoundingClientRect();
                 return b.top >= h.bottom - 2 && b.top < innerHeight - 100; }""")
        check(seen, "the API response lands on screen, clear of the sticky header")

        real = [e for e in dict.fromkeys(js_errors)]
        check(not real, f"no JS errors or failing API calls ({len(real)})")
        for e in real:
            print(f"        {e}")

        await browser.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=PROD, help="deployed site to test")
    args = ap.parse_args()

    print(f"Smoke test against {args.base}")
    asyncio.run(run(args.base))

    # The API is open on purpose, and a key must never quietly start gating it. These
    # ran in the offline unit suite for a while, which was wrong: that suite serves its
    # own requests from a local server and has no internet, so in CI they failed with
    # connection refused. They test the deployed API, so they live here.
    import json
    import urllib.error
    import urllib.request

    api = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1"

    def call(method, path, body=None, headers=None):
        head = {"Content-Type": "application/json"}
        head.update(headers or {})
        payload = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(api + path, data=payload, method=method, headers=head)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    status, issued = call("POST", "/keys", {"label": "smoke"})
    check(status == 200 and issued.get("key", "").startswith("tok_demo_")
          and issued.get("required") is False,
          "POST /v1/keys issues an optional tag that grants nothing")

    codes = []
    for headers in ({"X-Time-Out-Key": issued.get("key", "")},
                    {"X-Time-Out-Key": "not-a-real-key"}, None):
        codes.append(call("POST", "/encounters/demo/evaluate", {}, headers)[0])
    check(codes == [200, 200, 200],
          f"the key stays optional: real, nonsense and absent all return 200 ({codes})")

    refusals = [
        (call("GET", "/encounters/SYN-ENC-does-not-exist")[0], 404),
        (call("POST", "/encounters", {})[0], 400),
        (call("POST", "/keys", {"label": "someone@example.com"})[0], 400),
        (call("POST", "/keys", {"label": "x" * 300})[0], 400),
    ]
    check(all(got == want for got, want in refusals),
          f"the API refuses bad input the way /api documents it ({refusals})")

    # The README and the Devpost story both quote this number. A count that drifts is
    # the kind of small wrongness a judge checks first, so the suite that owns the
    # number verifies the claim instead of trusting a human to remember.
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    claimed: set[int] = set()
    for rel in ("README.md", "submission/devpost-about.md"):
        doc = root / rel
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8")
        claimed |= {int(n) for n in re.findall(r"(\d+) checks against production", text)}
        claimed |= {int(n) for n in re.findall(r"offline \+ (\d+) live-browser", text)}
        claimed |= {int(n) for n in re.findall(r"(\d+) live browser checks", text)}
    total = len(results) + 1          # this check counts itself
    check(claimed <= {total},
          f"documented live check count is right ({sorted(claimed) or 'none stated'} vs {total})")

    failed = [label for ok, label in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("\nFAILED:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print("All good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
