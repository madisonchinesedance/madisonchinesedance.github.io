"""Optimize and rename images in a directory.

For every image file inside the given directory this script will:

  1. Convert any non-image files (e.g. PDFs) into images automatically.
  2. Rename it to use the directory's own name plus a zero-padded counter,
     so files inside `images/splendid-china/splendid-china-2024/` become
     `splendid-china-2024_001.webp`, `splendid-china-2024_002.webp`, ....
  3. Re-encode the image to the smallest sensible file size while keeping
     the original clarity. By default the script targets WebP, which gives
     a much better size/quality ratio than JPEG/PNG for web use, but the
     output format and quality are configurable.

The script requires Pillow (`pip install Pillow`).

For PDF conversion it uses PyMuPDF (`pip install PyMuPDF`). If PyMuPDF is
not installed, PDF files will be skipped with a warning.

Usage:
    python scripts/image_optimize.py
    python scripts/image_optimize.py images/splendid-china/splendid-china-2024
    python scripts/image_optimize.py images/splendid-china/splendid-china-2024 images/splendid-china/splendid-china-2025
    python scripts/image_optimize.py images/splendid-china/splendid-china-2024 --format jpeg --quality 80
    python scripts/image_optimize.py images/splendid-china/splendid-china-2024 --keep-originals
    python scripts/image_optimize.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(
        "Pillow is required for image_optimize.py.\n"
        "Install it with:  pip install Pillow"
    )
    sys.exit(1)

# Optional: PyMuPDF for PDF -> image conversion.
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    fitz = None  # type: ignore[assignment]
    HAS_PYMUPDF = False


# Accepted input formats. Anything we can hand to Pillow.Image.open().
INPUT_EXTENSIONS = (
    ".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp",
)

# Non-image formats that we can convert to images before optimisation.
# Each entry maps an extension to a list of converter functions.  The first
# converter that succeeds wins.  Converters receive (src_path, dest_dir) and
# return a list of Path objects for the images they created.
CONVERTIBLE_EXTENSIONS = (".pdf",)

# Resolution for PDF rasterisation (dots per inch).  300 gives print-quality
# output; 150 is usually enough for web galleries.
PDF_DPI = 300

# Pillow format name -> file extension mapping. Keep the keys aligned with
# `Image.registered_extensions()` for the formats we want to support.
FORMAT_INFO = {
    "webp": {"extension": ".webp", "supports_alpha": True},
    "jpeg": {"extension": ".jpg",  "supports_alpha": False},
    "png":  {"extension": ".png",  "supports_alpha": True},
    "avif": {"extension": ".avif", "supports_alpha": True},
}

DEFAULT_FORMAT = "webp"
DEFAULT_QUALITY = 85
# Pillow is happy to skip "lossless" WebP/PNG optimisation, but a slow
# encoder pass gives noticeably smaller files at the same visual quality.
PILLOW_WEBP_METHOD = 6


def human_size(num_bytes: int) -> str:
    """Return a friendly byte/KB/MB string for printing."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def convert_pdf_to_images(
    src_path: Path,
    dest_dir: Path,
) -> list[Path]:
    """Convert a PDF file to one or more PNG images using PyMuPDF.

    Each page of the PDF is rendered at ``PDF_DPI`` and saved as a
    temporary PNG in *dest_dir*.  Returns a list of the created image
    paths.

    Raises ``RuntimeError`` if PyMuPDF is not installed.
    """
    if not HAS_PYMUPDF or fitz is None:
        raise RuntimeError(
            "PyMuPDF is required to convert PDF files.\n"
            "Install it with:  pip install PyMuPDF"
        )

    created: list[Path] = []
    doc = fitz.open(str(src_path))
    try:
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            # Render at the configured DPI.
            zoom = PDF_DPI / 72.0  # 72 is the PDF default DPI.
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Build an output filename from the source stem.
            if len(doc) == 1:
                out_name = f"{src_path.stem}.png"
            else:
                out_name = f"{src_path.stem}_p{page_number + 1}.png"
            out_path = dest_dir / out_name
            pix.save(str(out_path))
            created.append(out_path)
    finally:
        doc.close()

    return created


# Mapping of convertible extension -> converter function.
CONVERTERS: dict[str, Callable[[Path, Path], list[Path]]] = {
    ".pdf": convert_pdf_to_images,
}


def convert_non_image_files(
    image_dir: Path,
    keep_originals: bool = False,
) -> list[Path]:
    """Convert non-image files (e.g. PDFs) into PNG images.

    Scans *image_dir* for files whose extension is in
    ``CONVERTIBLE_EXTENSIONS``, converts each one to image(s), and
    optionally removes the original.  Returns a list of the newly
    created PNG paths.
    """
    converted: list[Path] = []

    for filename in sorted(os.listdir(image_dir)):
        ext = Path(filename).suffix.lower()
        if ext not in CONVERTIBLE_EXTENSIONS:
            continue

        src = image_dir / filename
        if not src.is_file():
            continue

        converter = CONVERTERS.get(ext)
        if converter is None:
            continue

        print(f"  Converting {filename} to image(s)...")
        try:
            images = converter(src, image_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"    Failed to convert {filename}: {exc}")
            continue

        converted.extend(images)
        for img_path in images:
            print(f"    -> {img_path.name}")

        if not keep_originals:
            src.unlink()

    return converted


