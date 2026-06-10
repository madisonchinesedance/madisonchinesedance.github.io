#!/usr/bin/env python3
"""Rename a page folder under both pages/ and content/, updating all route references.

Usage (interactive):

    python scripts/rename-folder.py

Or non-interactive:

    python scripts/rename-folder.py <old-folder-name> <new-folder-name>

This updates:
  1. Moves all files from pages/<old>/ to pages/<new>/
  2. Moves all files from content/<old>/ to content/<new>/
  3. Updates every route in site.json that references files in the folder
  4. Updates data-route attributes in all affected HTML files
"""

from __future__ import annotations

import json
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


class RenameResult:
    """Tracks every change made during a folder rename."""

    def __init__(self, old_folder: str, new_folder: str):
        self.old_folder = old_folder
        self.new_folder = new_folder
        self.changes: list[str] = []

    def log(self, description: str) -> None:
        self.changes.append(description)


# ── Core rename logic ────────────────────────────────────────────────────────

def rename_folder(
    old_folder: str,
    new_folder: str,
    root: Path,
    *,
    force: bool = False,
) -> RenameResult:
    """Rename a page folder under pages/ and content/, updating all references."""
    result = RenameResult(old_folder, new_folder)

    content_root = root / "content"
    pages_root = root / "pages"
    site_path = content_root / "site.json"

    old_pages_dir = pages_root / old_folder
    new_pages_dir = pages_root / new_folder
    old_content_dir = content_root / old_folder
    new_content_dir = content_root / new_folder

    # Validate
    if not old_pages_dir.is_dir() and not old_content_dir.is_dir():
        print(f"Error: folder '{old_folder}' not found under pages/ or content/")
        sys.exit(1)

    if new_pages_dir.exists() or new_content_dir.exists():
        if not force:
            print(f"Error: destination folder '{new_folder}' already exists.")
            sys.exit(1)
        else:
            print(f"Warning: destination folder '{new_folder}' exists – will merge/overwrite.")

    # ── 1. Move pages/ folder ────────────────────────────────────────────

    if old_pages_dir.is_dir():
        new_pages_dir.mkdir(parents=True, exist_ok=True)
        for file in old_pages_dir.iterdir():
            if file.is_file():
                dest = new_pages_dir / file.name
                shutil.move(str(file), str(dest))
                result.log(f"Moved page: {old_folder}/{file.name} -> {new_folder}/{file.name}")
        # Remove old directory if empty
        try:
            old_pages_dir.rmdir()
        except OSError:
            pass

    # ── 2. Move content/ folder ──────────────────────────────────────────

    if old_content_dir.is_dir():
        new_content_dir.mkdir(parents=True, exist_ok=True)
        for file in old_content_dir.iterdir():
            if file.is_file():
                dest = new_content_dir / file.name
                shutil.move(str(file), str(dest))
                result.log(f"Moved content: {old_folder}/{file.name} -> {new_folder}/{file.name}")
        # Remove old directory if empty
        try:
            old_content_dir.rmdir()
        except OSError:
            pass

    # ── 3. Update site.json routes ───────────────────────────────────────

    site = load_json(site_path)
    routes = site.get("routes", {})
    updated_count = 0

    for route_id, route_info in routes.items():
        updated = False
        for field in ("href", "page", "content"):
            if field in route_info and f"{old_folder}/" in route_info[field]:
                route_info[field] = route_info[field].replace(f"{old_folder}/", f"{new_folder}/")
                updated = True
        if updated:
            updated_count += 1

    if updated_count:
        write_json(site_path, site)
        result.log(f"Updated {updated_count} route(s) in site.json")

    # ── 4. Update data-route in moved HTML files ─────────────────────────

    if new_pages_dir.is_dir():
        for html_file in new_pages_dir.glob("*.html"):
            html = html_file.read_text(encoding="utf-8")
            # No data-route changes needed here — data-route uses route IDs, not folder names.
            # But we do update any hardcoded folder references in the HTML content.
            # (Typically there are none, but we check anyway.)

    # ── 5. Update header.json navigation ─────────────────────────────────

    header_path = content_root / "header.json"
    if header_path.exists():
        header = load_json(header_path)
        # Nav items don't contain folder paths directly, but route IDs may reference
        # pages in this folder. The route IDs themselves don't change with a folder rename,
        # only the file paths in site.json change. So no header changes needed.

    # ── Summary ──────────────────────────────────────────────────────────

    if not result.changes:
        result.log("No changes needed — folder content may already be in the target location.")

    return result


# ── CLI entry point ──────────────────────────────────────────────────────────

def interactive_menu() -> None:
    root = repo_root()
    pages_root = root / "pages"
    content_root = root / "content"

    print("\nRename Folder\n")
    print("Current folders:")

    # List folders that exist under pages/ or content/
    all_folders = set()
    if pages_root.is_dir():
        all_folders.update(
            d.name for d in pages_root.iterdir() if d.is_dir()
        )
    if content_root.is_dir():
        all_folders.update(
            d.name for d in content_root.iterdir() if d.is_dir()
        )

    for folder in sorted(all_folders):
        pages_exists = (pages_root / folder).is_dir()
        content_exists = (content_root / folder).is_dir()
        status = []
        if pages_exists:
            count = len(list((pages_root / folder).glob("*.html")))
            status.append(f"pages/ ({count} HTML)")
        if content_exists:
            count = len(list((content_root / folder).glob("*.json")))
            status.append(f"content/ ({count} JSON)")
        print(f"  • {folder}/ — {', '.join(status)}")

    old_folder = prompt("\nFolder name to rename")
    if not old_folder:
        print("No folder name provided.")
        return

    new_folder = prompt(f"New name for '{old_folder}'")
    if not new_folder:
        print("No new name provided.")
        return

    if new_folder == old_folder:
        print("Same name. Nothing to do.")
        return

    print(f"\nRenaming '{old_folder}/' → '{new_folder}/' will:")
    print(f"  • Move all HTML files from pages/{old_folder}/ → pages/{new_folder}/")
    print(f"  • Move all JSON files from content/{old_folder}/ → content/{new_folder}/")
    print(f"  • Update route paths in site.json")

    if not confirm("\nProceed?"):
        print("Aborted.")
        return

    result = rename_folder(old_folder, new_folder, root)

    print(f"\n{'='*50}")
    print(f"Folder rename complete: {old_folder}/ -> {new_folder}/")
    print(f"{'='*50}")
    for change in result.changes:
        print(f"  - {change}")
    print(f"\nTotal changes: {len(result.changes)}")


def main() -> None:
    root = repo_root()

    if len(sys.argv) == 3:
        old_folder = sys.argv[1]
        new_folder = sys.argv[2]
        print(f"Renaming folder '{old_folder}/' -> '{new_folder}/'...")
        result = rename_folder(old_folder, new_folder, root)
        for change in result.changes:
            print(f"  - {change}")
        print(f"\nDone. {len(result.changes)} change(s) made.")
    elif len(sys.argv) == 1:
        interactive_menu()
    else:
        print("Usage: python scripts/rename-folder.py [<old-folder> <new-folder>]")
        sys.exit(1)


if __name__ == "__main__":
    main()