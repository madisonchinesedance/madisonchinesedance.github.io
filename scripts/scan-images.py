"""Update gallery JSON files from images in Cloudflare R2 bucket.

For each per-year folder (e.g. splendid-china/splendid-china-2024/ in the bucket):
  * Populate `galleryImages` in content/splendid-china/splendid-china-2024.json
    so the matching Splendid China archive page (which uses the same gallery
    runner as the main Gallery page) shows those photos.

In addition, the script aggregates the per-year images into
content/gallery.json so the main Gallery page can still display everything
together. Years are sorted in reverse chronological order so the most recent
year appears first.

Configuration (in order of precedence):
    1. Environment variables: R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY,
       R2_BUCKET, R2_PUBLIC_URL
    2. scripts/r2-config.json file (gitignored -- never commit this file)

Usage:
    python scripts/scan-images.py
    python scripts/scan-images.py --content content/gallery.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import boto3
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# R2 / S3 configuration
#
# Credentials are loaded in order of precedence:
#   1. Environment variables (set in the shell / OS)
#   2. scripts/.env file (gitignored)
#   3. scripts/r2-config.json (gitignored, legacy fallback)
# ---------------------------------------------------------------------------

# Load .env file next to this script if it exists (does not override env vars)
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

_env = os.environ.get

R2_ACCOUNT_ID = _env("R2_ACCOUNT_ID")
R2_ACCESS_KEY = _env("R2_ACCESS_KEY")
R2_SECRET_KEY = _env("R2_SECRET_KEY")
R2_BUCKET = _env("R2_BUCKET")
R2_PUBLIC_URL = (_env("R2_PUBLIC_URL") or "").rstrip("/")

# Fall back to the local config file for any values not set via env vars.
CONFIG_PATH = Path(__file__).resolve().parent / "r2-config.json"
_cfg: dict = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        _cfg = json.load(f)

if not R2_ACCOUNT_ID:
    R2_ACCOUNT_ID = _cfg.get("account_id", "")
if not R2_ACCESS_KEY:
    R2_ACCESS_KEY = _cfg.get("access_key_id", "")
if not R2_SECRET_KEY:
    R2_SECRET_KEY = _cfg.get("secret_access_key", "")
if not R2_BUCKET:
    R2_BUCKET = _cfg.get("bucket_name", "")
if not R2_PUBLIC_URL:
    R2_PUBLIC_URL = _cfg.get("public_url", "").rstrip("/")

# Validate that all required values are present.
_missing = []
for _name, _val in [
    ("R2_ACCOUNT_ID", R2_ACCOUNT_ID),
    ("R2_ACCESS_KEY", R2_ACCESS_KEY),
    ("R2_SECRET_KEY", R2_SECRET_KEY),
    ("R2_BUCKET", R2_BUCKET),
    ("R2_PUBLIC_URL", R2_PUBLIC_URL),
]:
    if not _val:
        _missing.append(_name)

if _missing:
    raise SystemExit(
        "Missing required R2 configuration values: "
        + ", ".join(_missing)
        + "\n\nSet them as environment variables or add them to "
        + str(CONFIG_PATH)
    )

# S3-compatible endpoint for Cloudflare R2
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Create the S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",  # R2 uses 'auto' for all regions
)

# ---------------------------------------------------------------------------

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


def natural_key(name: str) -> list[object]:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", name)
    ]


def title_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    words = re.sub(r"[_-]+", " ", stem)
    words = re.sub(r"\s+", " ", words).strip()
    return words.title()


def r2_object_url(key: str) -> str:
    """Return the public URL for a given R2 object key."""
    return f"{R2_PUBLIC_URL}/{key}"


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


def list_bucket_prefixes(prefix: str, delimiter: str = "/") -> list[dict]:
    """Return the 'subdirectory' prefixes under *prefix* in the R2 bucket.

    For example, with prefix='splendid-china/' this returns entries like
    'splendid-china/splendid-china-2025/' from CommonPrefixes.
    """
    response = s3_client.list_objects_v2(
        Bucket=R2_BUCKET,
        Prefix=prefix,
        Delimiter=delimiter,
    )
    return response.get("CommonPrefixes", [])


def list_bucket_objects(prefix: str) -> list[str]:
    """Return all object keys under *prefix* in the R2 bucket.

    Only returns image files (matching IMAGE_EXTENSIONS).
    """
    keys: list[str] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if Path(key).suffix.lower() in IMAGE_EXTENSIONS:
                keys.append(key)
    return keys


def scan_year_images(year_prefix: str) -> list[dict[str, str]]:
    """Return image metadata for all images under *year_prefix* in R2.

    *year_prefix* is something like 'splendid-china/splendid-china-2025/'.
    """
    keys = list_bucket_objects(year_prefix)
    keys.sort(key=natural_key)

    return [
        {
            "src": r2_object_url(key),
            "thumb": r2_object_url(key),
            "alt": title_from_filename(Path(key).name),
        }
        for key in keys
    ]


def scan_year_folders() -> list[dict]:
    """Return one entry per ``splendid-china-YYYY`` folder in the R2 bucket.

    Scans the 'splendid-china/' prefix for year subdirectories.
    """
    # Get all subdirectories under splendid-china/
    common_prefixes = list_bucket_prefixes("splendid-china/")
    if not common_prefixes:
        return []

    years = []
    for cp in common_prefixes:
        prefix = cp["Prefix"]  # e.g. 'splendid-china/splendid-china-2025/'
        # Extract the folder name (e.g. 'splendid-china-2025')
        folder_name = prefix.strip("/").split("/")[-1]
        match = YEAR_FOLDER_PATTERN.match(folder_name)
        if not match:
            continue
        year = match.group(1)
        images = scan_year_images(prefix)
        years.append({
            "year": year,
            "dir_prefix": prefix,
            "images": images,
        })

    # Sort by year descending (most recent first)
    years.sort(key=lambda y: y["year"], reverse=True)
    return years


def build_gallery_groups(years: list[dict]) -> list[dict]:
    """Build the ``galleryGroups`` structure for content/gallery.json."""
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
    """Update a per-year JSON file with its ``galleryImages`` array.

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
        description="Scan year-based image folders in R2 and update gallery JSON files."
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
    content_path = args.content.resolve()
    per_year_dir = args.per_year_dir.resolve()

    # Verify the R2 bucket is accessible
    try:
        s3_client.head_bucket(Bucket=R2_BUCKET)
        print(f"Connected to R2 bucket: {R2_BUCKET}")
    except Exception as exc:
        raise SystemExit(f"Could not access R2 bucket '{R2_BUCKET}': {exc}") from exc

    years = scan_year_folders()
    if not years:
        print("No splendid-china-YYYY folders found in R2 bucket.")
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