def _prepare_for_format(img: Image.Image, output_format: str) -> Image.Image:
    """Return a copy of `img` with the right mode for `output_format`.

    JPEG can't store alpha, so any RGBA/LA/P image is flattened onto a
    white background. WebP/PNG/AVIF happily keep the alpha channel.
    """
    fmt = output_format.lower()
    if fmt in FORMAT_INFO and not FORMAT_INFO[fmt]["supports_alpha"]:
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            alpha = img.getchannel("A")
            background.paste(img, mask=alpha)
            return background
        if img.mode == "P":
            return img.convert("RGB")
    return img


def optimize_image(
    src_path: Path,
    dst_path: Path,
    output_format: str,
    quality: int,
) -> int:
    """Re-encode `src_path` into `dst_path` and return the new byte count."""
    fmt = output_format.lower()
    if fmt not in FORMAT_INFO:
        raise SystemExit(f"Unsupported output format: {output_format}")

    save_kwargs: dict = {"optimize": True}
    if fmt in ("webp", "jpeg", "avif"):
        save_kwargs["quality"] = quality
    if fmt == "webp":
        save_kwargs["method"] = PILLOW_WEBP_METHOD
    if fmt == "jpeg":
        # Progressive JPEGs are a touch smaller and load faster on the web.
        save_kwargs["progressive"] = True

    with Image.open(src_path) as raw:
        raw.load()  # Make sure the file handle is closed before we re-open.
        image = _prepare_for_format(raw, fmt)
        image.save(dst_path, fmt.upper(), **save_kwargs)

    return dst_path.stat().st_size


def _zero_padded_width(count: int) -> int:
    """Return the smallest number of digits needed to fit `count`.

    This means a folder with 9 or fewer images gets 1 digit, 10-99 gets
    2, 100-999 gets 3, and so on. Keeps the suffix compact for small
    folders while still sorting correctly for larger ones.
    """
    width = 1
    while 10 ** width <= count:
        width += 1
    return max(width, 3)  # Always pad to at least 3 digits for consistency.


def _is_generated_output(path: Path, directory_name: str) -> bool:
    """Return True for files that already look like this script's output."""
    output_extensions = {
        info["extension"].lower()
        for info in FORMAT_INFO.values()
    }
    if path.suffix.lower() not in output_extensions:
        return False

    return re.match(rf"^{re.escape(directory_name)}_\d+$", path.stem) is not None


def _media_files_for_processing(image_dir_path: Path) -> list[str]:
    """Return image filenames that should be optimized in this directory."""
    dir_name = image_dir_path.name
    return sorted(
        filename
        for filename in os.listdir(image_dir_path)
        if filename.lower().endswith(INPUT_EXTENSIONS)
        and not _is_generated_output(image_dir_path / filename, dir_name)
    )


