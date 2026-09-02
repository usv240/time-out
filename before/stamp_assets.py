"""Stamp a content hash onto every local CSS/JS URL in the site HTML.

Static assets are served with `Cache-Control: max-age=3600`. Without a version in
the URL a returning visitor gets an hour-old stylesheet against new markup — which
is exactly what happened after one deploy: the page shipped a collapsible tool list
while the browser still held the CSS from the previous build, so it rendered as raw
`<details>` elements with no expand affordance at all.

A judge visiting twice would have hit that. The hash changes only when the file
changes, so this is stable across rebuilds that touch nothing.

Run before pushing a static build:

    python -m before.stamp_assets
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "before" / "site"

# href="/product.css" or href="/product.css?v=abc1234"  /  src="./app.js"
#
# Artifacts are stamped too. They are served with the same max-age=3600, and the signed
# safety record was re-issued once during the build: for an hour afterwards a returning
# visitor was handed the previous PDF, with a first page that contradicted its own
# signature page. "data-src" matches as well, which is what the artifact viewer reads.
REF = re.compile(
    r'(?P<attr>href|src)="(?P<path>\.?/[^"?]+\.(?:css|js|pdf|png|jpg|json))'
    r'(?:\?v=[0-9a-f]+)?"')


def digest(asset: Path) -> str:
    """Content hash with line endings normalised.

    Git checks these files out CRLF on Windows and LF on Linux, so hashing raw bytes
    produces a different stamp per platform: the stamps written on a dev machine then
    read as stale in CI, for files nobody had touched. Normalising means the stamp
    tracks the content and nothing else.
    """
    return hashlib.sha256(
        asset.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()[:8]


def _digest(url_path: str) -> str | None:
    asset = SITE / url_path.lstrip("./").lstrip("/")
    if not asset.is_file():
        return None
    return digest(asset)


def stamp() -> list[tuple[str, int]]:
    changed = []
    for page in sorted(SITE.glob("*.html")):
        original = page.read_text(encoding="utf-8")

        def replace(m: re.Match[str]) -> str:
            digest = _digest(m["path"])
            if digest is None:                       # external or missing: leave alone
                return m.group(0)
            return f'{m["attr"]}="{m["path"]}?v={digest}"'

        updated, n = REF.subn(replace, original)
        if updated != original:
            page.write_text(updated, encoding="utf-8")
        changed.append((page.name, n))
    return changed


def main() -> None:
    for name, n in stamp():
        print(f"  {name:22} {n} asset link(s) stamped")


if __name__ == "__main__":
    main()
