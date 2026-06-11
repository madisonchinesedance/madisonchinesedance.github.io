#!/usr/bin/env python3
"""Move data-page-blocks from inner div to main element."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r'<main id="main" tabindex="-1" class="site-main">\s*<div data-page-blocks></div>\s*</main>',
    re.DOTALL,
)
REPLACEMENT = '<main id="main" tabindex="-1" class="site-main" data-page-blocks></main>'


def main() -> None:
    for path in (ROOT / "pages").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        new_text, count = PATTERN.subn(REPLACEMENT, text)
        if count:
            path.write_text(new_text, encoding="utf-8")
            print(f"Fixed {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
