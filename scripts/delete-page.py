#!/usr/bin/env python3
"""
Delete a page from the site.

Usage:
    python scripts/delete-page.py

The script lists all routes defined in content/site.json, prompts the user to select one,
and then removes the corresponding HTML and JSON files as well as the route entry
from site.json.

It is safe to run multiple times; only the selected route will be removed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def repo_root() -> Path:
    """Root directory of the repository (the parent of the scripts folder)."""
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    """Write a dictionary to a JSON file with pretty formatting."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_routes(site: dict) -> list[tuple[str, dict]]:
    """Return a sorted list of (route_id, info) tuples."""
    routes = site.get("routes", {})
    return sorted(routes.items())


def prompt(message: str) -> str:
    """Simple input prompt."""
    return input(f"{message}: ").strip()


def confirm(message: str) -> bool:
    """Ask a yes/no question."""
    answer = input(f"{message} (y/n): ").strip().lower()
    return answer in {"y", "yes"}


def main() -> None:
    root = repo_root()
    content_root = root / "content"
    pages_root = root / "pages"
    site_path = content_root / "site.json"

    if not site_path.is_file():
        print("site.json not found – are you in the correct repository?")
        sys.exit(1)

    site = load_json(site_path)

    routes = list_routes(site)
    if not routes:
        print("No routes defined in site.json.")
        return

    print("\nAvailable routes:")
    for idx, (route_id, info) in enumerate(routes, start=1):
        print(f"  {idx}. {route_id} → {info.get('page')} (content: {info.get('content')})")

    choice = prompt("\nEnter the number of the route to delete")
    if not choice.isdigit():
        print("Invalid selection.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(routes):
        print("Selection out of range.")
        return

    route_id, info = routes[idx]

    print(f"\nYou have selected route '{route_id}':")
    print(f"  HTML file : {info.get('page')}")
    print(f"  JSON file : {info.get('content')}")

    if not confirm("Are you sure you want to delete this page and its data?"):
        print("Aborted.")
        return

    # Remove HTML file
    html_path = pages_root / info.get("page", "")
    if html_path.is_file():
        html_path.unlink()
        print(f"Deleted HTML: {html_path.relative_to(root)}")
    else:
        print(f"HTML file not found: {html_path.relative_to(root)}")

    # Remove JSON file
    json_path = content_root / info.get("content", "")
    if json_path.is_file():
        json_path.unlink()
        print(f"Deleted JSON: {json_path.relative_to(root)}")
    else:
        print(f"JSON file not found: {json_path.relative_to(root)}")

    # Remove route from site.json
    del site["routes"][route_id]
    write_json(site_path, site)
    print(f"Removed route '{route_id}' from site.json.")

    print("\nDeletion complete.")


if __name__ == "__main__":
    main()