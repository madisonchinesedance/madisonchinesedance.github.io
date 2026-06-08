"""Manage site navigation — rename labels, move items, or reorder menus.

Run it with:

    python scripts/manage-nav.py

It shows a menu with options. Follow the prompts.
"""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_nav_items(nav: list) -> None:
    for idx, item in enumerate(nav, 1):
        if "route" in item:
            print(f"  {idx}. {item.get('label', item['route'])} → @{item['route']}")
        elif "items" in item:
            print(f"  {idx}. ▼ {item.get('label', '(group)')}")
            for sub in item.get("items", []):
                route = sub.get("route", "?")
                print(f"      – {sub.get('label', route)} → @{route}")


def find_nav_item(nav: list, label: str) -> tuple[dict, list, int] | None:
    """Return (item, parent_list, index) for a nav item matching label."""
    for i, item in enumerate(nav):
        if item.get("label") == label:
            return item, nav, i
        if "items" in item:
            for j, sub in enumerate(item["items"]):
                if sub.get("label") == label:
                    return sub, item["items"], j
    return None


def prompt(message: str) -> str:
    return input(f"{message}: ").strip()


def prompt_choice(message: str, options: list[str]) -> int | None:
    print(f"\n{message}")
    for idx, opt in enumerate(options, 1):
        print(f"  {idx}. {opt}")
    choice = input("Enter number (or press enter to cancel): ").strip()
    if not choice:
        return None
    try:
        return int(choice)
    except ValueError:
        return None


def main() -> None:
    root = repo_root()
    header_path = root / "content" / "header.json"
    header = load_json(header_path)
    nav = header.setdefault("nav", [])

    print("\nNavigation Manager\n")

    while True:
        print("\nOptions:")
        print("1. List navigation")
        print("2. Rename a nav item")
        print("3. Move a nav item (top-level ↔ dropdown)")
        print("4. Reorder a dropdown menu")
        print("5. Remove a nav item")
        print("q. Quit")

        choice = prompt("\nWhat would you like to do?").lower()

        if choice in ("q", "quit", "exit"):
            break

        elif choice == "1":
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
                write_json(header_path, header)
                print(f"Renamed to '{new_label}'.")

        elif choice == "3":
            label = prompt("Label of the nav item to move")
            result = find_nav_item(nav, label)
            if not result:
                print(f"Item '{label}' not found.")
                continue
            item, parent_list, idx = result

            # Remove from current position
            parent_list.pop(idx)

            # Choose destination
            options = ["Top-level menu"]
            for nav_item in nav:
                if "items" in nav_item:
                    options.append(f"Dropdown: {nav_item.get('label', '(group)')}")

            dest = prompt_choice("Where should this item go?", options)
            if dest is None:
                continue

            if dest == 1:
                nav.append(item)
            else:
                dropdown_idx = dest - 2
                dropdown = nav[dropdown_idx]
                dropdown.setdefault("items", []).append(item)

            write_json(header_path, header)
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
                new_items = [items[i] for i in new_order]
                dropdown["items"] = new_items
                write_json(header_path, header)
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
            write_json(header_path, header)
            print("Item removed.")

        else:
            print("Invalid choice. Try again.")

    print("\nDone.")


if __name__ == "__main__":
    main()