def optimize_directory(
    image_dir: str,
    output_format: str = DEFAULT_FORMAT,
    quality: int = DEFAULT_QUALITY,
    keep_originals: bool = False,
    dry_run: bool = False,
) -> None:
    """Optimize and rename every image inside `image_dir`."""
    image_dir_path = Path(image_dir)
    if not image_dir_path.is_dir():
        raise SystemExit(f"Directory does not exist: {image_dir}")

    # --- Step 1: Convert any non-image files (PDFs, etc.) to images. ---
    convertible_count = sum(
        1 for f in os.listdir(image_dir_path)
        if Path(f).suffix.lower() in CONVERTIBLE_EXTENSIONS
    )
    if convertible_count:
        print(f"Found {convertible_count} convertible file(s) in {image_dir_path}.")
        if dry_run:
            print("  Dry run: skipping conversion.")
        else:
            converted = convert_non_image_files(image_dir_path, keep_originals)
            if converted:
                print(f"Converted {len(converted)} file(s) to images.\n")

    # --- Step 2: Optimise and rename every image. ---
    dir_name = image_dir_path.name
    target_ext = FORMAT_INFO[output_format.lower()]["extension"]

    originals = _media_files_for_processing(image_dir_path)

    if not originals:
        print(f"No unoptimized input images found in {image_dir_path}.")
        return

    skipped_outputs = sorted(
        filename
        for filename in os.listdir(image_dir_path)
        if _is_generated_output(image_dir_path / filename, dir_name)
    )
    if skipped_outputs:
        print(f"Skipping {len(skipped_outputs)} already-optimized output file(s).")

    pad_width = _zero_padded_width(len(originals))
    total_before = 0
    total_after = 0
    processed = 0

    for index, filename in enumerate(originals, start=1):
        src = image_dir_path / filename
        new_filename = f"{dir_name}_{index:0{pad_width}d}{target_ext}"
        dst = image_dir_path / new_filename

        if dry_run:
            before = src.stat().st_size
            total_before += before
            processed += 1
            print(f"  Would optimize {filename} -> {new_filename} ({human_size(before)})")
            continue

        try:
            before = src.stat().st_size
            after = optimize_image(src, dst, output_format, quality)
        except Exception as exc:  # noqa: BLE001 - surface anything to the user
            print(f"  Failed to optimize {filename}: {exc}")
            continue

        total_before += before
        total_after += after
        processed += 1
        savings = (1 - after / before) * 100 if before else 0
        print(
            f"  {filename} -> {new_filename}  "
            f"({human_size(before)} -> {human_size(after)}, {savings:+.1f}%)"
        )

        if not keep_originals and src != dst:
            src.unlink()

    if processed == 0:
        print("No images were optimized.")
        return

    if dry_run:
        print(
            f"\nDry run. Found {processed} image(s) to optimize in {image_dir_path}.\n"
            f"Current size: {human_size(total_before)}."
        )
        return

    overall_savings = (1 - total_after / total_before) * 100 if total_before else 0
    print(
        f"\nDone. Optimized {processed} image(s) in {image_dir_path}.\n"
        f"Total size: {human_size(total_before)} -> {human_size(total_after)} "
        f"({overall_savings:+.1f}%)."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize and rename images in a directory.",
    )
    parser.add_argument(
        "image_dirs",
        nargs="*",
        help=(
            "Path(s) to image directories. "
            "If omitted, all image directories under images/ are processed."
        ),
    )
    parser.add_argument(
        "--format",
        choices=sorted(FORMAT_INFO.keys()),
        default=DEFAULT_FORMAT,
        help=f"Output format (default: {DEFAULT_FORMAT}).",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help=(
            "Encoder quality 1-100, higher is better. "
            f"Ignored for PNG (lossless). Default: {DEFAULT_QUALITY}."
        ),
    )
    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Keep the original files after optimization.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which directories and files would be processed without changing anything.",
    )
    return parser.parse_args()


def _discover_image_dirs(base: Path) -> list[Path]:
    """Recursively find all directories containing images or convertible files.

    Walks the directory tree under *base* and returns every directory that
    contains at least one image or convertible file, sorted
    alphabetically.  Leaf directories are preferred — if a directory
    contains both images *and* subdirectories with images, only the
    subdirectories are returned to avoid double-processing.
    """
    # Collect every directory that directly contains relevant files.
    leaf_dirs: set[Path] = set()
    for dirpath, dirnames, filenames in os.walk(base):
        d = Path(dirpath)
        has_media = any(
            Path(f).suffix.lower() in (*INPUT_EXTENSIONS, *CONVERTIBLE_EXTENSIONS)
            for f in filenames
        )
        if has_media:
            leaf_dirs.add(d)

    # A "leaf" is a dir with images whose descendants don't also have images.
    result: list[Path] = []
    for d in sorted(leaf_dirs):
        # If any descendant of *d* is also a leaf, skip *d* (the deeper
        # directory will be processed instead, avoiding double work).
        if any(other != d and other.is_relative_to(d) for other in leaf_dirs):
            continue
        result.append(d)

    return result


def main() -> None:
    args = parse_args()
    image_dirs = args.image_dirs

    if shutil.which("cwebp") is None and args.format == "webp":
        # Pillow bundles a WebP encoder so this isn't a hard requirement,
        # but the system toolchain gives slightly smaller files. Print a
        # friendly note rather than failing.
        print(
            "Note: install `libwebp` (provides the `cwebp` tool) for the "
            "smallest possible WebP output. Pillow's encoder will still run."
        )

    if image_dirs:
        # Process one or more explicitly requested directories.
        for idx, image_dir in enumerate(image_dirs, 1):
            header = f"[{idx}/{len(image_dirs)}] {image_dir}"
            print(f"\n{'=' * len(header)}")
            print(header)
            print(f"{'=' * len(header)}")
            optimize_directory(
                image_dir,
                output_format=args.format,
                quality=args.quality,
                keep_originals=args.keep_originals,
                dry_run=args.dry_run,
            )
    else:
        # No directory given — discover and process all image directories.
        script_dir = Path(__file__).resolve().parent
        images_root = script_dir.parent / "images"
        if not images_root.is_dir():
            raise SystemExit(f"Images directory not found: {images_root}")

        image_dirs = _discover_image_dirs(images_root)
        if not image_dirs:
            print(f"No image directories found under {images_root}.")
            return

        print(f"Processing {len(image_dirs)} directory(s) under {images_root}.\n")
        for idx, d in enumerate(image_dirs, 1):
            header = f"[{idx}/{len(image_dirs)}] {d.relative_to(images_root)}"
            print(f"\n{'=' * len(header)}")
            print(header)
            print(f"{'=' * len(header)}")
            optimize_directory(
                str(d),
                output_format=args.format,
                quality=args.quality,
                keep_originals=args.keep_originals,
                dry_run=args.dry_run,
            )


if __name__ == "__main__":
    main()
