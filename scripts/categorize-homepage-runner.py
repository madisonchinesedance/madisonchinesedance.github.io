"""Sort homepage runner images into aspect-ratio buckets for local R2 import.

Reads images from cloudflare-r2-import/homepage-runner/ and assigns each file
to a sibling folder based on pixel width and height:

  * homepage-runner/       — near 16:9 (standard top carousel)
  * homepage-runner-tall/  — portrait (4:5 viewport)
  * homepage-runner-wide/  — panoramic (21:9 viewport)

Only files directly inside homepage-runner/ are processed. Images already
sorted into tall/wide folders are left untouched.

Dependency: pip install Pillow

Usage:
    python scripts/categorize-homepage-runner.py              # dry-run (default)
    python scripts/categorize-homepage-runner.py --apply      # move files
    python scripts/categorize-homepage-runner.py --apply --copy # copy instead

After sorting, push to R2 and sync JSON:
    rclone copy cloudflare-r2-import r2:mcda-website-cdn -P
    python scripts/scan-images.py
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}

BUCKET_STANDARD = "homepage-runner"
BUCKET_TALL = "homepage-runner-tall"
BUCKET_WIDE = "homepage-runner-wide"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def classify_aspect_ratio(ratio: float, tall_max: float, wide_min: float) -> str:
    if ratio < tall_max:
        return BUCKET_TALL
    if ratio > wide_min:
        return BUCKET_WIDE
    return BUCKET_STANDARD


def image_dimensions(path: Path) -> tuple[int, int]:
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


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Sort homepage-runner images into tall/wide/standard folders."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=root / "cloudflare-r2-import" / "homepage-runner",
        help="Folder containing uncategorized homepage runner images.",
    )
    parser.add_argument(
        "--dest-root",
        type=Path,
        default=root / "cloudflare-r2-import",
        help="Parent folder for homepage-runner* output directories.",
    )
    parser.add_argument(
        "--tall-max",
        type=float,
        default=1.25,
        help="Aspect ratios below this go to homepage-runner-tall (default: 1.25).",
    )
    parser.add_argument(
        "--wide-min",
        type=float,
        default=2.1,
        help="Aspect ratios above this go to homepage-runner-wide (default: 2.1).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move or copy files. Without this flag, only print the plan.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving (only with --apply).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source.resolve()
    dest_root = args.dest_root.resolve()

    images = list_source_images(source_dir)
    if not images:
        print(f"No images found in {source_dir}")
        return

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

        print(
            f"{path.name:<40} {width}x{height:>5} {ratio:>8.2f}  {bucket}/"
        )

        if args.apply:
            if bucket == BUCKET_STANDARD:
                continue
            transfer_file(path, destination, copy=args.copy)

    print("-" * 80)
    print(
        f"Standard ({BUCKET_STANDARD}): {counts[BUCKET_STANDARD]}  "
        f"Tall ({BUCKET_TALL}): {counts[BUCKET_TALL]}  "
        f"Wide ({BUCKET_WIDE}): {counts[BUCKET_WIDE]}"
    )

    if not args.apply:
        print("\nNo files changed. Re-run with --apply to move or --apply --copy to copy.")


if __name__ == "__main__":
    main()
