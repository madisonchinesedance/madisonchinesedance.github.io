#!/usr/bin/env python3
"""
Generate ai-context.md from content JSON files.

Reads all JSON files referenced in content/site.json and compiles
their text content into a single markdown file for AI chatbot context.

Usage:
    python scripts/generate-ai-context.py
"""

import json
import os
import re
from pathlib import Path

# Project root is one level up from scripts/
ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
OUTPUT_FILE = ROOT / "ai-context.md"


def load_json(path):
    """Load and return a JSON file as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_html(text):
    """Remove HTML tags but keep the text content. Convert <b>/<strong> to **bold**."""
    if not text:
        return ""
    # Bold tags -> markdown bold
    text = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", text, flags=re.IGNORECASE)
    # Italic tags -> markdown italic
    text = re.sub(r"<(?:i|em)>(.*?)</(?:i|em)>", r"*\1*", text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def extract_actions(actions, routes):
    """Extract action links as markdown list items."""
    lines = []
    for action in actions:
        label = action.get("label", "")
        href = action.get("href", "")
        route = action.get("route", "")
        if route and route in routes:
            href = routes[route].get("href", href)
        if label:
            lines.append(f"- **{label}**" + (f" ({href})" if href else ""))
    return lines


def extract_block_lines(block, routes):
    """Extract text content from a single content block."""
    lines = []
    block_type = block.get("type", "")

    if block_type == "heading":
        level = int(block.get("level", 2))
        text = block.get("text", "")
        if text:
            lines.append("")
            lines.append(f"{'#' * level} {text}")
            lines.append("")
    elif block_type == "body":
        lines.extend(extract_body_lines(block, routes))
    elif block_type == "gallery":
        lines.extend(extract_gallery_lines(block))
    elif block_type == "zeffyEmbed":
        form_url = block.get("formUrl", "")
        if form_url:
            lines.append(f"- Embedded form: {form_url}")
            lines.append("")

    return lines


def extract_legacy_item_lines(item, routes):
    """Extract text content from legacy keyed item objects."""
    lines = []
    for key, value in item.items():
        base_key = re.sub(r"_\d+$", "", key)
        if not isinstance(value, dict):
            continue

        if base_key.startswith("heading") and base_key[-1:].isdigit():
            block = {"type": "heading", "level": int(base_key[-1]), **value}
            lines.extend(extract_block_lines(block, routes))
        elif re.fullmatch(r"statistic\d+", base_key):
            block = {"type": "heading", "level": 2, **value}
            lines.extend(extract_block_lines(block, routes))
        elif base_key == "body":
            lines.extend(extract_block_lines({**value, "type": "body"}, routes))
        elif base_key == "gallery":
            lines.extend(extract_block_lines({**value, "type": "gallery"}, routes))
        elif base_key == "zeffyEmbed":
            lines.extend(extract_block_lines({**value, "type": "zeffyEmbed"}, routes))

    return lines


def extract_text_from_sections(sections, routes):
    """Extract text content from section/item page JSON."""
    lines = []
    for section in sections or []:
        items = section.get("items", [])
        for item in items:
            blocks = item.get("blocks")
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        lines.extend(extract_block_lines(block, routes))
            else:
                lines.extend(extract_legacy_item_lines(item, routes))
    return lines


def extract_body_lines(block, routes):
    """Extract paragraph text and actions from a body object."""
    lines = []
    text = block.get("text", "") or block.get("body", "")
    text = strip_html(text)
    if text:
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                for line in para.split("\n"):
                    lines.append(line.strip())
                lines.append("")

    actions = block.get("actions", [])
    if actions:
        lines.extend(extract_actions(actions, routes))
        lines.append("")

    return lines


def extract_gallery_lines(block):
    """Extract summary text from gallery data."""
    lines = []
    groups = block.get("groups", [])
    images = block.get("images", [])
    if groups:
        for group in groups:
            year = group.get("year", "")
            events = group.get("events", [])
            for event in events:
                event_name = event.get("event", "")
                event_images = event.get("images", [])
                lines.append(f"- {year} - {event_name}: {len(event_images)} images")
    elif images:
        lines.append(f"- Gallery with {len(images)} images")
    lines.append("")
    return lines


def clean_lines(lines):
    """Remove excessive blank lines (more than 2 consecutive)."""
    result = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return result


def get_section_title(route_id):
    """Generate a human-readable section title from a route ID."""
    return route_id.replace("-", " ").title()


def build_context():
    """Build the full AI context markdown from all content files."""
    site = load_json(CONTENT_DIR / "site.json")
    routes = site.get("routes", {})

    # Load supplementary content
    try:
        header_config = load_json(CONTENT_DIR / "header.json")
    except Exception:
        header_config = {}

    try:
        footer_config = load_json(CONTENT_DIR / "footer.json")
    except Exception:
        footer_config = {}

    try:
        announcements_config = load_json(CONTENT_DIR / "announcements.json")
    except Exception:
        announcements_config = {}

    sections = []

    # ---- Header info ----
    mission = footer_config.get("brand", {}).get("mission", "")
    if mission:
        sections.append(("About the Academy", [mission, ""]))

    # ---- Contact info from footer ----
    operations = footer_config.get("operations", [])
    if operations:
        contact_lines = ["**Contact:**"]
        for op in operations:
            label = op.get("label", "")
            if label:
                contact_lines.append(f"- {label}")
        sections.append(("Contact", contact_lines))

    # ---- Announcements ----
    announcements = announcements_config.get("announcements", [])
    active_announcements = [a for a in announcements if a.get("enabled", True)]
    if active_announcements:
        ann_lines = []
        for ann in active_announcements:
            label = ann.get("label", "")
            body = ann.get("body", "")
            if label or body:
                ann_lines.append(f"- **{label}**: {body}" if label else f"- {body}")
        sections.append(("Current Announcements", ann_lines))

    # ---- Process each route's content ----
    for route_id, route_info in routes.items():
        content_path = route_info.get("content", "")
        if not content_path:
            continue

        full_path = CONTENT_DIR / content_path
        if not full_path.exists():
            continue

        try:
            content = load_json(full_path)
        except Exception as e:
            print(f"  Warning: Could not load {content_path}: {e}")
            continue

        title = content.get("pageTitle", get_section_title(route_id))
        meta = content.get("metaDescription", "")
        content_sections = content.get("sections", [])

        section_lines = []

        # Add meta description if available
        if meta:
            section_lines.append(meta)
            section_lines.append("")

        if content_sections:
            section_lines.extend(extract_text_from_sections(content_sections, routes))

        if section_lines:
            # Use a clean section title
            display_title = title.split("|")[0].strip() if "|" in title else title
            sections.append((display_title, section_lines))

    return sections


def generate_markdown(sections):
    """Generate the final markdown output."""
    lines = []

    lines.append("# Madison Chinese Dance Academy - Website Content")
    lines.append("")
    lines.append("This file contains all content from the Madison Chinese Dance Academy website.")
    lines.append("It is used as context for AI-powered responses.")
    lines.append("Generated automatically by `scripts/generate-ai-context.py`.")
    lines.append("")

    seen_titles = {}
    for title, content_lines in sections:
        # Deduplicate titles
        if title in seen_titles:
            seen_titles[title] += 1
            unique_title = f"{title} ({seen_titles[title]})"
        else:
            seen_titles[title] = 1
            unique_title = title

        lines.append("---")
        lines.append("")
        lines.append(f"## {unique_title}")
        lines.append("")

        for line in content_lines:
            lines.append(line)

    # Navigation summary at the end
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Website Navigation")
    lines.append("")

    try:
        site = load_json(CONTENT_DIR / "site.json")
        header_config = load_json(CONTENT_DIR / "header.json")
        nav = header_config.get("nav", [])

        for entry in nav:
            label = entry.get("label", "")
            items = entry.get("items", [])
            if items:
                lines.append(f"### {label}")
                for item in items:
                    item_label = item.get("label", item.get("route", ""))
                    lines.append(f"- {item_label}")
                lines.append("")
            elif entry.get("route"):
                lines.append(f"- {label}")
    except Exception:
        pass

    # Quick actions
    lines.append("### Quick Actions")
    lines.append("- Purchase Tickets: https://www.zeffy.com/en-US/ticketing/splendid-china--2026")
    lines.append("- Donate: https://www.zeffy.com/en-US/donation-form/donate-to-madison-chinese-dance-academy")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("© 2026 Madison Chinese Dance Academy. All rights reserved.")

    return "\n".join(lines)


def main():
    print("Generating ai-context.md from content JSON files...")
    print(f"  Content directory: {CONTENT_DIR}")
    print(f"  Output file: {OUTPUT_FILE}")
    print()

    sections = build_context()

    print(f"  Found {len(sections)} content sections")
    for title, _ in sections:
        print(f"    - {title}")
    print()

    markdown = generate_markdown(sections)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"  Successfully wrote {OUTPUT_FILE}")
    print(f"  File size: {len(markdown):,} characters")
    print()
    print("Done!")


if __name__ == "__main__":
    main()
