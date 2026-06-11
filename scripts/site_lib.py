"""Shared paths and helpers for site management scripts."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"
CONTENT_ROOT = DOCS_ROOT / "content"
PAGES_ROOT = DOCS_ROOT / "pages"
SITE_JSON = CONTENT_ROOT / "site.json"
HEADER_JSON = CONTENT_ROOT / "header.json"
FOOTER_JSON = CONTENT_ROOT / "footer.json"
ANNOUNCEMENTS_JSON = CONTENT_ROOT / "announcements.json"
INDEX_HTML = DOCS_ROOT / "index.html"

TITLE_SUFFIX = " | Madison Chinese Dance Academy"

_TITLE_CASE_MINOR_WORDS = {
    "a", "an", "the", "and", "but", "or", "for", "nor",
    "on", "at", "to", "from", "by", "in", "of", "vs", "via",
}


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


def slug_to_title(slug: str) -> str:
    words = slug.replace("_", "-").split("-")
    if not words:
        return slug
    result = []
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word.lower() not in _TITLE_CASE_MINOR_WORDS:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return " ".join(result)


def route_from_slug(slug: str) -> dict:
    slug = slug.strip().strip("/")
    if not slug:
        raise ValueError("Route slug cannot be empty")

    parts = slug.split("/")
    page = parts[-1] + ".html"
    content = parts[-1] + ".json"

    if len(parts) == 1:
        href = f"pages/{page}"
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


def slug_from_path(file_path: str, old_slug: str, new_slug: str) -> str:
    return file_path.replace(f"{old_slug}.", f"{new_slug}.")


def extract_data_route(html_path: Path) -> str | None:
    if not html_path.is_file():
        return None
    html = html_path.read_text(encoding="utf-8")
    match = re.search(r'<body[^>]*\sdata-route\s*=\s*"([^"]+)"', html, re.IGNORECASE)
    return match.group(1) if match else None


def page_rel_to_content_rel(page_rel: str) -> str:
    return str(Path(page_rel).with_suffix(".json"))


def nav_label_for_route(route_id: str, content_rel: str) -> str:
    content_path = CONTENT_ROOT / content_rel
    if content_path.is_file():
        data = load_json(content_path)
        title = data.get("pageTitle", "")
        if isinstance(title, str) and title:
            if TITLE_SUFFIX in title:
                title = title.split(TITLE_SUFFIX)[0].strip()
            return title
    return slug_to_title(route_id)


def list_routes(site: dict) -> list[tuple[str, dict]]:
    return sorted(site.get("routes", {}).items())


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
    for i, item in enumerate(nav):
        if item.get("label") == label:
            return item, nav, i
        if "items" in item:
            for j, sub in enumerate(item["items"]):
                if sub.get("label") == label:
                    return sub, item["items"], j
    return None


def remove_route_from_nav(nav: list, route_id: str) -> bool:
    changed = False
    i = 0
    while i < len(nav):
        item = nav[i]
        if item.get("route") == route_id:
            nav.pop(i)
            changed = True
            continue
        if "items" in item:
            before = len(item["items"])
            item["items"] = [sub for sub in item["items"] if sub.get("route") != route_id]
            if len(item["items"]) < before:
                changed = True
            if not item["items"]:
                nav.pop(i)
                changed = True
                continue
        i += 1
    return changed


def remove_route_from_actions(actions: list, route_id: str) -> bool:
    before = len(actions)
    actions[:] = [a for a in actions if a.get("route") != route_id]
    return len(actions) < before


def remove_route_from_footer(footer: dict, route_id: str) -> bool:
    changed = False
    for column in footer.get("columns", []):
        links = column.get("links", [])
        before = len(links)
        column["links"] = [link for link in links if link.get("route") != route_id]
        if len(column["links"]) < before:
            changed = True
        if not column["links"] and column.get("heading"):
            column["heading"] = ""
    return changed


def remove_route_from_announcements(announcements: dict, route_id: str) -> bool:
    highlights = announcements.get("highlights", {})
    changed = False
    for key in ("navRoutes", "actionRoutes"):
        routes = highlights.get(key, [])
        if route_id in routes:
            highlights[key] = [r for r in routes if r != route_id]
            changed = True
    return changed


def update_route_refs_in_obj(obj: dict | list, old_id: str, new_id: str) -> bool:
    new_title = slug_to_title(new_id)
    changed = False
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "route" and value == old_id:
                obj[key] = new_id
                changed = True
            elif isinstance(value, (dict, list)):
                if update_route_refs_in_obj(value, old_id, new_id):
                    changed = True
        if "label" in obj and isinstance(obj["label"], str):
            old_title = slug_to_title(old_id)
            if obj["label"] == old_title:
                obj["label"] = new_title
                changed = True
        if "heading" in obj and isinstance(obj["heading"], str):
            old_title = slug_to_title(old_id)
            if obj["heading"] == old_title:
                obj["heading"] = new_title
                changed = True
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                if update_route_refs_in_obj(item, old_id, new_id):
                    changed = True
    return changed


class RenameResult:
    def __init__(self, old_id: str, new_id: str):
        self.old_id = old_id
        self.new_id = new_id
        self.changes: list[str] = []

    def log(self, description: str) -> None:
        self.changes.append(description)


def rename_page(old_id: str, new_id: str, *, force: bool = False) -> RenameResult:
    result = RenameResult(old_id, new_id)

    site = load_json(SITE_JSON)
    routes = site.get("routes", {})

    if old_id not in routes:
        print(f"Error: route '{old_id}' not found in site.json.")
        sys.exit(1)

    if new_id in routes and not force:
        print(f"Error: route '{new_id}' already exists in site.json.")
        sys.exit(1)

    route_info = routes[old_id]
    old_html_rel = route_info["page"]
    old_json_rel = route_info["content"]
    new_html_rel = slug_from_path(old_html_rel, old_id, new_id)
    new_json_rel = slug_from_path(old_json_rel, old_id, new_id)

    old_html = PAGES_ROOT / old_html_rel
    new_html = PAGES_ROOT / new_html_rel
    old_json = CONTENT_ROOT / old_json_rel
    new_json = CONTENT_ROOT / new_json_rel

    if old_html.exists():
        new_html.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_html), str(new_html))
        result.log(f"Renamed HTML: {old_html_rel} → {new_html_rel}")

    if old_json.exists():
        new_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_json), str(new_json))
        result.log(f"Renamed JSON: {old_json_rel} → {new_json_rel}")

    route_entry = routes.pop(old_id)
    route_entry["page"] = new_html_rel
    route_entry["content"] = new_json_rel
    if "href" in route_entry:
        route_entry["href"] = slug_from_path(route_entry["href"], old_id, new_id)
    routes[new_id] = route_entry
    write_json(SITE_JSON, site)
    result.log(f"Updated site.json route: {old_id} → {new_id}")

    new_title = slug_to_title(new_id)

    if new_html.exists():
        html = new_html.read_text(encoding="utf-8")
        html_new = re.sub(
            r'(data-route\s*=\s*")' + re.escape(old_id) + r'(")',
            rf'\g<1>{new_id}\2',
            html,
        )
        html_new = html_new.replace(old_id, new_title)
        if html_new != html:
            new_html.write_text(html_new, encoding="utf-8")
            result.log(f"Updated HTML content for '{new_id}'")

    if new_json.exists():
        page_content = load_json(new_json)
        if "pageTitle" in page_content and old_id in page_content["pageTitle"]:
            page_content["pageTitle"] = page_content["pageTitle"].replace(old_id, new_title)
            result.log(f"Updated pageTitle in {new_json_rel}")
        if "metaDescription" in page_content and old_id in page_content["metaDescription"]:
            page_content["metaDescription"] = page_content["metaDescription"].replace(
                old_id, new_title
            )
            result.log(f"Updated metaDescription in {new_json_rel}")
        write_json(new_json, page_content)

    if HEADER_JSON.exists():
        header = load_json(HEADER_JSON)
        header_updated = update_route_refs_in_obj(header, old_id, new_id)
        nav = header.get("nav", [])
        for group in nav:
            if "items" not in group:
                continue
            group_routes = {item.get("route") for item in group["items"] if "route" in item}
            if old_id in group_routes or new_id in group_routes:
                old_title = slug_to_title(old_id)
                if group.get("label", "") == old_title:
                    group["label"] = new_title
                    header_updated = True
                    result.log(f"Updated nav group label: '{old_title}' -> '{new_title}'")
        if header_updated:
            write_json(HEADER_JSON, header)
            result.log("Updated route references in header.json")

    if FOOTER_JSON.exists():
        footer = load_json(FOOTER_JSON)
        footer_updated = update_route_refs_in_obj(footer, old_id, new_id)
        for column in footer.get("columns", []):
            col_routes = {link.get("route") for link in column.get("links", []) if "route" in link}
            if old_id in col_routes or new_id in col_routes:
                old_title = slug_to_title(old_id)
                if column.get("heading", "") == old_title:
                    column["heading"] = new_title
                    footer_updated = True
                    result.log(f"Updated footer heading: '{old_title}' -> '{new_title}'")
        if footer_updated:
            write_json(FOOTER_JSON, footer)
            result.log("Updated route references in footer.json")

    skip_json = {SITE_JSON, HEADER_JSON, FOOTER_JSON, new_json}
    for json_file in CONTENT_ROOT.rglob("*.json"):
        if json_file in skip_json:
            continue
        data = load_json(json_file)
        if update_route_refs_in_obj(data, old_id, new_id):
            write_json(json_file, data)
            result.log(f"Updated cross-references in {json_file.relative_to(REPO_ROOT)}")

    for html_file in PAGES_ROOT.rglob("*.html"):
        if html_file == new_html:
            continue
        html = html_file.read_text(encoding="utf-8")
        pattern = r'(data-route\s*=\s*")' + re.escape(old_id) + r'(")'
        new_html_text, count = re.subn(pattern, rf'\g<1>{new_id}\2', html)
        if count > 0:
            html_file.write_text(new_html_text, encoding="utf-8")
            result.log(f"Updated data-route in {html_file.relative_to(REPO_ROOT)}")

    return result


class FolderRenameResult:
    def __init__(self, old_folder: str, new_folder: str):
        self.old_folder = old_folder
        self.new_folder = new_folder
        self.changes: list[str] = []

    def log(self, description: str) -> None:
        self.changes.append(description)


def _routes_in_folder(site: dict, folder: str) -> set[str]:
    route_ids = set()
    for route_id, info in site.get("routes", {}).items():
        page = info.get("page", "")
        content = info.get("content", "")
        if page.startswith(f"{folder}/") or content.startswith(f"{folder}/"):
            route_ids.add(route_id)
    return route_ids


def rename_folder(old_folder: str, new_folder: str, *, force: bool = False) -> FolderRenameResult:
    result = FolderRenameResult(old_folder, new_folder)

    old_pages_dir = PAGES_ROOT / old_folder
    new_pages_dir = PAGES_ROOT / new_folder
    old_content_dir = CONTENT_ROOT / old_folder
    new_content_dir = CONTENT_ROOT / new_folder

    if not old_pages_dir.is_dir() and not old_content_dir.is_dir():
        print(f"Error: folder '{old_folder}' not found under pages/ or content/")
        sys.exit(1)

    if (new_pages_dir.exists() or new_content_dir.exists()) and not force:
        print(f"Error: destination folder '{new_folder}' already exists.")
        sys.exit(1)

    if old_pages_dir.is_dir():
        new_pages_dir.mkdir(parents=True, exist_ok=True)
        for file in old_pages_dir.iterdir():
            if file.is_file():
                dest = new_pages_dir / file.name
                shutil.move(str(file), str(dest))
                result.log(f"Moved page: {old_folder}/{file.name} -> {new_folder}/{file.name}")
        try:
            old_pages_dir.rmdir()
        except OSError:
            pass

    if old_content_dir.is_dir():
        new_content_dir.mkdir(parents=True, exist_ok=True)
        for file in old_content_dir.iterdir():
            if file.is_file():
                dest = new_content_dir / file.name
                shutil.move(str(file), str(dest))
                result.log(f"Moved content: {old_folder}/{file.name} -> {new_folder}/{file.name}")
        try:
            old_content_dir.rmdir()
        except OSError:
            pass

    site = load_json(SITE_JSON)
    routes = site.get("routes", {})
    updated_count = 0
    for route_info in routes.values():
        updated = False
        for field in ("href", "page", "content"):
            if field in route_info and f"{old_folder}/" in route_info[field]:
                route_info[field] = route_info[field].replace(f"{old_folder}/", f"{new_folder}/")
                updated = True
        if updated:
            updated_count += 1

    if updated_count:
        write_json(SITE_JSON, site)
        result.log(f"Updated {updated_count} route(s) in site.json")

    affected_routes = _routes_in_folder(site, new_folder)
    new_label = slug_to_title(new_folder)

    if HEADER_JSON.exists():
        header = load_json(HEADER_JSON)
        nav = header.get("nav", [])
        header_updated = False
        for group in nav:
            if "items" not in group:
                continue
            group_routes = {item.get("route") for item in group["items"] if "route" in item}
            if group_routes and group_routes.issubset(affected_routes):
                old_label = group.get("label", "")
                if old_label and old_label != new_label:
                    group["label"] = new_label
                    header_updated = True
                    result.log(f"Updated nav label: '{old_label}' -> '{new_label}'")
        if header_updated:
            write_json(HEADER_JSON, header)

    if FOOTER_JSON.exists():
        footer = load_json(FOOTER_JSON)
        footer_updated = False
        for column in footer.get("columns", []):
            col_routes = {link.get("route") for link in column.get("links", []) if "route" in link}
            if col_routes and col_routes.issubset(affected_routes):
                old_heading = column.get("heading", "")
                if old_heading and old_heading != new_label:
                    column["heading"] = new_label
                    footer_updated = True
                    result.log(f"Updated footer heading: '{old_heading}' -> '{new_label}'")
        if footer_updated:
            write_json(FOOTER_JSON, footer)

    if not result.changes:
        result.log("No changes needed.")

    return result


def delete_page(route_id: str) -> list[str]:
    changes: list[str] = []
    site = load_json(SITE_JSON)
    routes = site.get("routes", {})

    if route_id not in routes:
        print(f"Error: route '{route_id}' not found.")
        sys.exit(1)

    if route_id == "home":
        print("Error: cannot delete the home route.")
        sys.exit(1)

    info = routes[route_id]
    html_path = PAGES_ROOT / info.get("page", "")
    json_path = CONTENT_ROOT / info.get("content", "")

    if html_path.is_file():
        html_path.unlink()
        changes.append(f"Deleted HTML: {html_path.relative_to(REPO_ROOT)}")
    if json_path.is_file():
        json_path.unlink()
        changes.append(f"Deleted JSON: {json_path.relative_to(REPO_ROOT)}")

    del routes[route_id]
    write_json(SITE_JSON, site)
    changes.append(f"Removed route '{route_id}' from site.json")

    if HEADER_JSON.exists():
        header = load_json(HEADER_JSON)
        nav_changed = remove_route_from_nav(header.get("nav", []), route_id)
        actions_changed = remove_route_from_actions(header.get("actions", []), route_id)
        if nav_changed or actions_changed:
            write_json(HEADER_JSON, header)
            changes.append("Removed route from header.json")

    if FOOTER_JSON.exists():
        footer = load_json(FOOTER_JSON)
        if remove_route_from_footer(footer, route_id):
            write_json(FOOTER_JSON, footer)
            changes.append("Removed route from footer.json")

    if ANNOUNCEMENTS_JSON.exists():
        announcements = load_json(ANNOUNCEMENTS_JSON)
        if remove_route_from_announcements(announcements, route_id):
            write_json(ANNOUNCEMENTS_JSON, announcements)
            changes.append("Removed route from announcements.json")

    return changes


def create_page(title: str, slug: str) -> tuple[Path, Path]:
    route = route_from_slug(slug)
    route_id = slug.strip("/").split("/")[-1]

    html_path = PAGES_ROOT / route["page"]
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

    json_path = CONTENT_ROOT / route["content"]
    write_json(
        json_path,
        {
            "pageTitle": f"{title}{TITLE_SUFFIX}",
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

    site = load_json(SITE_JSON)
    site.setdefault("routes", {})[route_id] = route
    write_json(SITE_JSON, site)

    return html_path, json_path
