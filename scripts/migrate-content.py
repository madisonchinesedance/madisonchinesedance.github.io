#!/usr/bin/env python3
"""One-time migration: docs/content JSON -> 11ty Markdown + YAML."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ROOT / "docs" / "content"
SRC = ROOT / "src"
ROUTES: dict[str, dict] = {}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def route_href(route_id: str) -> str:
    route = ROUTES.get(route_id)
    if not route:
        return "#"
    href = route.get("href", "")
    return f"/{href.lstrip('/')}" if href else "#"


def resolve_link(link: dict) -> tuple[str, str]:
    if link.get("route"):
        return route_href(link["route"]), link.get("label", link["route"])
    href = link.get("href", "#")
    return href, link.get("label", href)


def blocks_to_markdown(sections: list) -> str:
    parts: list[str] = []
    for section in sections or []:
        for item in section.get("items", []):
            for block in item.get("blocks", []):
                btype = block.get("type")
                if btype == "heading":
                    level = 1
                    token = str(block.get("fontSize", ""))
                    match = re.match(r"heading-(\d)", token)
                    if match:
                        level = int(match.group(1))
                    level = max(1, min(level, 6))
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(f"{'#' * level} {text}\n")
                elif btype == "body":
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(f"{text}\n")
                    for action in block.get("actions", []):
                        href, label = resolve_link(action)
                        parts.append(f"\n[{label}]({href})\n")
                elif btype == "zeffyEmbed":
                    pass  # handled via frontmatter
    return "\n".join(parts).strip()


def convert_nav_entry(entry: dict) -> dict:
    if entry.get("items"):
        return {
            "label": entry["label"],
            "items": [convert_nav_entry(i) for i in entry["items"]],
        }
    if entry.get("route"):
        return {
            "label": entry.get("label", entry["route"]),
            "href": route_href(entry["route"]),
            "routeId": entry["route"],
        }
    return entry


def convert_footer_link(link: dict) -> dict:
    if link.get("route"):
        return {
            "label": link.get("label", link["route"]),
            "href": route_href(link["route"]),
        }
    return {"label": link.get("label", ""), "href": link.get("href", "")}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, frontmatter: dict, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = json.dumps(frontmatter, indent=2, ensure_ascii=False)
    # Use YAML-style frontmatter for Pages CMS compatibility
    import yaml
    fm = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm}---\n\n{body}\n", encoding="utf-8")


def migrate_globals() -> None:
    header = load_json(LEGACY / "header.json")
    footer = load_json(LEGACY / "footer.json")
    announcements = load_json(LEGACY / "announcements.json")
    index = load_json(LEGACY / "index.json")
    gallery = load_json(LEGACY / "gallery.json")

    nav = {
        "logo": {
            **header.get("logo", {}),
            "href": route_href(header.get("logo", {}).get("route", "home")),
        },
        "navigationLabel": header.get("navigationLabel", "Primary navigation"),
        "menuToggleOpenLabel": header.get("menuToggleOpenLabel", "Open navigation"),
        "menuToggleCloseLabel": header.get("menuToggleCloseLabel", "Close navigation"),
        "nav": [convert_nav_entry(e) for e in header.get("nav", [])],
        "actions": [
            {
                "label": a.get("label"),
                "href": route_href(a["route"]),
                "routeId": a["route"],
                "ariaLabel": a.get("ariaLabel", a.get("label")),
            }
            for a in header.get("actions", [])
            if a.get("route")
        ],
    }

    footer_data = {
        "brand": {
            **footer.get("brand", {}),
            "href": route_href(footer.get("brand", {}).get("route", "home")),
        },
        "columns": [
            {
                "heading": col.get("heading", ""),
                "links": [convert_footer_link(l) for l in col.get("links", [])],
            }
            for col in footer.get("columns", [])
        ],
        "operations": footer.get("operations", []),
        "copyright": footer.get("copyright", ""),
    }

    ann_data = announcements.copy()
    for ann in ann_data.get("announcements", []):
        for action in ann.get("actions", []):
            if action.get("route"):
                action["href"] = route_href(action["route"])

    homepage = {
        "title": index.get("pageTitle", "Madison Chinese Dance Academy | Home"),
        "description": index.get("metaDescription", ""),
        "hero": {
            "heading": "Madison Chinese Dance Academy",
            "body": "We dance to integrate Eastern and Western arts and cultures for a more harmonious world.",
        },
        "runnerImages": index.get("homepageRunnerImages", []),
        "runnerTallImages": index.get("homepageRunnerTallImages", []),
        "runnerWideImages": index.get("homepageRunnerWideImages", []),
        "stats": [
            {"heading": "1987", "body": "Founded as a nonprofit dance academy over 30 years ago. Generations of students have trained, performed, and shared Chinese dance with the Madison community."},
            {"heading": "Splendid China", "body": "Annual showcase at the Robert E. Parilla Performing Arts Center — where community artistry meets the stage. Each year brings new choreography, costumes, and traditions to life."},
            {"heading": "Ages 3 to 18+", "body": "Classes for beginner dancers through advanced students and beyond. Programs grow with each student from first steps to senior choreography projects."},
        ],
        "cards": [
            {"heading": "Classes", "body": "Beginner through advanced dance instruction for students of all ages.", "href": route_href("beginner-dancers"), "label": "Start with beginner dancers"},
            {"heading": "Splendid China", "body": "Our annual concert brings traditional and contemporary Chinese dance to the stage.", "href": route_href("splendid-china-2026"), "label": "See Splendid China 2026"},
            {"heading": "Gallery", "body": "Browse moments from performances, community programs, and academy events.", "href": route_href("gallery"), "label": "Open gallery"},
        ],
        "story": {
            "english": {"heading": "Our Story", "body": ""},
            "chinese": {"heading": "我們的故事", "body": ""},
        },
        "ctas": [
            {"heading": "Attend a performance", "body": "Get details for Splendid China 2026 and purchase tickets online.", "href": route_href("tickets"), "label": "Purchase tickets"},
            {"heading": "Support the academy", "body": "Help fund classes, costumes, rehearsal space, and community outreach.", "href": route_href("donate"), "label": "Donate"},
            {"heading": "Get in touch", "body": "Ask about classes, performances, donations, or community programs.", "href": "mailto:contact@madisonchinesedance.org", "label": "Contact us"},
        ],
    }

    for section in index.get("sections", []):
        for item in section.get("items", []):
            for block in item.get("blocks", []):
                if block.get("type") == "heading" and block.get("text") == "Our Story":
                    pass
                if block.get("type") == "body":
                    text = block.get("text", "")
                    if "Madison Chinese Dance Academy was founded" in text:
                        homepage["story"]["english"]["body"] = text
                    if "取名「陌地生」" in text:
                        homepage["story"]["chinese"]["body"] = text

    gallery_data = {
        "featuredImages": gallery.get("galleryImages", []),
        "groups": gallery.get("galleryGroups", []),
    }

    write_json(SRC / "_data" / "mcdaNav.json", nav)
    write_json(SRC / "_data" / "footer.json", footer_data)
    write_json(SRC / "_data" / "announcements.json", ann_data)
    write_json(SRC / "_data" / "homepage.json", homepage)
    write_json(SRC / "_data" / "gallery.json", gallery_data)


def migrate_pages() -> None:
    splendid_dir = SRC / "splendid-china"
    pages_dir = SRC / "content" / "pages"

    skip_routes = {"home"}
    zeffy_pages = {"tickets", "donate"}

    for route_id, info in ROUTES.items():
        if route_id in skip_routes:
            continue

        content_path = LEGACY / str(info["content"]).replace("\\", "/")
        if not content_path.exists():
            print(f"Skip missing: {content_path}")
            continue

        data = load_json(content_path)
        href = f"/{info['href'].lstrip('/')}"
        title = data.get("pageTitle", route_id)
        description = data.get("metaDescription", "")

        if route_id.startswith("splendid-china-"):
            year = route_id.replace("splendid-china-", "")
            body = blocks_to_markdown(data.get("sections", []))
            zeffy = None
            for section in data.get("sections", []):
                for item in section.get("items", []):
                    for block in item.get("blocks", []):
                        if block.get("type") == "zeffyEmbed":
                            zeffy = block.get("formUrl")
            fm = {
                "layout": "layouts/splendid-china.njk",
                "permalink": href,
                "title": title,
                "description": description,
                "year": year,
                "routeId": route_id,
                "galleryImages": data.get("galleryImages", []),
            }
            if zeffy:
                fm["zeffyFormUrl"] = zeffy
            write_md(splendid_dir / f"{year}.md", fm, body)
            continue

        layout = "layouts/zeffy.njk" if route_id in zeffy_pages else "layouts/page.njk"
        body = blocks_to_markdown(data.get("sections", []))

        fm: dict = {
            "layout": layout,
            "permalink": href,
            "title": title,
            "description": description,
            "routeId": route_id,
        }

        if route_id == "gallery":
            fm["layout"] = "layouts/gallery.njk"
            fm["featuredImages"] = data.get("galleryImages", [])

        for section in data.get("sections", []):
            for item in section.get("items", []):
                for block in item.get("blocks", []):
                    if block.get("type") == "zeffyEmbed":
                        fm["zeffyFormUrl"] = block.get("formUrl", "")
                        fm["zeffyIframeTitle"] = block.get("iframeTitle", "Embedded form powered by Zeffy")

        rel_path = info["page"]
        if rel_path == "index.html":
            out = pages_dir / "index.md"
        else:
            out = pages_dir / Path(rel_path.replace(".html", ".md"))

        write_md(out, fm, body)


def main() -> None:
    global ROUTES
    site = load_json(LEGACY / "site.json")
    ROUTES = site.get("routes", {})

    migrate_globals()
    migrate_pages()
    print(f"Migration complete. Output: {SRC}")


if __name__ == "__main__":
    main()
