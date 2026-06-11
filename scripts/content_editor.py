"""Interactive editor for page content JSON (sections, blocks, actions)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from site_lib import (
    CONTENT_ROOT,
    REPO_ROOT,
    SITE_JSON,
    confirm,
    first_heading_and_body,
    list_routes,
    load_json,
    prompt,
    prompt_choice,
    prompt_multiline,
    route_content_path,
    truncate_preview,
    write_json,
)


@dataclass
class BlockRef:
    section_idx: int
    item_idx: int
    block_idx: int
    block: dict


def load_page_content(route_id: str) -> tuple[Path, dict] | None:
    site = load_json(SITE_JSON)
    path = route_content_path(site, route_id)
    if path is None or not path.is_file():
        return None
    return path, load_json(path)


def save_page_content(path: Path, data: dict) -> None:
    write_json(path, data)
    print(f"Updated {path.relative_to(REPO_ROOT)}")


def summarize_section(section: dict, index: int) -> str:
    columns = section.get("columns", 1)
    heading, body = first_heading_and_body(section)
    parts = [f"Section {index + 1} ({columns} col)"]
    if heading:
        parts.append(f'"{truncate_preview(heading, 40)}"')
    if body:
        parts.append(f"— {truncate_preview(body, 50)}")
    return " ".join(parts)


def summarize_block(block: dict, item_idx: int) -> str:
    block_type = block.get("type", "?")
    prefix = f"[item {item_idx + 1} · {block_type}"
    if block_type == "heading":
        font_size = block.get("fontSize", "heading-4")
        text = block.get("text", "")
        return f"{prefix} {font_size}] {truncate_preview(text, 50)}"
    if block_type == "body":
        text = block.get("text", "")
        return f"{prefix}] {truncate_preview(text, 50)}"
    if block_type == "gallery":
        variant = block.get("variant", "")
        return f"{prefix}{' ' + variant if variant else ''}] (gallery)"
    if block_type == "zeffyEmbed":
        return f"{prefix}] (Zeffy embed)"
    return f"{prefix}]"


def collect_block_refs(section: dict, section_idx: int) -> list[BlockRef]:
    refs: list[BlockRef] = []
    for item_idx, item in enumerate(section.get("items", [])):
        for block_idx, block in enumerate(item.get("blocks", [])):
            refs.append(BlockRef(section_idx, item_idx, block_idx, block))
    return refs


def new_section_template(columns: int) -> dict:
    items = []
    for i in range(columns):
        items.append({
            "blocks": [
                {"type": "heading", "fontSize": "heading-4", "text": f"New Section{f' {i + 1}' if columns > 1 else ''}"},
                {"type": "body", "text": ""},
            ],
        })
    return {"columns": columns, "items": items}


def pick_route() -> str | None:
    site = load_json(SITE_JSON)
    routes = list_routes(site)
    if not routes:
        print("No routes defined.")
        return None

    print("\nSelect a page:")
    for idx, (route_id, info) in enumerate(routes, 1):
        print(f"  {idx}. {route_id} → {info.get('page')}")

    choice = prompt("\nEnter number (or press enter to cancel)")
    if not choice.isdigit():
        return None
    idx = int(choice) - 1
    if idx < 0 or idx >= len(routes):
        print("Invalid selection.")
        return None
    return routes[idx][0]


def edit_heading_block(block: dict) -> None:
    current_text = block.get("text", "")
    new_text = prompt("Heading text", current_text)
    if new_text:
        block["text"] = new_text

    presets = [f"heading-{n}" for n in range(1, 7)]
    current = block.get("fontSize", "heading-4")
    font_size = prompt(f"Font size ({', '.join(presets)})", current)
    if font_size:
        block["fontSize"] = font_size


def list_actions(actions: list) -> None:
    if not actions:
        print("  (no action buttons)")
        return
    for idx, action in enumerate(actions, 1):
        link = action.get("route") or action.get("href", "")
        print(f"  {idx}. {action.get('label', '')} → {link}")


def pick_internal_route() -> str | None:
    site = load_json(SITE_JSON)
    routes = list_routes(site)
    options = [route_id for route_id, _ in routes]
    choice = prompt_choice("Select internal route", options)
    if choice is None:
        return None
    return options[choice - 1]


def edit_actions(block: dict) -> None:
    actions = block.setdefault("actions", [])

    while True:
        print("\nAction buttons:")
        list_actions(actions)
        print("\n1. Add action")
        print("2. Edit action")
        print("3. Delete action")
        print("b. Back")

        choice = prompt("Choice").lower()
        if choice in ("b", "back"):
            break

        if choice == "1":
            label = prompt("Button label")
            if not label:
                continue
            link_type = prompt_choice("Link type", ["Internal route", "External URL"])
            if link_type is None:
                continue
            if link_type == 1:
                route = pick_internal_route()
                if not route:
                    continue
                actions.append({"route": route, "label": label})
            else:
                href = prompt("URL")
                if not href:
                    continue
                new_tab = confirm("Open in new tab?")
                action = {"href": href, "label": label}
                if new_tab:
                    action["newTab"] = True
                actions.append(action)
            print("Action added.")

        elif choice == "2":
            if not actions:
                print("No actions to edit.")
                continue
            idx_str = prompt("Action number to edit")
            if not idx_str.isdigit():
                continue
            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(actions):
                print("Invalid selection.")
                continue
            action = actions[idx]
            new_label = prompt("Button label", action.get("label", ""))
            if new_label:
                action["label"] = new_label
            if "route" in action:
                route = pick_internal_route()
                if route:
                    action["route"] = route
            elif "href" in action:
                href = prompt("URL", action.get("href", ""))
                if href:
                    action["href"] = href
            print("Action updated.")

        elif choice == "3":
            if not actions:
                print("No actions to delete.")
                continue
            idx_str = prompt("Action number to delete")
            if not idx_str.isdigit():
                continue
            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(actions):
                print("Invalid selection.")
                continue
            if confirm(f"Delete action '{actions[idx].get('label', '')}'?"):
                actions.pop(idx)
                print("Action deleted.")

        else:
            print("Invalid choice.")

    if not actions:
        block.pop("actions", None)


def edit_block(block: dict) -> None:
    block_type = block.get("type", "")

    if block_type == "heading":
        edit_heading_block(block)
    elif block_type == "body":
        current = block.get("text", "")
        new_text = prompt_multiline("Body text", current)
        block["text"] = new_text
        if confirm("Edit action buttons on this block?"):
            edit_actions(block)
    elif block_type in ("gallery", "zeffyEmbed"):
        print(
            f"\n'{block_type}' blocks cannot be edited here. "
            "Use scan-images.py for gallery images or edit JSON manually for Zeffy embeds."
        )
    else:
        print(f"\nUnsupported block type: {block_type!r}")


def element_editor(section: dict, section_idx: int, path: Path, data: dict) -> None:
    while True:
        refs = collect_block_refs(section, section_idx)
        if not refs:
            print("\nThis section has no blocks.")
            return

        print(f"\nElements in section {section_idx + 1}:")
        for idx, ref in enumerate(refs, 1):
            print(f"  {idx}. {summarize_block(ref.block, ref.item_idx)}")

        print("b. Back")
        choice = prompt("\nElement number to edit (or b)").lower()
        if choice in ("b", "back"):
            break
        if not choice.isdigit():
            print("Invalid selection.")
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(refs):
            print("Invalid selection.")
            continue
        edit_block(refs[idx].block)
        save_page_content(path, data)


def section_editor(data: dict, path: Path) -> None:
    sections = data.setdefault("sections", [])

    while True:
        print("\nSections:")
        if not sections:
            print("  (no sections)")
        for idx, section in enumerate(sections):
            print(f"  {idx + 1}. {summarize_section(section, idx)}")

        print("\n1. Add section")
        print("2. Edit section elements")
        print("3. Delete section")
        print("b. Back")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break

        if choice == "1":
            cols_str = prompt("Number of columns (1-4)", "1")
            if not cols_str.isdigit():
                print("Invalid columns.")
                continue
            columns = int(cols_str)
            if columns < 1 or columns > 4:
                print("Columns must be 1-4.")
                continue
            sections.append(new_section_template(columns))
            save_page_content(path, data)
            print("Section added.")

        elif choice == "2":
            if not sections:
                print("No sections to edit.")
                continue
            idx_str = prompt("Section number to edit")
            if not idx_str.isdigit():
                continue
            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(sections):
                print("Invalid selection.")
                continue
            element_editor(sections[idx], idx, path, data)

        elif choice == "3":
            if not sections:
                print("No sections to delete.")
                continue
            idx_str = prompt("Section number to delete")
            if not idx_str.isdigit():
                continue
            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(sections):
                print("Invalid selection.")
                continue
            if confirm(f"Delete section {idx + 1}?"):
                sections.pop(idx)
                save_page_content(path, data)
                print("Section deleted.")

        else:
            print("Invalid choice.")


def edit_page_settings(data: dict, path: Path) -> None:
    current_title = data.get("pageTitle", "")
    current_desc = data.get("metaDescription", "")

    new_title = prompt("Page title", current_title)
    if new_title and new_title != current_title:
        data["pageTitle"] = new_title
        print("\nNote: scan-pages overwrites nav labels from pageTitle.")

    new_desc = prompt_multiline("Meta description", current_desc)
    if new_desc != current_desc:
        data["metaDescription"] = new_desc

    save_page_content(path, data)


def edit_page_content(route_id: str) -> None:
    loaded = load_page_content(route_id)
    if loaded is None:
        print(f"No content file found for route '{route_id}'.")
        return

    path, data = loaded

    while True:
        print(f"\nEditing content: {route_id} ({path.relative_to(REPO_ROOT)})")
        print("1. Edit sections")
        print("2. Edit page settings (title & meta description)")
        print("b. Back")

        choice = prompt("\nChoice").lower()
        if choice in ("b", "back"):
            break
        elif choice == "1":
            section_editor(data, path)
        elif choice == "2":
            edit_page_settings(data, path)
        else:
            print("Invalid choice.")
