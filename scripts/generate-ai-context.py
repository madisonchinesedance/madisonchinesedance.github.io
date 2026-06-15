#!/usr/bin/env python3
"""Generate ai-context.md from 11ty content (Markdown + JSON data files)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA_DIR = SRC / "_data"
OUTPUT_FILE = ROOT / "ai-context.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(md_path: Path) -> tuple[dict, str]:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    import yaml

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return meta, body


def strip_html(text: str) -> str:
    text = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def collect_markdown_pages() -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for md_path in sorted(SRC.rglob("*.md")):
        if md_path.name == "index.md" and md_path.parent == SRC:
            continue
        meta, body = parse_frontmatter(md_path)
        title = meta.get("title", md_path.stem)
        display = title.split("|")[0].strip()
        description = meta.get("description", "")
        lines = []
        if description:
            lines.extend([description, ""])
        if body:
            lines.append(body)
        if lines:
            sections.append((display, lines))
    return sections


def build_context() -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []

    footer = load_json(DATA_DIR / "footer.json") if (DATA_DIR / "footer.json").exists() else {}
    mission = footer.get("brand", {}).get("mission", "")
    if mission:
        sections.append(("About the Academy", [mission, ""]))

    operations = footer.get("operations", [])
    if operations:
        contact_lines = ["**Contact:**"]
        for op in operations:
            if op.get("label"):
                contact_lines.append(f"- {op['label']}")
        sections.append(("Contact", contact_lines))

    announcements = load_json(DATA_DIR / "announcements.json") if (DATA_DIR / "announcements.json").exists() else {}
    for ann in announcements.get("announcements", []):
        if ann.get("enabled") is False:
            continue
        label = ann.get("label", "")
        body = ann.get("body", "")
        if label or body:
            sections.append(("Current Announcements", [f"- **{label}**: {body}" if label else f"- {body}"]))

    homepage = load_json(DATA_DIR / "homepage.json") if (DATA_DIR / "homepage.json").exists() else {}
    if homepage:
        home_lines = [
            homepage.get("hero", {}).get("heading", ""),
            homepage.get("hero", {}).get("body", ""),
            "",
            homepage.get("story", {}).get("english", {}).get("body", ""),
            "",
            homepage.get("story", {}).get("chinese", {}).get("body", ""),
        ]
        home_lines = [line for line in home_lines if line]
        if home_lines:
            sections.insert(0, ("Home", home_lines))

    sections.extend(collect_markdown_pages())
    return sections


def generate_markdown(sections: list[tuple[str, list[str]]]) -> str:
    lines = [
        "# Madison Chinese Dance Academy - Website Content",
        "",
        "Generated automatically by `scripts/generate-ai-context.py`.",
        "",
    ]
    for title, content_lines in sections:
        lines.extend(["---", "", f"## {title}", ""])
        lines.extend(content_lines)
        lines.append("")

    lines.extend([
        "---",
        "",
        "### Quick Actions",
        "- Purchase Tickets: https://www.zeffy.com/en-US/ticketing/splendid-china--2026",
        "- Donate: https://www.zeffy.com/en-US/donation-form/donate-to-madison-chinesedance-academy",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    sections = build_context()
    markdown = generate_markdown(sections)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} ({len(markdown):,} characters, {len(sections)} sections)")


if __name__ == "__main__":
    main()
