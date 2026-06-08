"""Update gallery JSON files from images in images/splendid-china/.

For each per-year folder (e.g. images/splendid-china/splendid-china-2024/):
  * Populate `galleryImages` in content/splendid-china/splendid-china-2024.json
    so the matching Splendid China archive page (which uses the same gallery
    runner as the main Gallery page) shows those photos.

In addition, the script aggregates the per-year images into
content/gallery.json so the main Gallery page can still display everything
together. Years are sorted in reverse chronological order so the most recent
year appears first.

Usage:
    python scripts/scan-images.py
    python scripts/scan-images.py --images-dir path/to/images
    python scripts/scan-images.py --content content/gallery.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
DEFAULT_CONTENT = {
    "pageTitle": "Gallery | Madison Chinese Dance Academy",
    "metaDescription": "Image gallery of the Madison Chinese Dance Academy.",
    "heading": "Gallery",
    "galleryGroups": [],
    "galleryImages": [],
}

# Per-year folders are named like "splendid-china-2024" so the script can
# pair them up with the matching page + JSON file.
YEAR_FOLDER_PATTERN = re.compile(r"^splendid-china-(\d{4})$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def natural_key(path: Path) -> list[object]:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def title_from_filename(path: Path) -> str:
    words = re.sub(r"[_-]+", " ", path.stem)
    words = re.sub(r"\s+", " ", words).strip()
    return words.title()


def site_path(path: Path, root: Path) -> str:
    return "/" + path.relative_to(root).as_posix()


def read_existing_content(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Could not parse {path}: {error}") from error

    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object.")

    return data


def scan_year_images(year_dir: Path, root: Path) -> list[dict[str, str]]:
    images = sorted(
        (
            path
            for path in year_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=natural_key,
    )

    return [
        {
            "src": site_path(path, root),
            "thumb": site_path(path, root),
            "alt": title_from_filename(path),
        }
        for path in images
    ]


def scan_year_folders(images_dir: Path, root: Path) -> list[dict]:
    """Return one entry per `splendid-china-YYYY` folder under images_dir."""
    if not images_dir.exists():
        return []

    years = []
    for year_dir in sorted(
        (path for path in images_dir.iterdir() if path.is_dir()),
        key=lambda path: path.name,
        reverse=True,
    ):
        match = YEAR_FOLDER_PATTERN.match(year_dir.name)
        if not match:
            continue
        year = match.group(1)
        images = scan_year_images(year_dir, root)
        years.append({
            "year": year,
            "dir": year_dir,
            "images": images,
        })

    return years


def build_gallery_groups(years: list[dict]) -> list[dict]:
    """Build the `galleryGroups` structure for content/gallery.json."""
    groups = []
    for year_info in years:
        if not year_info["images"]:
            continue
        groups.append({
            "year": year_info["year"],
            "events": [
                {
                    "event": "Splendid China",
                    "images": year_info["images"],
                }
            ],
        })
    return groups


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def update_main_gallery(content_path: Path, existing: dict, years: list[dict]) -> int:
    gallery_groups = build_gallery_groups(years)
    content = {
        "pageTitle": existing.get("pageTitle")
            or existing.get("galleryPageTitle")
            or DEFAULT_CONTENT["pageTitle"],
        "metaDescription": existing.get("metaDescription")
            or existing.get("galleryMetaDescription")
            or DEFAULT_CONTENT["metaDescription"],
        "heading": existing.get("heading")
            or existing.get("galleryHeroHeading")
            or DEFAULT_CONTENT["heading"],
        "galleryGroups": gallery_groups,
        "galleryImages": DEFAULT_CONTENT["galleryImages"],
    }
    write_json(content_path, content)
    return len(gallery_groups)


def update_per_year_json(content_path: Path, year_info: dict) -> int:
    """Update a per-year JSON file with its `galleryImages` array.

    The script preserves every other field (page title, blocks, etc.) so
    the page's content stays intact.
    """
    existing = read_existing_content(content_path)
    existing["galleryImages"] = year_info["images"]
    write_json(content_path, existing)
    return len(year_info["images"])


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Scan year-based image folders and update gallery JSON files."
    )
    parser.add_argument(
        "--images-dir",
        default=root / "images" / "splendid-china",
        type=Path,
        help="Directory containing per-year image subfolders (e.g. images/splendid-china).",
    )
    parser.add_argument(
        "--content",
        default=root / "content" / "gallery.json",
        type=Path,
        help="Path to the main gallery JSON file to update.",
    )
    parser.add_argument(
        "--per-year-dir",
        default=root / "content" / "splendid-china",
        type=Path,
        help="Directory containing the per-year JSON files to update.",
    )
    parser.add_argument(
        "--skip-main",
        action="store_true",
        help="Skip updating the main gallery.json (only update per-year JSONs).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root()
    images_dir = args.images_dir.resolve()
    content_path = args.content.resolve()
    per_year_dir = args.per_year_dir.resolve()

    years = scan_year_folders(images_dir, root)
    if not years:
        print(f"No splendid-china-YYYY folders found in {images_dir}")
        return

    image_count = sum(len(year["images"]) for year in years)

    if not args.skip_main:
        existing = read_existing_content(content_path)
        group_count = update_main_gallery(content_path, existing, years)
        group_noun = "group" if group_count == 1 else "groups"
        image_noun = "image" if image_count == 1 else "images"
        print(
            f"Updated {content_path.relative_to(root)} with {group_count} {group_noun} "
            f"({image_count} {image_noun})."
        )

    updated_per_year = 0
    for year_info in years:
        per_year_path = per_year_dir / f"splendid-china-{year_info['year']}.json"
        if not per_year_path.exists():
            print(f"Skipping {per_year_path.relative_to(root)}: file not found")
            continue
        image_noun = "image" if len(year_info["images"]) == 1 else "images"
        update_per_year_json(per_year_path, year_info)
        updated_per_year += 1
        print(
            f"Updated {per_year_path.relative_to(root)} with "
            f"{len(year_info['images'])} {image_noun}."
        )

    print(
        f"\nDone. Updated {updated_per_year} per-year JSON file(s) "
        f"covering {image_count} image(s)."
    )


if __name__ == "__main__":
    main()


