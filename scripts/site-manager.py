#!/usr/bin/env python3
"""Unified site management — pages, content, navigation, and images.

Run interactively:

    python scripts/site-manager.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from content_editor import edit_page_content, pick_route
from page_ops import create_page, delete_page, rename_folder, rename_page
from site_lib import (
    CONTENT_ROOT,
    HEADER_JSON,
    PAGES_ROOT,
    REPO_ROOT,
    SITE_JSON,
    confirm,
    find_nav_item,
    list_nav_items,
    list_routes,
    load_json,
    prompt,
    prompt_choice,
    slug_to_title,
    write_json,
)

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_script(script_name: str, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPTS_DIR / script_name), *args], check=False)


def cmd_list_routes() -> None:
    site = load_json(SITE_JSON)
    routes = site.get("routes", {})
    if not routes:
        print("No routes defined.")
        return
    print("\nCurrent routes:")
    for route_id, info in sorted(routes.items()):
        print(f"  {route_id} → {info['page']} (content: {info['content']})")


def cmd_create_page() -> None:
    print("\nCreate a new page\n")
    title = prompt("Page title", "New Page")
    slug = prompt("Route slug (e.g., about, classes/new-class)")
    if not slug:
        print("No route slug provided.")
        return

    html_path, json_path = create_page(title, slug)
    print(f"\nCreated page: {html_path.relative_to(REPO_ROOT)}")
    print(f"Created content: {json_path.relative_to(REPO_ROOT)}")
    print("Updated site.json")
    print("\nRun 'Scan pages' to refresh navigation.")


def cmd_delete_page() -> None:
    site = load_json(SITE_JSON)
    routes = list_routes(site)
    if not routes:
        print("No routes defined.")
        return

    print("\nAvailable routes:")
    for idx, (route_id, info) in enumerate(routes, start=1):
        print(f"  {idx}. {route_id} → {info.get('page')}")

    choice = prompt("\nEnter the number of the route to delete")
    if not choice.isdigit():
        print("Invalid selection.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(routes):
        print("Selection out of range.")
        return

    route_id = routes[idx][0]
    if route_id == "home":
        print("Cannot delete the home route.")
        return

    if not confirm(f"Delete route '{route_id}' and all references?"):
        print("Aborted.")
        return

    changes = delete_page(route_id)
    print("\nDeletion complete:")
    for change in changes:
        print(f"  - {change}")


def cmd_rename_page() -> None:
    site = load_json(SITE_JSON)
    routes = list_routes(site)
    if not routes:
        print("No routes defined.")
        return

    print("\nAvailable routes:")
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
    if not new_id or new_id == old_id:
        print("Nothing to do.")
        return

    if not confirm(f"Rename '{old_id}' → '{new_id}'?"):
        print("Aborted.")
        return

    result = rename_page(old_id, new_id)
    print(f"\nRename complete: {old_id} → {new_id}")
    for change in result.changes:
        print(f"  - {change}")


def cmd_rename_folder() -> None:
    print("\nRename Folder\n")
    print("Current folders:")

    all_folders: set[str] = set()
    if PAGES_ROOT.is_dir():
        all_folders.update(d.name for d in PAGES_ROOT.iterdir() if d.is_dir())
    if CONTENT_ROOT.is_dir():
        all_folders.update(d.name for d in CONTENT_ROOT.iterdir() if d.is_dir())

    for folder in sorted(all_folders):
        pages_exists = (PAGES_ROOT / folder).is_dir()
        content_exists = (CONTENT_ROOT / folder).is_dir()
        status = []
        if pages_exists:
            count = len(list((PAGES_ROOT / folder).glob("*.html")))
            status.append(f"pages/ ({count} HTML)")
        if content_exists:
            count = len(list((CONTENT_ROOT / folder).glob("*.json")))
            status.append(f"content/ ({count} JSON)")
        print(f"  * {folder}/ — {', '.join(status)}")

    old_folder = prompt("\nFolder name to rename")
    if not old_folder:
        return

    new_folder = prompt(f"New name for '{old_folder}'")
    if not new_folder or new_folder == old_folder:
        return

    new_label = slug_to_title(new_folder)
    print(f"\nRenaming '{old_folder}/' → '{new_folder}/' (nav label: '{new_label}')")

    if not confirm("Proceed?"):
        print("Aborted.")
        return

    result = rename_folder(old_folder, new_folder)
    print("\nFolder rename complete:")
    for change in result.changes:
        print(f"  - {change}")


def cmd_change_location() -> None:
    choice = prompt_choice(
        "Change page location",
        ["Rename page (route ID)", "Rename folder"],
    )
    if choice == 1:
        cmd_rename_page()
    elif choice == 2:
        cmd_rename_folder()


def cmd_edit_page() -> None:
    route_id = pick_route()
    if not route_id:
        return

    while True:
        print(f"\nEdit page: {route_id}")
        print("1. Change location (rename page or folder)")
        print("2. Edit content")
        print("3. Edit page settings (title & meta description)")
        print("b. Back")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break
        elif choice == "1":
            saved_id = route_id
            cmd_change_location()
            # Route may have been renamed; re-pick if needed
            site = load_json(SITE_JSON)
            if saved_id not in site.get("routes", {}):
                print("Route was renamed. Returning to page list.")
                break
        elif choice == "2":
            edit_page_content(route_id)
        elif choice == "3":
            from content_editor import edit_page_settings, load_page_content

            loaded = load_page_content(route_id)
            if loaded:
                path, data = loaded
                edit_page_settings(data, path)
        else:
            print("Invalid choice.")


def cmd_manage_pages() -> None:
    while True:
        print("\nManage pages")
        print("1. Create page")
        print("2. Delete page")
        print("3. Edit page")
        print("b. Back to main menu")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break
        elif choice == "1":
            cmd_create_page()
        elif choice == "2":
            cmd_delete_page()
        elif choice == "3":
            cmd_edit_page()
        else:
            print("Invalid choice.")


def cmd_edit_nav() -> None:
    header = load_json(HEADER_JSON)
    nav = header.setdefault("nav", [])

    while True:
        print("\nNavigation editor")
        print("1. List navigation")
        print("2. Rename a nav item")
        print("3. Move a nav item (top-level ↔ dropdown)")
        print("4. Reorder a dropdown menu")
        print("5. Remove a nav item")
        print("b. Back")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break

        if choice == "1":
            print("\nCurrent navigation:")
            list_nav_items(nav)

        elif choice == "2":
            label = prompt("Label of the nav item to rename")
            result = find_nav_item(nav, label)
            if not result:
                print(f"Item '{label}' not found.")
                continue
            item, _, _ = result
            new_label = prompt("New label")
            if new_label:
                item["label"] = new_label
                write_json(HEADER_JSON, header)
                print(f"Renamed to '{new_label}'.")

        elif choice == "3":
            label = prompt("Label of the nav item to move")
            result = find_nav_item(nav, label)
            if not result:
                print(f"Item '{label}' not found.")
                continue
            item, parent_list, idx = result
            parent_list.pop(idx)

            options = ["Top-level menu"]
            for nav_item in nav:
                if "items" in nav_item:
                    options.append(f"Dropdown: {nav_item.get('label', '(group)')}")

            dest = prompt_choice("Where should this item go?", options)
            if dest is None:
                parent_list.insert(idx, item)
                continue

            if dest == 1:
                nav.append(item)
            else:
                dropdown = nav[dest - 2]
                dropdown.setdefault("items", []).append(item)

            write_json(HEADER_JSON, header)
            print("Item moved.")

        elif choice == "4":
            dropdown_label = prompt("Label of the dropdown to reorder")
            dropdown = None
            for item in nav:
                if item.get("label") == dropdown_label and "items" in item:
                    dropdown = item
                    break

            if not dropdown:
                print(f"Dropdown '{dropdown_label}' not found.")
                continue

            items = dropdown["items"]
            print("Current order:")
            for i, sub in enumerate(items, 1):
                print(f"  {i}. {sub.get('label', '')}")

            order_str = prompt("New order (e.g., 3,1,2)")
            try:
                new_order = [int(x.strip()) - 1 for x in order_str.split(",")]
                dropdown["items"] = [items[i] for i in new_order]
                write_json(HEADER_JSON, header)
                print("Reordered.")
            except (ValueError, IndexError):
                print("Invalid order.")

        elif choice == "5":
            label = prompt("Label of the nav item to remove")
            result = find_nav_item(nav, label)
            if not result:
                print(f"Item '{label}' not found.")
                continue
            _, parent_list, idx = result
            parent_list.pop(idx)
            write_json(HEADER_JSON, header)
            print("Item removed.")

        else:
            print("Invalid choice.")


def cmd_update_images() -> None:
    while True:
        print("\nUpdate images")
        print("1. Categorize homepage runners (dry-run)")
        print("2. Categorize homepage runners (apply)")
        print("3. Reconcile homepage-runner duplicates (dry-run)")
        print("4. Reconcile homepage-runner duplicates (apply)")
        print("5. Sync images from R2 → JSON")
        print("b. Back")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break
        elif choice == "1":
            run_script("scan-images.py", "categorize")
        elif choice == "2":
            run_script("scan-images.py", "categorize", "--apply")
        elif choice == "3":
            run_script("scan-images.py", "categorize", "--reconcile")
        elif choice == "4":
            run_script("scan-images.py", "categorize", "--reconcile", "--apply")
        elif choice == "5":
            run_script("scan-images.py", "sync")
        else:
            print("Invalid choice.")


def cmd_site_tools() -> None:
    while True:
        print("\nSite tools")
        print("1. Edit navigation")
        print("2. Scan pages (rebuild site.json + nav)")
        print("3. Update images")
        print("4. List routes")
        print("b. Back to main menu")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break
        elif choice == "1":
            cmd_edit_nav()
        elif choice == "2":
            run_script("scan-pages.py")
        elif choice == "3":
            cmd_update_images()
        elif choice == "4":
            cmd_list_routes()
        else:
            print("Invalid choice.")


def main() -> None:
    print("\nSite Manager\n")

    while True:
        print("\nOptions:")
        print("1. Manage pages")
        print("2. Site tools")
        print("q. Quit")

        choice = prompt("\nWhat would you like to do?").lower()

        if choice in ("q", "quit", "exit"):
            break
        elif choice == "1":
            cmd_manage_pages()
        elif choice == "2":
            cmd_site_tools()
        else:
            print("Invalid choice.")

    print("\nDone.")


if __name__ == "__main__":
    main()
