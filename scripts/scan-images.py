"""Update content/gallery.json from files in images/gallery.

Usage:
    python scripts/scan-images.py
    python scripts/scan-images.py --gallery-dir path/to/images --content content/gallery.json
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
}


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


def scan_gallery_images(gallery_dir: Path, root: Path) -> list[dict[str, str]]:
    if not gallery_dir.exists():
        raise SystemExit(f"Gallery directory does not exist: {gallery_dir}")

    if not gallery_dir.is_dir():
        raise SystemExit(f"Gallery path is not a directory: {gallery_dir}")

    images = sorted(
        (
            path
            for path in gallery_dir.iterdir()
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


def build_content(existing: dict, gallery_images: list[dict[str, str]]) -> dict:
    return {
        "pageTitle": existing.get("pageTitle")
        or existing.get("galleryPageTitle")
        or DEFAULT_CONTENT["pageTitle"],
        "metaDescription": existing.get("metaDescription")
        or existing.get("galleryMetaDescription")
        or DEFAULT_CONTENT["metaDescription"],
        "heading": existing.get("heading")
        or existing.get("galleryHeroHeading")
        or DEFAULT_CONTENT["heading"],
        "galleryGroups": existing.get("galleryGroups")
        if isinstance(existing.get("galleryGroups"), list)
        else DEFAULT_CONTENT["galleryGroups"],
        "galleryImages": gallery_images,
    }


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Scan gallery image files and update content/gallery.json."
    )
    parser.add_argument(
        "--gallery-dir",
        default=root / "images" / "gallery",
        type=Path,
        help="Directory containing gallery images.",
    )
    parser.add_argument(
        "--content",
        default=root / "content" / "gallery.json",
        type=Path,
        help="Path to the gallery JSON file to update.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root()
    gallery_dir = args.gallery_dir.resolve()
    content_path = args.content.resolve()

    existing = read_existing_content(content_path)
    gallery_images = scan_gallery_images(gallery_dir, root)
    content = build_content(existing, gallery_images)

    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    noun = "image" if len(gallery_images) == 1 else "images"
    print(f"Updated {content_path.relative_to(root)} with {len(gallery_images)} {noun}.")


if __name__ == "__main__":
    main()
