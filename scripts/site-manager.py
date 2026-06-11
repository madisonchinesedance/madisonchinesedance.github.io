#!/usr/bin/env python3
"""Unified site management — pages, navigation, and route scanning.

Run interactively:

    python scripts/site-manager.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from site_lib import (
    HEADER_JSON,
    REPO_ROOT,
    SITE_JSON,
    confirm,
    create_page,
    delete_page,
    find_nav_item,
    list_nav_items,
    list_routes,
    load_json,
    prompt,
    prompt_choice,
    rename_folder,
    rename_page,
    write_json,
)


def run_scan() -> None:
    script = Path(__file__).resolve().parent / "scan-pages.py"
    subprocess.run([sys.executable, str(script)], check=False)


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
    from site_lib import CONTENT_ROOT, PAGES_ROOT, slug_to_title

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
    print(f"\nFolder rename complete:")
    for change in result.changes:
        print(f"  - {change}")


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
        print("b. Back to main menu")

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


def main() -> None:
    print("\nSite Manager\n")

    while True:
        print("\nOptions:")
        print("1. List routes")
        print("2. Create page")
        print("3. Delete page")
        print("4. Rename page")
        print("5. Rename folder")
        print("6. Edit navigation")
        print("7. Scan pages (rebuild site.json + nav)")
        print("q. Quit")

        choice = prompt("\nWhat would you like to do?").lower()

        if choice in ("q", "quit", "exit"):
            break
        elif choice == "1":
            cmd_list_routes()
        elif choice == "2":
            cmd_create_page()
        elif choice == "3":
            cmd_delete_page()
        elif choice == "4":
            cmd_rename_page()
        elif choice == "5":
            cmd_rename_folder()
        elif choice == "6":
            cmd_edit_nav()
        elif choice == "7":
            run_scan()
        else:
            print("Invalid choice.")

    print("\nDone.")


if __name__ == "__main__":
    main()
