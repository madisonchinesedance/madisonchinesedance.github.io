#!/usr/bin/env python3
"""Deprecated — use scan-images.py categorize instead."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    print(
        "Note: categorize-homepage-runner.py is deprecated.\n"
        "Use: python scripts/scan-images.py categorize [options]\n",
        file=sys.stderr,
    )
    script = Path(__file__).resolve().parent / "scan-images.py"
    result = subprocess.run(
        [sys.executable, str(script), "categorize", *sys.argv[1:]],
        check=False,
    )
    raise SystemExit(result.returncode)
