"""Update gallery JSON files from images in Cloudflare R2 bucket.

Subcommands:
    sync        Scan R2 and update gallery / per-year / homepage JSON (default)
    categorize  Sort local homepage-runner images into tall/wide/standard folders

Usage:
    python scripts/scan-images.py
    python scripts/scan-images.py sync
    python scripts/scan-images.py categorize
    python scripts/scan-images.py categorize --apply
    python scripts/scan-images.py categorize --reconcile --apply

After categorizing locally, push to R2 then sync:
    rclone sync cloudflare-r2-import r2:mcda-website-cdn -P
    python scripts/scan-images.py sync
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}

BUCKET_STANDARD = "homepage-runner"
BUCKET_TALL = "homepage-runner-tall"
BUCKET_WIDE = "homepage-runner-wide"

DEFAULT_CONTENT = {
    "pageTitle": "Gallery | Madison Chinese Dance Academy",
    "metaDescription": "Image gallery of the Madison Chinese Dance Academy.",
    "heading": "Gallery",
    "galleryGroups": [],
    "galleryImages": [],
}

YEAR_FOLDER_PATTERN = re.compile(r"^splendid-china-(\d{4})$")
GALLERY_PREFIX = "gallery/"
HOMEPAGE_RUNNER_PREFIX = "homepage-runner/"
HOMEPAGE_RUNNER_TALL_PREFIX = "homepage-runner-tall/"
HOMEPAGE_RUNNER_WIDE_PREFIX = "homepage-runner-wide/"

HOMEPAGE_RUNNER_KEYS = {
    "homepageRunnerImages": HOMEPAGE_RUNNER_PREFIX,
    "homepageRunnerTallImages": HOMEPAGE_RUNNER_TALL_PREFIX,
    "homepageRunnerWideImages": HOMEPAGE_RUNNER_WIDE_PREFIX,
}

HOMEPAGE_RUNNER_FIELD_MAP = {
    "homepageRunnerImages": "runnerImages",
    "homepageRunnerTallImages": "runnerTallImages",
    "homepageRunnerWideImages": "runnerWideImages",
}

RCLONE_REMINDER = (
    "\nNext: upload to R2 with:\n"
    "  rclone sync cloudflare-r2-import r2:mcda-website-cdn -P\n"
    "Then run: python scripts/scan-images.py sync"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Local categorize (homepage runner buckets)
# ---------------------------------------------------------------------------


def classify_aspect_ratio(ratio: float, tall_max: float, wide_min: float) -> str:
    if ratio < tall_max:
        return BUCKET_TALL
    if ratio > wide_min:
        return BUCKET_WIDE
    return BUCKET_STANDARD


def image_dimensions(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def list_source_images(source_dir: Path) -> list[Path]:
    if not source_dir.is_dir():
        return []
    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def transfer_file(source: Path, destination: Path, *, copy: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copy2(source, destination)
    else:
        shutil.move(source, destination)


def reconcile_duplicates(dest_root: Path, *, apply: bool) -> int:
    """Delete files in homepage-runner/ that also exist in tall or wide folders."""
    standard_dir = dest_root / BUCKET_STANDARD
    relocated_dirs = [dest_root / BUCKET_TALL, dest_root / BUCKET_WIDE]
    if not standard_dir.is_dir():
        print(f"No {BUCKET_STANDARD}/ folder found at {standard_dir}")
        return 0

    relocated_names: set[str] = set()
    for folder in relocated_dirs:
        for path in list_source_images(folder):
            relocated_names.add(path.name)

    if not relocated_names:
        print("No tall/wide images found to reconcile against.")
        return 0

    removed = 0
    mode = "RECONCILE" if apply else "DRY RUN"
    print(f"{mode}: checking {standard_dir} for duplicates in tall/wide folders\n")

    for path in list_source_images(standard_dir):
        if path.name not in relocated_names:
            continue
        print(f"  remove duplicate: {path.name}")
        if apply:
            path.unlink()
        removed += 1

    noun = "duplicate" if removed == 1 else "duplicates"
    if apply:
        print(f"\nRemoved {removed} {noun} from {BUCKET_STANDARD}/.")
    else:
        print(f"\nWould remove {removed} {noun} from {BUCKET_STANDARD}/.")
        if removed:
            print("Re-run with: python scripts/scan-images.py categorize --reconcile --apply")

    return removed


def cmd_categorize(args: argparse.Namespace) -> int:
    source_dir = args.source.resolve()
    dest_root = args.dest_root.resolve()

    if args.reconcile:
        reconcile_duplicates(dest_root, apply=args.apply)
        if args.apply:
            print(RCLONE_REMINDER)
        return 0

    images = list_source_images(source_dir)
    if not images:
        print(f"No images found in {source_dir}")
        return 0

    mode = "DRY RUN" if not args.apply else ("COPY" if args.copy else "MOVE")
    print(f"{mode}: classifying {len(images)} image(s) from {source_dir}\n")
    print(f"{'File':<40} {'Size':>12} {'Ratio':>8}  Destination")
    print("-" * 80)

    counts = {BUCKET_STANDARD: 0, BUCKET_TALL: 0, BUCKET_WIDE: 0}

    for path in images:
        width, height = image_dimensions(path)
        if height == 0:
            print(f"{path.name:<40} {'?':>12} {'?':>8}  SKIP (invalid dimensions)")
            continue

        ratio = width / height
        bucket = classify_aspect_ratio(ratio, args.tall_max, args.wide_min)
        counts[bucket] += 1
        destination = dest_root / bucket / path.name

        print(f"{path.name:<40} {width}x{height:>5} {ratio:>8.2f}  {bucket}/")

        if args.apply and bucket != BUCKET_STANDARD:
            transfer_file(path, destination, copy=args.copy)

    print("-" * 80)
    print(
        f"Standard ({BUCKET_STANDARD}): {counts[BUCKET_STANDARD]}  "
        f"Tall ({BUCKET_TALL}): {counts[BUCKET_TALL]}  "
        f"Wide ({BUCKET_WIDE}): {counts[BUCKET_WIDE]}"
    )

    if not args.apply:
        print("\nNo files changed. Re-run with --apply to move or --apply --copy to copy.")
    else:
        print(RCLONE_REMINDER)

    return 0


# ---------------------------------------------------------------------------
# R2 sync
# ---------------------------------------------------------------------------


def _load_r2_config() -> tuple[str, str, str, str, str]:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)

    env = os.environ.get
    account_id = env("R2_ACCOUNT_ID", "")
    access_key = env("R2_ACCESS_KEY", "")
    secret_key = env("R2_SECRET_KEY", "")
    bucket = env("R2_BUCKET", "")
    public_url = (env("R2_PUBLIC_URL") or "").rstrip("/")

    config_path = Path(__file__).resolve().parent / "r2-config.json"
    cfg: dict = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)

    if not account_id:
        account_id = cfg.get("account_id", "")
    if not access_key:
        access_key = cfg.get("access_key_id", "")
    if not secret_key:
        secret_key = cfg.get("secret_access_key", "")
    if not bucket:
        bucket = cfg.get("bucket_name", "")
    if not public_url:
        public_url = cfg.get("public_url", "").rstrip("/")

    missing = [
        name
        for name, val in [
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY", access_key),
            ("R2_SECRET_KEY", secret_key),
            ("R2_BUCKET", bucket),
            ("R2_PUBLIC_URL", public_url),
        ]
        if not val
    ]
    if missing:
        raise SystemExit(
            "Missing required R2 configuration values: "
            + ", ".join(missing)
            + f"\n\nSet them as environment variables or add them to {config_path}"
        )

    return account_id, access_key, secret_key, bucket, public_url


def _create_s3_client():
    import boto3
    from botocore.config import Config

    account_id, access_key, secret_key, bucket, public_url = _load_r2_config()
    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return client, bucket, public_url


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


def read_existing_content(path: Path) -> dict:
    if not path.exists():
        return {}

    if path.suffix.lower() == ".md":
        import yaml

        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}
        data = yaml.safe_load(parts[1]) or {}
        if not isinstance(data, dict):
            raise SystemExit(f"{path} frontmatter must be a mapping.")
        data["_body"] = parts[2].lstrip("\n")
        return data

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Could not parse {path}: {error}") from error

    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object.")

    return data


def write_content_file(path: Path, data: dict) -> None:
    body = data.pop("_body", "")
    if path.suffix.lower() == ".md":
        import yaml

        frontmatter = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
        return
    write_json(path, data)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def list_bucket_prefixes(s3_client, bucket: str, prefix: str, delimiter: str = "/") -> list[dict]:
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        Delimiter=delimiter,
    )
    return response.get("CommonPrefixes", [])


def list_bucket_objects(s3_client, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if Path(key).suffix.lower() in IMAGE_EXTENSIONS:
                keys.append(key)
    return keys


def scan_year_images(
    s3_client,
    bucket: str,
    public_url: str,
    year_prefix: str,
) -> list[dict[str, str]]:
    keys = list_bucket_objects(s3_client, bucket, year_prefix)
    keys.sort(key=natural_key)

    return [
        {
            "src": f"{public_url}/{key}",
            "thumb": f"{public_url}/{key}",
            "alt": title_from_filename(Path(key).name),
        }
        for key in keys
    ]


def image_basename(image: dict[str, str]) -> str:
    return Path(image["src"].rstrip("/")).name


def dedupe_homepage_runners(
    runners: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, list[dict[str, str]]], int]:
    tall_names = {image_basename(image) for image in runners["homepageRunnerTallImages"]}
    wide_names = {image_basename(image) for image in runners["homepageRunnerWideImages"]}
    relocated_names = tall_names | wide_names

    standard_images = runners["homepageRunnerImages"]
    deduped_standard = [
        image
        for image in standard_images
        if image_basename(image) not in relocated_names
    ]
    excluded_count = len(standard_images) - len(deduped_standard)

    return {
        **runners,
        "homepageRunnerImages": deduped_standard,
    }, excluded_count


def scan_homepage_runners(s3_client, bucket: str, public_url: str) -> tuple[dict[str, list[dict[str, str]]], int]:
    runners = {
        key: scan_year_images(s3_client, bucket, public_url, prefix)
        for key, prefix in HOMEPAGE_RUNNER_KEYS.items()
    }
    return dedupe_homepage_runners(runners)


def scan_year_folders(s3_client, bucket: str, public_url: str) -> list[dict]:
    common_prefixes = list_bucket_prefixes(s3_client, bucket, "")
    if not common_prefixes:
        return []

    years = []
    for cp in common_prefixes:
        prefix = cp["Prefix"]
        folder_name = prefix.strip("/").split("/")[-1]
        match = YEAR_FOLDER_PATTERN.match(folder_name)
        if not match:
            continue
        year = match.group(1)
        images = scan_year_images(s3_client, bucket, public_url, prefix)
        years.append({
            "year": year,
            "dir_prefix": prefix,
            "images": images,
        })

    years.sort(key=lambda y: y["year"], reverse=True)
    return years


def build_gallery_groups(years: list[dict]) -> list[dict]:
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


def update_main_gallery(
    content_path: Path,
    existing: dict,
    years: list[dict],
    featured_images: list[dict[str, str]],
) -> tuple[int, int]:
    gallery_groups = build_gallery_groups(years)
    content = {
        **existing,
        "featuredImages": featured_images,
        "groups": gallery_groups,
    }
    write_json(content_path, content)
    return len(gallery_groups), len(featured_images)


def update_per_year_json(content_path: Path, year_info: dict) -> int:
    existing = read_existing_content(content_path)
    existing["galleryImages"] = year_info["images"]
    write_content_file(content_path, existing)
    return len(year_info["images"])


def update_homepage_json(
    content_path: Path,
    runner_images: dict[str, list[dict[str, str]]],
) -> dict[str, int]:
    existing = read_existing_content(content_path)
    counts = {}
    for key, images in runner_images.items():
        field = HOMEPAGE_RUNNER_FIELD_MAP.get(key, key)
        existing[field] = images
        counts[key] = len(images)
    write_json(content_path, existing)
    return counts


def cmd_sync(args: argparse.Namespace) -> int:
    root = repo_root()
    content_path = args.content.resolve()
    per_year_dir = args.per_year_dir.resolve()

    s3_client, bucket, public_url = _create_s3_client()
    print(f"Connecting to R2 bucket: {bucket} ...")

    years = scan_year_folders(s3_client, bucket, public_url)
    featured_images = scan_year_images(s3_client, bucket, public_url, GALLERY_PREFIX)
    homepage_runners, excluded_homepage_dupes = scan_homepage_runners(s3_client, bucket, public_url)
    homepage_image_count = sum(len(images) for images in homepage_runners.values())

    if not years and not featured_images and homepage_image_count == 0:
        print(
            "No splendid-china-YYYY, gallery/, or homepage-runner* "
            "image folders found in R2 bucket."
        )
        return 0

    image_count = sum(len(year["images"]) for year in years)
    homepage_path = root / "src" / "_data" / "homepage.json"
    homepage_counts = update_homepage_json(homepage_path, homepage_runners)
    for key, count in homepage_counts.items():
        noun = "image" if count == 1 else "images"
        print(
            f"Updated {homepage_path.relative_to(root)} with "
            f"{count} {key} {noun}."
        )
    if excluded_homepage_dupes:
        noun = "duplicate" if excluded_homepage_dupes == 1 else "duplicates"
        print(
            f"Excluded {excluded_homepage_dupes} {noun} from homepage-runner/ "
            f"(also present in homepage-runner-tall/ or homepage-runner-wide/)."
        )

    if not args.skip_main:
        existing = read_existing_content(content_path)
        group_count, featured_count = update_main_gallery(
            content_path, existing, years, featured_images
        )
        group_noun = "group" if group_count == 1 else "groups"
        archive_noun = "image" if image_count == 1 else "images"
        featured_noun = "image" if featured_count == 1 else "images"
        print(
            f"Updated {content_path.relative_to(root)} with {group_count} {group_noun} "
            f"({image_count} archive {archive_noun}) and {featured_count} featured "
            f"{featured_noun}."
        )

    updated_per_year = 0
    for year_info in years:
        per_year_path = per_year_dir / f"{year_info['year']}.md"
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

    standard_count = homepage_counts.get("homepageRunnerImages", 0)
    tall_count = homepage_counts.get("homepageRunnerTallImages", 0)
    wide_count = homepage_counts.get("homepageRunnerWideImages", 0)
    homepage_total = standard_count + tall_count + wide_count
    featured_count = len(featured_images) if not args.skip_main else 0

    print(
        f"\nDone. Homepage runners: {standard_count} standard, "
        f"{tall_count} tall, {wide_count} wide ({homepage_total} total)."
    )
    print(
        f"Splendid China archive: {image_count} image(s) across "
        f"{updated_per_year} per-year JSON file(s)."
    )
    if not args.skip_main:
        featured_noun = "image" if featured_count == 1 else "images"
        print(f"Featured gallery: {featured_count} {featured_noun}.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Manage site images: categorize local homepage runners or sync from R2."
    )
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser(
        "sync",
        help="Scan R2 and update gallery JSON files (default)",
    )
    sync_parser.add_argument(
        "--content",
        default=root / "src" / "_data" / "gallery.json",
        type=Path,
        help="Path to the main gallery JSON file to update.",
    )
    sync_parser.add_argument(
        "--per-year-dir",
        default=root / "src" / "splendid-china",
        type=Path,
        help="Directory containing the per-year JSON files to update.",
    )
    sync_parser.add_argument(
        "--skip-main",
        action="store_true",
        help="Skip updating the main gallery.json (only update per-year JSONs).",
    )
    sync_parser.set_defaults(func=cmd_sync)

    cat_parser = subparsers.add_parser(
        "categorize",
        help="Sort local homepage-runner images into tall/wide/standard folders",
    )
    cat_parser.add_argument(
        "--source",
        type=Path,
        default=root / "cloudflare-r2-import" / "homepage-runner",
        help="Folder containing uncategorized homepage runner images.",
    )
    cat_parser.add_argument(
        "--dest-root",
        type=Path,
        default=root / "cloudflare-r2-import",
        help="Parent folder for homepage-runner* output directories.",
    )
    cat_parser.add_argument(
        "--tall-max",
        type=float,
        default=1.25,
        help="Aspect ratios below this go to homepage-runner-tall (default: 1.25).",
    )
    cat_parser.add_argument(
        "--wide-min",
        type=float,
        default=2.1,
        help="Aspect ratios above this go to homepage-runner-wide (default: 2.1).",
    )
    cat_parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Remove files from homepage-runner/ that also exist in tall/wide folders.",
    )
    cat_parser.add_argument(
        "--apply",
        action="store_true",
        help="Move/copy files, or delete duplicates when used with --reconcile.",
    )
    cat_parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving (only with --apply, not --reconcile).",
    )
    cat_parser.set_defaults(func=cmd_categorize)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Backward compat: bare invocation or legacy flags → sync
    if not argv or argv[0] not in ("sync", "categorize"):
        argv = ["sync", *argv]

    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
