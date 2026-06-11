"""Shared paths and helpers for site management scripts."""

from __future__ import annotations

import json
import re
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


def prompt_multiline(message: str, current: str = "") -> str:
    """Read multi-line text; end input with a blank line."""
    if current:
        print(f"\n{message}")
        print("(Current value shown; press Enter on first line to keep, or type new text)")
        print("---")
        for line in current.split("\n"):
            print(line)
        print("---")
    else:
        print(f"\n{message}")
        print("(Enter text; finish with a blank line)")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line and not lines:
            return current
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


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


def route_content_path(site: dict, route_id: str) -> Path | None:
    routes = site.get("routes", {})
    info = routes.get(route_id)
    if not info:
        return None
    content_rel = info.get("content", "")
    if not content_rel:
        return None
    return CONTENT_ROOT / content_rel


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


def truncate_preview(text: str, max_len: int = 60) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def first_heading_and_body(section: dict) -> tuple[str, str]:
    for item in section.get("items", []):
        heading = ""
        body = ""
        for block in item.get("blocks", []):
            if block.get("type") == "heading" and not heading:
                heading = block.get("text", "")
            elif block.get("type") == "body" and not body:
                body = block.get("text", "")
            if heading and body:
                break
        if heading or body:
            return heading, body
    return "", ""


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
