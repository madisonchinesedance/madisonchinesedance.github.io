#!/usr/bin/env python3
"""Rename a page's route, labels, and all cross-references across the site.

Usage (interactive):

    python scripts/rename-page.py

The script lists all routes, lets you pick one, and prompts for the new
route ID.  It then updates:

  1. content/site.json          – route key, page path, content path
  2. The HTML file              – file name, <title>, data-route attribute
  3. The JSON content file      – file name, pageTitle / metaDescription
  4. content/header.json        – any nav items referencing the old route
  5. content/footer.json        – any footer links referencing the old route
  6. All other content JSONs    – cross-references (route fields) site-wide
  7. All other HTML files       – data-route attributes referencing the old route

You can also supply arguments for non-interactive use:

    python scripts/rename-page.py <old-route-id> <new-route-id>
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────────────────

def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prompt(message: str) -> str:
    return input(f"{message}: ").strip()


def confirm(message: str) -> bool:
    answer = input(f"{message} (y/n): ").strip().lower()
    return answer in {"y", "yes"}


# ── Core rename logic ────────────────────────────────────────────────────────

class RenameResult:
    """Tracks every file / field that was changed."""

    def __init__(self, old_id: str, new_id: str):
        self.old_id = old_id
        self.new_id = new_id
        self.changes: list[str] = []

    def log(self, description: str) -> None:
        self.changes.append(description)


def list_routes(site: dict) -> list[tuple[str, dict]]:
    return sorted(site.get("routes", {}).items())


def slug_from_path(file_path: str, old_slug: str, new_slug: str) -> str:
    return file_path.replace(f"{old_slug}.", f"{new_slug}.")


# Words that should remain lowercase in title case (unless first word)
_TITLE_CASE_MINOR_WORDS = {
    "a", "an", "the", "and", "but", "or", "for", "nor",
    "on", "at", "to", "from", "by", "in", "of", "vs", "via",
}


def slug_to_title(slug: str) -> str:
    """Convert a kebab-case slug to Title Case.

    Examples:
        "about-us"         → "About Us"
        "meet-the-faculty" → "Meet the Faculty"
        "splendid-china-2026" → "Splendid China 2026"
        "book-a-performance" → "Book a Performance"
    """
    words = slug.replace("_", "-").split("-")
    if not words:
        return slug
    # Always capitalize first and last words; minor words only mid-title
    result = []
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word.lower() not in _TITLE_CASE_MINOR_WORDS:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return " ".join(result)


def rename_page(old_id: str, new_id: str, root: Path, *, force: bool = False) -> RenameResult:
    """Perform the full rename and return a summary of changes."""
    result = RenameResult(old_id, new_id)

    content_root = root / "content"
    pages_root = root / "pages"
    site_path = content_root / "site.json"
    header_path = content_root / "header.json"
    footer_path = content_root / "footer.json"

    site = load_json(site_path)
    routes = site.get("routes", {})

    if old_id not in routes:
        print(f"Error: route '{old_id}' not found in site.json.")
        sys.exit(1)

    if new_id in routes:
        if not force:
            print(f"Error: route '{new_id}' already exists in site.json.")
            sys.exit(1)
        else:
            print(f"Warning: route '{new_id}' already exists – overwriting.")

    route_info = routes[old_id]
    old_html_rel = route_info["page"]
    old_json_rel = route_info["content"]

    # Derive new paths (same directory, new file name)
    new_html_rel = slug_from_path(old_html_rel, old_id, new_id)
    new_json_rel = slug_from_path(old_json_rel, old_id, new_id)

    old_html = pages_root / old_html_rel
    new_html = pages_root / new_html_rel
    old_json = content_root / old_json_rel
    new_json = content_root / new_json_rel

    # ── 1. Move / rename files ────────────────────────────────────────────

    if old_html.exists():
        new_html.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_html), str(new_html))
        result.log(f"Renamed HTML: {old_html_rel} → {new_html_rel}")

    if old_json.exists():
        new_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_json), str(new_json))
        result.log(f"Renamed JSON: {old_json_rel} → {new_json_rel}")

    # ── 2. Update site.json ───────────────────────────────────────────────

    route_entry = routes.pop(old_id)
    route_entry["page"] = new_html_rel
    route_entry["content"] = new_json_rel
    # Also update href if it referenced the old HTML file
    if "href" in route_entry and old_html_rel.replace(".html", "") in route_entry["href"]:
        route_entry["href"] = slug_from_path(route_entry["href"], old_id, new_id)
    elif "href" in route_entry:
        route_entry["href"] = slug_from_path(route_entry["href"], old_id, new_id)
    routes[new_id] = route_entry
    write_json(site_path, site)
    result.log(f"Updated site.json route: {old_id} → {new_id}")

    # ── 3. Update the HTML file (title, data-route) ──────────────────────

    new_title = slug_to_title(new_id)

    if new_html.exists():
        html = new_html.read_text(encoding="utf-8")

        # Replace data-route attribute (keep lowercase slug)
        html_new = re.sub(
            r'(data-route\s*=\s*")' + re.escape(old_id) + r'(")',
            rf'\g<1>{new_id}\2',
            html,
        )

        # Replace old route ID in <title> with properly capitalized form
        # Match patterns like "Old Route | MCD..." or "Old Route | Madison..."
        # Use title-case replacement, not raw slug
        html_new = html_new.replace(old_id, new_title)

        if html_new != html:
            new_html.write_text(html_new, encoding="utf-8")
            result.log(f"Updated HTML content: data-route, title, meta for '{new_id}'")

    # ── 4. Update the JSON content file (pageTitle) ──────────────────────

    if new_json.exists():
        page_content = load_json(new_json)

        # Update pageTitle if it references the old route (use title case)
        if "pageTitle" in page_content and old_id in page_content["pageTitle"]:
            page_content["pageTitle"] = page_content["pageTitle"].replace(old_id, new_title)
            result.log(f"Updated pageTitle in {new_json_rel}")

        # Update metaDescription if it references the old route
        if "metaDescription" in page_content and old_id in page_content["metaDescription"]:
            page_content["metaDescription"] = page_content["metaDescription"].replace(old_id, new_title)
            result.log(f"Updated metaDescription in {new_json_rel}")

        write_json(new_json, page_content)

    # ── 5. Update header.json navigation ─────────────────────────────────

    if header_path.exists():
        header = load_json(header_path)
        header_updated = _update_route_refs_in_obj(header, old_id, new_id)
        if header_updated:
            write_json(header_path, header)
            result.log("Updated route references in header.json")

    # ── 6. Update footer.json ────────────────────────────────────────────

    if footer_path.exists():
        footer = load_json(footer_path)
        footer_updated = _update_route_refs_in_obj(footer, old_id, new_id)
        if footer_updated:
            write_json(footer_path, footer)
            result.log("Updated route references in footer.json")

    # ── 7. Update all other content JSON files (cross-references) ────────

    for json_file in content_root.rglob("*.json"):
        if json_file in (site_path, header_path, footer_path, new_json):
            continue

        data = load_json(json_file)
        updated = _update_route_refs_in_obj(data, old_id, new_id)
        if updated:
            write_json(json_file, data)
            result.log(f"Updated cross-references in {json_file.relative_to(root)}")

    # ── 8. Update all other HTML files (data-route attributes) ───────────

    for html_file in pages_root.rglob("*.html"):
        if html_file == new_html:
            continue

        html = html_file.read_text(encoding="utf-8")
        pattern = r'(data-route\s*=\s*")' + re.escape(old_id) + r'(")'
        new_html_text, count = re.subn(pattern, rf'\g<1>{new_id}\2', html)
        if count > 0:
            html_file.write_text(new_html_text, encoding="utf-8")
            result.log(f"Updated data-route in {html_file.relative_to(root)}")

    return result


def _update_route_refs_in_obj(obj: dict | list, old_id: str, new_id: str) -> bool:
    """Recursively replace route values matching old_id → new_id.
    Also updates 'label' values that match the old route's title-case form
    to the new route's title-case form.

    Returns True if any changes were made."""
    new_title = slug_to_title(new_id)
    changed = False
    if isinstance(obj, dict):
        # Update route references (keep as kebab-case slug)
        for key, value in obj.items():
            if key == "route" and value == old_id:
                obj[key] = new_id
                changed = True
            elif isinstance(value, (dict, list)):
                if _update_route_refs_in_obj(value, old_id, new_id):
                    changed = True
        # Update label fields: replace the old title with new title
        if "label" in obj and isinstance(obj["label"], str):
            old_title = slug_to_title(old_id)
            if obj["label"] == old_title:
                obj["label"] = new_title
                changed = True
        # Update heading fields
        if "heading" in obj and isinstance(obj["heading"], str):
            old_title = slug_to_title(old_id)
            if obj["heading"] == old_title:
                obj["heading"] = new_title
                changed = True
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                if _update_route_refs_in_obj(item, old_id, new_id):
                    changed = True
    return changed


# ── CLI entry point ──────────────────────────────────────────────────────────

def interactive_menu() -> None:
    root = repo_root()
    site_path = root / "content" / "site.json"
    site = load_json(site_path)

    print("\nRename Page\n")

    routes = list_routes(site)
    if not routes:
        print("No routes defined in site.json.")
        return

    print("Available routes:")
    for idx, (route_id, info) in enumerate(routes, 1):
        print(f"  {idx}. {route_id} → {info.get('page')}")

    choice = prompt("\nEnter the number of the route to rename")
    if not choice.isdigit():
        print("Invalid selection.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(routes):
        print("Selection out of range.")
        return

    old_id = routes[idx][0]
    new_id = prompt(f"New route ID for '{old_id}'")

    if not new_id:
        print("No new route ID provided.")
        return

    if new_id == old_id:
        print("New route ID is the same as the old one. Nothing to do.")
        return

    print(f"\nRenaming '{old_id}' → '{new_id}' will:")
    print(f"  • Rename HTML file")
    print(f"  • Rename JSON content file")
    print(f"  • Update site.json route entry")
    print(f"  • Update data-route in HTML")
    print(f"  • Update page title and meta")
    print(f"  • Update navigation labels in header.json")
    print(f"  • Update footer links in footer.json")
    print(f"  • Update cross-references in all content JSON files")
    print(f"  • Update data-route in all other HTML pages")

    if not confirm("\nProceed?"):
        print("Aborted.")
        return

    result = rename_page(old_id, new_id, root)

    print(f"\n{'='*50}")
    print(f"Rename complete: {old_id} -> {new_id}")
    print(f"{'='*50}")
    for change in result.changes:
        print(f"  - {change}")
    print(f"\nTotal changes: {len(result.changes)}")


def main() -> None:
    root = repo_root()

    # Support non-interactive CLI: rename-page.py <old> <new>
    if len(sys.argv) == 3:
        old_id = sys.argv[1]
        new_id = sys.argv[2]
        print(f"Renaming '{old_id}' -> '{new_id}'...")
        result = rename_page(old_id, new_id, root)
        for change in result.changes:
            print(f"  - {change}")
        print(f"\nDone. {len(result.changes)} change(s) made.")
    elif len(sys.argv) == 1:
        interactive_menu()
    else:
        print("Usage: python scripts/rename-page.py [<old-route-id> <new-route-id>]")
        sys.exit(1)


if __name__ == "__main__":
    main()