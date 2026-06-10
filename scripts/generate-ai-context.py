#!/usr/bin/env python3
"""
Generate ai-context.md from content JSON files.

Reads all JSON files referenced in content/site.json and compiles
their text content into a concise markdown file for AI chatbot context.
Target output: 15,000-20,000 characters (to stay within Groq free tier limits).

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

# Placeholder patterns - pages whose body text only matches these are skipped
PLACEHOLDER_PATTERNS = [
    "coming soon",
    "can be added here",
    "performance archive details, photos, and program notes",
    "placeholder page",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", text, flags=re.IGNORECASE)
    text = re.sub(r"<(?:i|em)>(.*?)</(?:i|em)>", r"*\1*", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def extract_actions(actions, routes):
    lines = []
    for action in actions:
        label = action.get("label", "")
        href = action.get("href", "")
        route = action.get("route", "")
        if route and route in routes:
            href = routes[route].get("href", href)
        if label:
            # Only include external URLs (http/https/zeffy), skip relative internal links
            if href and (href.startswith("http") or href.startswith("https") or href.startswith("www")):
                lines.append(f"- {label}: {href}")
            elif not href:
                lines.append(f"- {label}")
    return lines


def has_meaningful_content(text):
    text_lower = text.lower().strip()
    if not text_lower:
        return False
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in text_lower:
            return False
    return True


def page_has_real_content(content):
    blocks = content.get("blocks", [])
    if not blocks:
        return False

    all_text = ""
    for block in blocks:
        bt = block.get("type", "")
        if bt in ("heading1", "heading2", "heading3"):
            all_text += block.get("text", "") + " "
        elif bt == "body":
            body_text = block.get("text", "") or block.get("body", "")
            all_text += strip_html(body_text) + " "
        elif bt == "cards":
            for item in block.get("items", []):
                all_text += item.get("heading", "") + " " + item.get("body", "") + " "
        elif bt in ("section", "hero"):
            nested = block.get("blocks", [])
            if nested and page_has_real_content({"blocks": nested}):
                return True
    return has_meaningful_content(all_text)


def _words_set(s):
    w = s.lower().strip()
    for ch in "-–—|:;.":
        w = w.replace(ch, " ")
    return frozenset(w.split())


def _is_dup_heading(heading_text, section_title):
    """Return True if heading essentially duplicates the section title."""
    if not heading_text or not section_title:
        return False
    if heading_text.strip().lower() == section_title.strip().lower():
        return True
    hw = _words_set(heading_text)
    stw = _words_set(section_title)
    return len(hw) > 0 and hw.issubset(stw)


def extract_text_from_blocks(blocks, routes, section_title=""):
    """Extract text from blocks. Returns compact lines, deduplicating headings that match section_title."""
    lines = []
    if not blocks:
        return lines

    for block in blocks:
        bt = block.get("type", "")

        if bt in ("heading1", "heading2", "heading3"):
            text = block.get("text", "")
            if text and not _is_dup_heading(text, section_title):
                level = int(bt[-1])
                lines.append(f"{'#' * level} {text}")

        elif bt == "body":
            text = block.get("text", "") or block.get("body", "")
            text = strip_html(text)
            if text:
                for para in text.split("\n\n"):
                    para = para.strip()
                    if para:
                        combined = " ".join(line.strip() for line in para.split("\n") if line.strip())
                        lines.append(combined)
            actions = block.get("actions", [])
            if actions:
                lines.extend(extract_actions(actions, routes))

        elif bt == "cards":
            for item in block.get("items", []):
                heading = item.get("heading", "")
                body = strip_html(item.get("body", ""))
                label = item.get("label", "")
                if heading:
                    lines.append(f"- **{heading}**: {body}" if body else f"- **{heading}**")
                elif body:
                    lines.append(f"- {body}")
            actions = block.get("actions", [])
            if actions:
                lines.extend(extract_actions(actions, routes))

        elif bt in ("section", "hero"):
            nested = block.get("blocks", [])
            if nested:
                lines.extend(extract_text_from_blocks(nested, routes, section_title))

        elif bt == "gallery":
            groups = block.get("groups", [])
            images = block.get("images", [])
            if groups:
                for group in groups:
                    year = group.get("year", "")
                    for event in group.get("events", []):
                        ename = event.get("event", "")
                        eimages = event.get("images", [])
                        if ename:
                            lines.append(f"- {year} - {ename}: {len(eimages)} images")
            elif images:
                lines.append(f"- {len(images)} gallery images")

        elif bt == "zeffyEmbed":
            form_url = block.get("formUrl", "")
            # Only include full URLs, skip relative embed paths
            if form_url and (form_url.startswith("http") or form_url.startswith("https")):
                lines.append(f"- Form: {form_url}")

    return lines


def build_context():
    """Build context sections from content files, skipping placeholder-only pages."""
    site = load_json(CONTENT_DIR / "site.json")
    routes = site.get("routes", {})

    try:
        footer = load_json(CONTENT_DIR / "footer.json")
    except Exception:
        footer = {}

    try:
        announcements = load_json(CONTENT_DIR / "announcements.json")
    except Exception:
        announcements = {}

    sections = []
    skipped = []

    # --- About from footer ---
    mission = footer.get("brand", {}).get("mission", "")
    if mission:
        sections.append(("About the Academy", [mission]))

    # --- Contact from footer ---
    ops = footer.get("operations", [])
    if ops:
        cl = [f"- {op['label']}" for op in ops if op.get("label")]
        if cl:
            sections.append(("Contact", cl))

    # --- Announcements ---
    anns = announcements.get("announcements", [])
    active = [a for a in anns if a.get("enabled", True)]
    meaningful = [a for a in active if has_meaningful_content(f"{a.get('label','')} {a.get('body','')}".strip())]
    if meaningful:
        al = []
        for a in meaningful:
            label = a.get("label", "")
            body = a.get("body", "")
            al.append(f"- **{label}**: {body}" if label else f"- {body}")
        sections.append(("Current Announcements", al))

    # --- Route pages ---
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
        if not page_has_real_content(content):
            skipped.append(route_id)
            continue

        title = content.get("pageTitle", route_id.replace("-", " ").title())
        blocks = content.get("blocks", [])

        section_lines = extract_text_from_blocks(blocks, routes, section_title=title)

        if section_lines:
            display_title = title.split("|")[0].strip() if "|" in title else title
            sections.append((display_title, section_lines))

    if skipped:
        print(f"  Skipped {len(skipped)} placeholder pages: {', '.join(sorted(skipped))}")

    return sections


def generate_markdown(sections):
    lines = []
    lines.append("# Madison Chinese Dance Academy - Website Context")
    lines.append("")
    lines.append("Content from the MCDA website for AI-powered responses. Generated by scripts/generate-ai-context.py.")
    lines.append("")

    seen = {}
    for title, content_lines in sections:
        if title in seen:
            seen[title] += 1
            unique = f"{title} ({seen[title]})"
        else:
            seen[title] = 1
            unique = title
        lines.append(f"## {unique}")
        lines.append("")
        for line in content_lines:
            lines.append(line)
        if content_lines and content_lines[-1] != "":
            lines.append("")

    # Compact nav - summarize archive years
    lines.append("## Navigation")
    lines.append("")
    try:
        header = load_json(CONTENT_DIR / "header.json")
        for entry in header.get("nav", []):
            label = entry.get("label", "")
            items = entry.get("items", [])
            if items:
                # Count Splendid China archive items to compress them
                archive_count = sum(1 for it in items if it.get("route", "").startswith("splendid-china-20") and it.get("route") not in ("splendid-china-2026",))
                archive_shown = False
                for item in items:
                    il = item.get("label", item.get("route", ""))
                    route_id = item.get("route", "")
                    # Show Splendid China 2026 normally, summarize others
                    if route_id.startswith("splendid-china-20") and route_id != "splendid-china-2026":
                        if not archive_shown:
                            lines.append(f"- {label} / Archives 2008-2025")
                            archive_shown = True
                    else:
                        lines.append(f"- {label} / {il}")
            elif entry.get("route"):
                lines.append(f"- {label}")
    except Exception:
        pass

    lines.append("")
    lines.append("**Quick Actions:**")
    lines.append("- Tickets: https://www.zeffy.com/en-US/ticketing/splendid-china--2026")
    lines.append("- Donate: https://www.zeffy.com/en-US/donation-form/donate-to-madison-chinese-dance-academy")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("(c) 2026 Madison Chinese Dance Academy")
    return "\n".join(lines)


def main():
    print("Generating ai-context.md from content JSON files...")
    print(f"  Content directory: {CONTENT_DIR}")
    print(f"  Output file: {OUTPUT_FILE}")
    print()

    sections = build_context()

    print(f"\n  Found {len(sections)} content sections")
    for title, _ in sections:
        print(f"    - {title}")
    print()

    markdown = generate_markdown(sections)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)

    char_count = len(markdown)
    print(f"  Successfully wrote {OUTPUT_FILE}")
    print(f"  File size: {char_count:,} characters ({len(markdown.splitlines())} lines)")
    if char_count > 20000:
        print(f"  WARNING: Exceeds 20k target by {char_count - 20000} characters")
    elif char_count < 15000:
        print(f"  Below 15k target by {15000 - char_count} characters")
    else:
        print(f"  Within target range (15,000-20,000 characters)")
    print()
    print("Done!")


if __name__ == "__main__":
    main()