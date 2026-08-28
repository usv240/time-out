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
        check("WAITING" not in text, "no check left WAITING")

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

        reset = page.locator("button", has_text="Reset").first
        await reset.scroll_into_view_if_needed()
        await reset.click()
        await page.wait_for_timeout(10000)
        rt = await page.evaluate("() => document.querySelector('#attack-result').innerText")
        check("CLEAR" in rt, "Reset returns CLEAR")

        # ---- receipt: the signed attestation and both sponsors' proof ----------
        print("\n/receipt.html")
        await page.goto(base + "/receipt.html", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(6000)
        rec = await page.evaluate("() => document.body.innerText")
        check("SIGNED BY A NAMED HUMAN" in rec, "attestation shows a human signature")
        check("TXT READ-BACK MATCHED" in rec, "name.com DNS read-back matched")
        check("YOUR BASELINE" in rec, "Perfect Corp baseline present")
        check("What this proves" in rec, "limits stated on the receipt")
        broken = await page.evaluate(
            "() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length")
        check(broken == 0, f"no broken images on the receipt ({broken} broken)")

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

        # ---- every page reachable, no sideways scroll, no JS errors ------------
        print("\nwhole site")
        pages = ["/", "/try.html", "/receipt.html", "/how-it-works.html", "/evidence.html", "/api.html"]
        for w, name in ((390, "phone"), (1440, "desktop")):
            await page.set_viewport_size({"width": w, "height": 900})
            worst = 0
            for p in pages:
                await page.goto(base + p, wait_until="networkidle", timeout=90000)
                await page.wait_for_timeout(2500)
                worst = max(worst, await page.evaluate(
                    "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"))
            check(worst <= 2, f"no horizontal scroll at {w}px ({name}), worst {worst}px")

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
