#!/usr/bin/env python3
"""Update HTML pages to use data-page-blocks layout."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    "pages/classes/beginner-dancers.html",
    "pages/classes/intermediate-dancers.html",
    "pages/classes/advanced-dancers.html",
    "pages/donate.html",
    "pages/tickets.html",
    "pages/events/events.html",
    "pages/events/services.html",
    "pages/gallery.html",
    *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "pages/splendid-china").glob("*.html")),
]

MAIN_PATTERN = re.compile(
    r'<main id="main" tabindex="-1" class="site-main"[^>]*>.*?</main>',
    re.DOTALL,
)

LIGHTBOX_PATTERN = re.compile(
    r'\n\t<div class="gallery-lightbox".*?</div>\n',
    re.DOTALL,
)


def main() -> None:
    for rel in PAGES:
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING {rel}")
            continue

        text = path.read_text(encoding="utf-8")
        if "data-page-blocks" in text and "page-hero" not in text:
            print(f"SKIP {rel}")
            continue

        new_main = (
            '\t<main id="main" tabindex="-1" class="site-main" data-page-blocks></main>'
        )
        new_text, count = MAIN_PATTERN.subn(new_main, text)
        if count == 0:
            print(f"NO MATCH {rel}")
            continue

        if rel.endswith("gallery.html"):
            new_text = LIGHTBOX_PATTERN.sub("\n", new_text)

        path.write_text(new_text, encoding="utf-8")
        print(f"Updated {rel}")


if __name__ == "__main__":
    main()
