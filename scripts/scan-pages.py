#!/usr/bin/env python3
"""Scan docs/ and rebuild site.json routes and header.json navigation.

Usage:
    python scripts/scan-pages.py           # interactive confirm before write
    python scripts/scan-pages.py --write   # non-interactive
    python scripts/scan-pages.py --dry-run # print summary, no writes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from site_lib import (
    CONTENT_ROOT,
    DOCS_ROOT,
    HEADER_JSON,
    INDEX_HTML,
    PAGES_ROOT,
    SITE_JSON,
    confirm,
    extract_data_route,
    load_json,
    nav_label_for_route,
    page_rel_to_content_rel,
    slug_to_title,
    write_json,
)

YEAR_RE = re.compile(r"(20\d{2})")


def scan_routes() -> tuple[dict, list[str]]:
    """Return (routes dict, warnings list)."""
    routes: dict[str, dict] = {}
    warnings: list[str] = []

    if INDEX_HTML.is_file():
        content_rel = "index.json"
        if not (CONTENT_ROOT / content_rel).is_file():
            warnings.append(f"Missing content file for home: {content_rel}")
        routes["home"] = {
            "href": "index.html",
            "page": "index.html",
            "content": content_rel,
        }
    else:
        warnings.append(f"Missing home page: {INDEX_HTML.relative_to(DOCS_ROOT.parent)}")

    if not PAGES_ROOT.is_dir():
        warnings.append(f"Pages directory not found: {PAGES_ROOT}")
        return routes, warnings

    for html_path in sorted(PAGES_ROOT.rglob("*.html")):
        page_rel = html_path.relative_to(PAGES_ROOT).as_posix()
        stem = html_path.stem
        route_id = extract_data_route(html_path) or stem

        if route_id in routes:
            warnings.append(
                f"Duplicate route ID '{route_id}' for {page_rel} (already registered)"
            )
            continue

        if extract_data_route(html_path) is None and route_id != stem:
            warnings.append(
                f"{page_rel}: no data-route attribute; using filename stem '{stem}'"
            )

        content_rel = page_rel_to_content_rel(page_rel)
        if not (CONTENT_ROOT / content_rel).is_file():
            warnings.append(f"Missing content JSON for {page_rel}: {content_rel}")

        routes[route_id] = {
            "href": f"pages/{page_rel}",
            "page": page_rel,
            "content": content_rel,
        }

    return routes, warnings


def _splendid_china_sort_key(route_id: str) -> tuple[int, str]:
    match = YEAR_RE.search(route_id)
    year = int(match.group(1)) if match else 0
    return (-year, route_id)


def _nav_item(route_id: str, content_rel: str) -> dict:
    return {
        "route": route_id,
        "label": nav_label_for_route(route_id, content_rel),
    }


def build_nav(routes: dict, header: dict) -> list:
    action_routes = {
        item.get("route")
        for item in header.get("actions", [])
        if item.get("route")
    }

    nav: list = []

    if "home" in routes:
        nav.append(_nav_item("home", routes["home"]["content"]))

    top_level: list[dict] = []
    folders: dict[str, list[dict]] = {}

    for route_id, info in routes.items():
        if route_id == "home":
            continue
        if route_id in action_routes:
            continue

        page_rel = info["page"]
        parts = Path(page_rel).parts
        if len(parts) == 1:
            top_level.append(_nav_item(route_id, info["content"]))
        elif len(parts) >= 2:
            folder = parts[0]
            folders.setdefault(folder, []).append(_nav_item(route_id, info["content"]))

    top_level.sort(key=lambda item: item["label"].lower())
    nav.extend(top_level)

    for folder in sorted(folders.keys()):
        items = folders[folder]
        if folder == "splendid-china":
            items.sort(key=lambda item: _splendid_china_sort_key(item["route"]))
        else:
            items.sort(key=lambda item: item["label"].lower())
        nav.append({"label": slug_to_title(folder), "items": items})

    return nav


def scan_pages(*, dry_run: bool = False, write: bool = False, interactive: bool = False) -> int:
    if not DOCS_ROOT.is_dir():
        print(f"Error: docs root not found at {DOCS_ROOT}")
        return 1

    old_site = load_json(SITE_JSON)
    old_routes = old_site.get("routes", {})
    header = load_json(HEADER_JSON)

    new_routes, warnings = scan_routes()
    dropped = sorted(set(old_routes) - set(new_routes))
    added = sorted(set(new_routes) - set(old_routes))

    print(f"\nScan results: {len(new_routes)} route(s)")
    if added:
        print(f"  Added: {', '.join(added)}")
    if dropped:
        print(f"  Dropped: {', '.join(dropped)}")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ! {warning}")

    new_nav = build_nav(new_routes, header)
    nav_count = sum(
        1 if "route" in item else len(item.get("items", [])) for item in new_nav
    )
    print(f"\nNavigation: {len(new_nav)} top-level entries, {nav_count} link(s)")

    if dry_run:
        print("\nDry run — no files written.")
        return 0

    if interactive and not write:
        if not confirm("\nWrite site.json and header.json?"):
            print("Aborted.")
            return 0

    write_json(SITE_JSON, {"routes": new_routes})

    header["nav"] = new_nav
    write_json(HEADER_JSON, header)

    print(f"\nWrote {SITE_JSON.relative_to(DOCS_ROOT.parent.parent)}")
    print(f"Wrote {HEADER_JSON.relative_to(DOCS_ROOT.parent.parent)}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild site.json and nav from docs/")
    parser.add_argument("--write", action="store_true", help="Write without confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Show summary only")
    args = parser.parse_args()

    interactive = not args.write and not args.dry_run
    sys.exit(scan_pages(dry_run=args.dry_run, write=args.write, interactive=interactive))


if __name__ == "__main__":
    main()
