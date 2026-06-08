"""Manage page files — rename routes, move pages between folders.

Run it with:

    python scripts/manage-pages.py

It shows a menu with options. Follow the prompts.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_routes(site: dict) -> None:
    routes = site.get("routes", {})
    for route_id, info in sorted(routes.items()):
        print(f"  {route_id} → {info['page']} (content: {info['content']})")


def find_route(site: dict, route_id: str) -> tuple[str, dict] | None:
    routes = site.get("routes", {})
    if route_id in routes:
        return route_id, routes[route_id]
    return None


def prompt(message: str) -> str:
    return input(f"{message}: ").strip()


def confirm(message: str) -> bool:
    answer = input(f"{message} (y/n): ").strip().lower()
    return answer in {"y", "yes"}


def main() -> None:
    root = repo_root()
    content_root = root / "content"
    pages_root = root / "pages"
    site_path = content_root / "site.json"
    site = load_json(site_path)

    print("\nPage Manager\n")

    while True:
        print("\nOptions:")
        print("1. List all routes")
        print("2. Rename a route (updates HTML, JSON, and site.json)")
        print("3. Move a page to a different folder")
        print("q. Quit")

        choice = prompt("\nWhat would you like to do?").lower()

        if choice in ("q", "quit", "exit"):
            break

        elif choice == "1":
            print("\nCurrent routes:")
            list_routes(site)

        elif choice == "2":
            route_id = prompt("Route ID to rename (e.g., tickets)")
            result = find_route(site, route_id)
            if not result:
                print(f"Route '{route_id}' not found.")
                continue

            old_route_id, route_info = result
            new_route_id = prompt("New route ID")
            if not new_route_id:
                print("No new route ID provided.")
                continue

            # Update site.json
            routes = site["routes"]
            routes[new_route_id] = routes.pop(old_route_id)
            routes[new_route_id]["page"] = routes[new_route_id]["page"].replace(
                f"{old_route_id}.html", f"{new_route_id}.html"
            )
            routes[new_route_id]["content"] = routes[new_route_id]["content"].replace(
                f"{old_route_id}.json", f"{new_route_id}.json"
            )
            write_json(site_path, site)

            # Rename HTML file
            old_html = pages_root / route_info["page"]
            new_html = pages_root / routes[new_route_id]["page"]
            if old_html.exists():
                new_html.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_html), str(new_html))
                print(f"Moved HTML: {old_html.relative_to(root)} → {new_html.relative_to(root)}")

            # Rename JSON file
            old_json = content_root / route_info["content"]
            new_json = content_root / routes[new_route_id]["content"]
            if old_json.exists():
                new_json.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_json), str(new_json))
                print(f"Moved JSON: {old_json.relative_to(root)} → {new_json.relative_to(root)}")

            print(f"Renamed route: {old_route_id} → {new_route_id}")

        elif choice == "3":
            route_id = prompt("Route ID to move (e.g., programs/beginner-dancers)")
            result = find_route(site, route_id)
            if not result:
                print(f"Route '{route_id}' not found.")
                continue

            old_route_id, route_info = result
            new_folder = prompt("New folder (e.g., programs, get-involved, or leave empty for root)")
            new_slug = f"{new_folder}/{route_id}" if new_folder else route_id

            # Update site.json
            routes = site["routes"]
            routes[old_route_id]["page"] = f"{new_slug}.html"
            routes[old_route_id]["content"] = f"{new_slug}.json"
            write_json(site_path, site)

            # Move HTML file
            old_html = pages_root / route_info["page"]
            new_html = pages_root / f"{new_slug}.html"
            if old_html.exists():
                new_html.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_html), str(new_html))
                print(f"Moved HTML: {old_html.relative_to(root)} → {new_html.relative_to(root)}")

            # Move JSON file
            old_json = content_root / route_info["content"]
            new_json = content_root / f"{new_slug}.json"
            if old_json.exists():
                new_json.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_json), str(new_json))
                print(f"Moved JSON: {old_json.relative_to(root)} → {new_json.relative_to(root)}")

            print(f"Moved page to: {new_slug}")

        else:
            print("Invalid choice. Try again.")

    print("\nDone.")


if __name__ == "__main__":
    main()