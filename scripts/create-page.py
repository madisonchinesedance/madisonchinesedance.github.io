"""Create a new page and optionally add it to navigation.

This script is intentionally interactive to avoid memorizing command-line flags.
Run it with:

    python scripts/create-page.py

The script will prompt you for:
- Page title
- Route slug (e.g., about, programs/advanced-dancers)
- Whether to add it to the main navigation
- Which dropdown to place it under (optional)
"""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prompt(message: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ").strip()
    return value or default


def confirm(message: str) -> bool:
    answer = input(f"{message} (y/n): ").strip().lower()
    return answer in {"y", "yes"}


def route_from_slug(slug: str) -> dict:
    slug = slug.strip().strip("/")
    if not slug:
        raise ValueError("Route slug cannot be empty")

    parts = slug.split("/")
    page = parts[-1] + ".html"
    content = parts[-1] + ".json"

    if len(parts) == 1:
        href = page
        page_path = page
        content_path = content
    else:
        folder = "/".join(parts[:-1])
        href = f"pages/{folder}/{page}"
        page_path = f"{folder}/{page}"
        content_path = f"{folder}/{content}"

    return {
        "href": href,
        "page": page_path,
        "content": content_path,
    }


def add_to_nav(header: dict, route_id: str, label: str, parent: str = "") -> None:
    nav = header.setdefault("nav", [])

    # If no parent specified, add to top-level nav
    if not parent:
        nav.append({"route": route_id, "label": label})
        return

    # Find or create the parent dropdown
    for item in nav:
        if item.get("label") == parent:
            item.setdefault("items", []).append({"route": route_id, "label": label})
            return

    nav.append({"label": parent, "items": [{"route": route_id, "label": label}]})


def main() -> None:
    root = repo_root()
    content_root = root / "content"
    pages_root = root / "pages"

    print("Create a new page\n")

    title = prompt("Page title", "New Page")
    slug = prompt("Route slug (e.g., about, programs/advanced-dancers)")

    if not slug:
        print("No route slug provided. Exiting.")
        return

    route = route_from_slug(slug)
    route_id = slug.strip("/").split("/")[-1]

    # Create HTML file
    html_path = pages_root / route["page"]
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width,initial-scale=1" />
	<title data-json="pageTitle">{title} | Madison Chinese Dance Academy</title>
	<meta name="description" content="{title} page for Madison Chinese Dance Academy." data-json="metaDescription" data-json-attr="content" />
	<link rel="stylesheet" href="/style.css" />
	<script defer src="/app.js"></script>
</head>
<body data-route="{route_id}">
	<a class="skip-link" href="#main">Skip to main content</a>

	<div data-site-header></div>

	<main id="main" tabindex="-1" class="site-main" data-page-blocks></main>

	<div data-site-footer></div>
</body>
</html>
""",
        encoding="utf-8",
    )

    # Create JSON file
    json_path = content_root / route["content"]
    write_json(
        json_path,
        {
            "pageTitle": f"{title} | Madison Chinese Dance Academy",
            "metaDescription": f"{title} page for Madison Chinese Dance Academy.",
            "sections": [
                {
                    "columns": 1,
                    "items": [
                        {
                            "blocks": [
                                {
                                    "type": "heading",
                                    "level": 1,
                                    "id": f"{slug.replace('/', '-')}-heading",
                                    "text": title,
                                },
                                {
                                    "type": "body",
                                    "text": "Add your page content here.",
                                },
                            ],
                        }
                    ],
                }
            ],
        },
    )

    # Update site.json
    site = load_json(content_root / "site.json")
    routes = site.setdefault("routes", {})
    routes[route_id] = route
    write_json(content_root / "site.json", site)

    # Optionally add to nav
    if confirm("Add this page to the main navigation?"):
        header = load_json(content_root / "header.json")
        parent = prompt("Dropdown name (press enter for top-level)", "")
        add_to_nav(header, route_id, title, parent)
        write_json(content_root / "header.json", header)
        print("Updated header.json")

    print(f"\nCreated page: {html_path.relative_to(root)}")
    print(f"Created content: {json_path.relative_to(root)}")
    print("Updated site.json")


if __name__ == "__main__":
    main()
