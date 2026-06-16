#!/usr/bin/env python3
"""One-time migration: sections/items/blocks -> content[] typed blocks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "docs" / "content"

SKIP_FILES = {"site.json", "header.json", "footer.json", "announcements.json"}


def migrate_actions(actions: list | None) -> list[dict]:
    if not actions:
        return []
    buttons = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        button = {"label": action.get("label", "")}
        if action.get("href"):
            button["href"] = action["href"]
        if action.get("route"):
            button["route"] = action["route"]
        if action.get("newTab"):
            button["newTab"] = action["newTab"]
        if action.get("className"):
            button["className"] = action["className"]
        if action.get("ariaLabel"):
            button["ariaLabel"] = action["ariaLabel"]
        if action.get("style"):
            button["style"] = action["style"]
        if button.get("label"):
            buttons.append(button)
    return buttons


def item_to_grid_card(item: dict) -> dict | None:
    blocks = item.get("blocks") or []
    if len(blocks) == 1 and blocks[0].get("type") == "gallery":
        return {"type": "gallery", "variant": blocks[0].get("variant", "")}

    heading = ""
    body = ""
    buttons: list[dict] = []
    for block in blocks:
        block_type = block.get("type")
        if block_type == "heading":
            heading = block.get("text", "")
        elif block_type == "body":
            body = block.get("text", "")
            buttons = migrate_actions(block.get("actions"))
        elif block_type == "gallery":
            return {"type": "gallery", "variant": block.get("variant", "")}

    if not heading and not body:
        return None

    card: dict = {"heading": heading, "body": body}
    if buttons:
        card["buttons"] = buttons
    return card


def process_single_item(item: dict, is_first_hero: bool) -> tuple[list[dict], bool]:
    blocks = item.get("blocks") or []
    result: list[dict] = []
    pending_heading = ""
    pending_body = ""
    pending_buttons: list[dict] = []

    def flush_text() -> None:
        nonlocal is_first_hero, pending_heading, pending_body, pending_buttons
        if not pending_heading and not pending_body and not pending_buttons:
            return
        block_type = "hero" if is_first_hero else "text"
        entry: dict = {
            "type": block_type,
            "heading": pending_heading,
            "body": pending_body,
        }
        if pending_buttons:
            entry["buttons"] = pending_buttons
        result.append(entry)
        is_first_hero = False
        pending_heading = ""
        pending_body = ""
        pending_buttons = []

    for block in blocks:
        block_type = block.get("type")
        if block_type == "heading":
            flush_text()
            pending_heading = block.get("text", "")
        elif block_type == "body":
            pending_body = block.get("text", "")
            pending_buttons = migrate_actions(block.get("actions"))
            flush_text()
        elif block_type == "gallery":
            flush_text()
            result.append({"type": "gallery", "variant": block.get("variant", "")})
        elif block_type == "zeffyEmbed":
            flush_text()
            zeffy = {"type": "zeffy", "formUrl": block.get("formUrl", "")}
            if block.get("iframeTitle"):
                zeffy["iframeTitle"] = block["iframeTitle"]
            if block.get("iframeSrc"):
                zeffy["iframeSrc"] = block["iframeSrc"]
            result.append(zeffy)

    flush_text()
    return result, is_first_hero


def migrate_sections(sections: list) -> list[dict]:
    content: list[dict] = []
    is_first_hero = True

    for section in sections or []:
        columns = max(1, min(int(section.get("columns") or 1), 4))
        items = section.get("items") or []

        if columns > 1 or len(items) > 1:
            cards = []
            for item in items:
                card = item_to_grid_card(item)
                if card:
                    cards.append(card)
            if cards:
                content.append({"type": "grid", "columns": columns, "cards": cards})
            continue

        if len(items) == 1:
            blocks, is_first_hero = process_single_item(items[0], is_first_hero)
            content.extend(blocks)

    return content


def migrate_page(data: dict) -> dict:
    if "content" in data and "sections" not in data:
        return data

    sections = data.get("sections")
    if not sections:
        migrated = {key: value for key, value in data.items() if key != "sections"}
        migrated.setdefault("content", [])
        return migrated

    migrated = {key: value for key, value in data.items() if key != "sections"}
    migrated["content"] = migrate_sections(sections)
    return migrated


def page_json_files() -> list[Path]:
    site = json.loads((CONTENT_DIR / "site.json").read_text(encoding="utf-8"))
    paths = []
    for route in site.get("routes", {}).values():
        rel = route.get("content", "").replace("\\", "/")
        if rel:
            paths.append(CONTENT_DIR / rel)
    return sorted(set(paths))


def main() -> int:
    updated = 0
    for path in page_json_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        migrated = migrate_page(data)
        if migrated == data:
            continue
        path.write_text(
            json.dumps(migrated, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        updated += 1
        print(f"Migrated {path.relative_to(ROOT)}")

    remaining = []
    for path in page_json_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        if "sections" in data:
            remaining.append(str(path.relative_to(ROOT)))

    if remaining:
        print("WARNING: sections still present in:", ", ".join(remaining))
        return 1

    print(f"\nDone. Migrated {updated} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
