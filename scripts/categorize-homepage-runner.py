"""Sort homepage runner images into aspect-ratio buckets for local R2 import.

Reads images from cloudflare-r2-import/homepage-runner/ and assigns each file
to a sibling folder based on pixel width and height:

  * homepage-runner/       — near 16:9 (standard top carousel)
  * homepage-runner-tall/  — portrait (4:5 viewport)
  * homepage-runner-wide/  — panoramic (21:9 viewport)

Only files directly inside homepage-runner/ are processed. Images already
sorted into tall/wide folders are left untouched.

Use --reconcile to delete duplicate files still left in homepage-runner/
after files were copied into homepage-runner-tall/ or homepage-runner-wide/.

Dependency: pip install Pillow

Usage:
    python scripts/categorize-homepage-runner.py              # dry-run (default)
    python scripts/categorize-homepage-runner.py --apply      # move files
    python scripts/categorize-homepage-runner.py --apply --copy # copy instead
    python scripts/categorize-homepage-runner.py --reconcile  # remove duplicates

After sorting, push to R2 and sync JSON:
    python scripts/categorize-homepage-runner.py --apply
    python scripts/categorize-homepage-runner.py --reconcile
    rclone sync cloudflare-r2-import r2:mcda-website-cdn -P
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


def reconcile_duplicates(
    dest_root: Path,
    *,
    apply: bool,
) -> int:
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
            print("Re-run with --reconcile --apply to delete them.")

    return removed


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
        "--reconcile",
        action="store_true",
        help="Remove files from homepage-runner/ that also exist in tall/wide folders.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move/copy files, or delete duplicates when used with --reconcile.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving (only with --apply, not --reconcile).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source.resolve()
    dest_root = args.dest_root.resolve()

    if args.reconcile:
        reconcile_duplicates(dest_root, apply=args.apply)
        return

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
