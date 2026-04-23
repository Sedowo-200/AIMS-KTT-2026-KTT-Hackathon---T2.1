"""
Create the official mini hackathon plant dataset from local image folders.

Default outputs:
  - data/mini_plant_set/train|val|test/<class_name>/*.jpg
  - data/test_field/<class_name>/*.jpg
  - data/mini_plant_set.zip
  - data/test_field.zip

Run from this project root:
  python create_hackathon_dataset.py
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it with: python -m pip install pillow"
    ) from exc


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEFAULT_IMAGE_SIZE = 224
SPLITS = ("train", "val", "test")

if hasattr(Image, "Resampling"):
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
else:
    RESAMPLE_FILTER = Image.LANCZOS


@dataclass(frozen=True)
class SourceSpec:
    class_name: str
    image_dir: Path
    csv_file: Path | None = None
    csv_label: int | None = None


SOURCE_SPECS = [
    SourceSpec(
        class_name="maize_rust",
        image_dir=Path("maize_only_base") / "Corn_(maize)___Common_rust_",
    ),
    SourceSpec(
        class_name="maize_blight",
        image_dir=Path("maize_only_base") / "Corn_(maize)___Northern_Leaf_Blight",
    ),
    SourceSpec(
        class_name="healthy",
        image_dir=Path("maize_only_base") / "Corn_(maize)___healthy",
    ),
    SourceSpec(
        class_name="bean_spot",
        image_dir=Path("Bean_Dataset") / "angular_leaf_spot",
    ),
    SourceSpec(
        class_name="cassava_mosaic",
        image_dir=Path("cassava-leaf-disease-classification") / "train_images",
        csv_file=Path("cassava-leaf-disease-classification") / "train.csv",
        csv_label=3,
    ),
]


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        description="Build mini_plant_set and test_field from local crop datasets."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=project_root,
        help="Root folder containing maize_only_base, Bean_Dataset, and cassava data.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Output root containing mini_plant_set and test_field folders.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="Optional raw copy directory. Disabled by default for the official tree.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Processed output directory. Defaults to <data-dir>/mini_plant_set.",
    )
    parser.add_argument(
        "--field-dir",
        type=Path,
        default=None,
        help="Robustness output directory. Defaults to <data-dir>/test_field.",
    )
    parser.add_argument(
        "--processed-zip",
        type=Path,
        default=None,
        help="Processed ZIP path. Defaults to <mini_plant_set-dir>.zip.",
    )
    parser.add_argument(
        "--field-zip",
        type=Path,
        default=None,
        help="Robustness ZIP path. Defaults to <field-dir>.zip.",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=300,
        help="Maximum images to sample per class.",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=DEFAULT_IMAGE_SIZE,
        help="Square output image size in pixels.",
    )
    parser.add_argument(
        "--robust-count",
        type=int,
        default=60,
        help="Number of random test images to degrade into test_field.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling and perturbations.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Keep existing output folders instead of deleting them first.",
    )
    return parser.parse_args()


def resolve_under_root(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def clean_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def ensure_output_tree(output_dir: Path, class_names: list[str]) -> None:
    for split in SPLITS:
        for class_name in class_names:
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)


def ensure_raw_tree(raw_dir: Path, class_names: list[str]) -> None:
    for class_name in class_names:
        (raw_dir / class_name).mkdir(parents=True, exist_ok=True)


def ensure_field_tree(field_dir: Path, class_names: list[str]) -> None:
    for class_name in class_names:
        (field_dir / class_name).mkdir(parents=True, exist_ok=True)


def collect_folder_images(source_root: Path, spec: SourceSpec) -> list[Path]:
    image_dir = resolve_under_root(source_root, spec.image_dir)
    if not image_dir.exists():
        raise FileNotFoundError(f"Missing source folder: {image_dir}")
    return sorted(path for path in image_dir.rglob("*") if is_image_file(path))


def collect_csv_filtered_images(source_root: Path, spec: SourceSpec) -> list[Path]:
    image_dir = resolve_under_root(source_root, spec.image_dir)
    csv_file = resolve_under_root(source_root, spec.csv_file or Path("train.csv"))

    if not csv_file.exists():
        fallback = source_root / "train.csv"
        if fallback.exists():
            csv_file = fallback
        else:
            raise FileNotFoundError(f"Missing CSV file for {spec.class_name}: {csv_file}")

    if not image_dir.exists():
        raise FileNotFoundError(f"Missing source folder: {image_dir}")

    images: list[Path] = []
    with csv_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"image_id", "label"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{csv_file} is missing columns: {sorted(missing)}")

        for row in reader:
            if str(row["label"]).strip() != str(spec.csv_label):
                continue
            image_path = image_dir / row["image_id"].strip()
            if is_image_file(image_path):
                images.append(image_path)

    return sorted(images)


def collect_images(source_root: Path, spec: SourceSpec) -> list[Path]:
    if spec.csv_label is not None:
        return collect_csv_filtered_images(source_root, spec)
    return collect_folder_images(source_root, spec)


def split_counts(total: int) -> dict[str, int]:
    if total == 0:
        return {"train": 0, "val": 0, "test": 0}

    ideal = {"train": total * 0.80, "val": total * 0.10, "test": total * 0.10}
    counts = {split_name: int(value) for split_name, value in ideal.items()}
    remainder = total - sum(counts.values())

    order = sorted(
        SPLITS,
        key=lambda split_name: (ideal[split_name] - counts[split_name], split_name),
        reverse=True,
    )
    for split_name in order[:remainder]:
        counts[split_name] += 1

    return counts


def split_images(paths: list[Path], rng: random.Random, max_per_class: int) -> dict[str, list[Path]]:
    shuffled = list(paths)
    rng.shuffle(shuffled)
    selected = shuffled[:max_per_class]

    counts = split_counts(len(selected))
    train_count = counts["train"]
    val_count = counts["val"]

    return {
        "train": selected[:train_count],
        "val": selected[train_count : train_count + val_count],
        "test": selected[train_count + val_count :],
    }


def copy_raw_image(source_path: Path, destination_path: Path) -> bool:
    try:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        return True
    except OSError as exc:
        print(f"Warning: skipped raw copy {source_path}: {exc}", file=sys.stderr)
        return False


def load_resized_rgb(image_path: Path, image_size: int) -> Image.Image:
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        return image.resize((image_size, image_size), RESAMPLE_FILTER)


def save_resized_image(source_path: Path, destination_path: Path, image_size: int) -> bool:
    try:
        image = load_resized_rgb(source_path, image_size)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination_path, format="JPEG", quality=95, optimize=True)
        return True
    except (OSError, UnidentifiedImageError) as exc:
        print(f"Warning: skipped unreadable image {source_path}: {exc}", file=sys.stderr)
        return False


def build_main_dataset(
    source_root: Path,
    raw_dir: Path | None,
    output_dir: Path,
    rng: random.Random,
    max_per_class: int,
    image_size: int,
) -> tuple[list[tuple[str, Path]], dict[str, dict[str, int]]]:
    class_names = [spec.class_name for spec in SOURCE_SPECS]
    if raw_dir is not None:
        ensure_raw_tree(raw_dir, class_names)
    ensure_output_tree(output_dir, class_names)

    test_images: list[tuple[str, Path]] = []
    summary: dict[str, dict[str, int]] = {}

    for spec in SOURCE_SPECS:
        source_images = collect_images(source_root, spec)
        split_map = split_images(source_images, rng, max_per_class)
        selected_images = [path for split_name in SPLITS for path in split_map[split_name]]

        summary[spec.class_name] = {
            "found": len(source_images),
            "sampled": len(selected_images),
            "raw": 0,
            "processed": 0,
            "train": 0,
            "val": 0,
            "test": 0,
        }

        if raw_dir is not None:
            for index, source_path in enumerate(selected_images, start=1):
                raw_name = f"{spec.class_name}_{index:04d}{source_path.suffix.lower()}"
                raw_path = raw_dir / spec.class_name / raw_name
                if copy_raw_image(source_path, raw_path):
                    summary[spec.class_name]["raw"] += 1

        for split_name, split_paths in split_map.items():
            for index, source_path in enumerate(split_paths, start=1):
                destination_name = f"{spec.class_name}_{index:04d}.jpg"
                destination_path = output_dir / split_name / spec.class_name / destination_name

                if save_resized_image(source_path, destination_path, image_size):
                    summary[spec.class_name]["processed"] += 1
                    summary[spec.class_name][split_name] += 1
                    if split_name == "test":
                        test_images.append((spec.class_name, source_path))

    return test_images, summary


def save_degraded_field_image(
    source_path: Path,
    destination_path: Path,
    rng: random.Random,
    image_size: int,
) -> bool:
    try:
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = image.resize((image_size, image_size), RESAMPLE_FILTER)

            sigma = rng.uniform(0.0, 1.5)
            noise_sigma = rng.uniform(0.0, 6.0)
            jpeg_quality = rng.randint(50, 85)
            brightness_factor = rng.uniform(0.85, 1.15)

            image = image.filter(ImageFilter.GaussianBlur(radius=sigma))
            noise = Image.effect_noise(image.size, noise_sigma).convert("RGB")
            image = ImageChops.add(image, noise, scale=1.0, offset=-128)
            image = ImageEnhance.Brightness(image).enhance(brightness_factor)

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(destination_path, format="JPEG", quality=jpeg_quality, optimize=True)
            return True
    except (OSError, UnidentifiedImageError) as exc:
        print(f"Warning: skipped field image {source_path}: {exc}", file=sys.stderr)
        return False


def build_robustness_set(
    test_images: list[tuple[str, Path]],
    field_dir: Path,
    rng: random.Random,
    robust_count: int,
    image_size: int,
) -> int:
    class_names = [spec.class_name for spec in SOURCE_SPECS]
    ensure_field_tree(field_dir, class_names)

    shuffled = list(test_images)
    rng.shuffle(shuffled)
    selected = shuffled[: min(robust_count, len(shuffled))]

    written = 0
    for index, (class_name, source_path) in enumerate(selected, start=1):
        destination_name = f"field_{index:04d}_{source_path.stem}.jpg"
        destination_path = field_dir / class_name / destination_name
        if save_degraded_field_image(source_path, destination_path, rng, image_size):
            written += 1

    return written


def zip_directory(directory: Path, zip_path: Path) -> None:
    clean_path(zip_path)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(directory.parent))


def print_summary(summary: dict[str, dict[str, int]], field_count: int) -> None:
    print("\nDataset summary")
    print("---------------")
    for class_name, counts in summary.items():
        raw_part = f"raw={counts['raw']:3d} " if counts["raw"] else ""
        print(
            f"{class_name:15s} found={counts['found']:5d} "
            f"sampled={counts['sampled']:3d} {raw_part}"
            f"processed={counts['processed']:3d} "
            f"train={counts['train']:3d} val={counts['val']:3d} test={counts['test']:3d}"
        )
    print(f"test_field images: {field_count}")


def main() -> None:
    args = parse_args()

    source_root = args.source_root.resolve()
    data_dir = resolve_under_root(source_root, args.data_dir)
    raw_dir = resolve_under_root(source_root, args.raw_dir) if args.raw_dir else None
    output_dir = (
        resolve_under_root(source_root, args.output_dir)
        if args.output_dir
        else data_dir / "mini_plant_set"
    )
    field_dir = (
        resolve_under_root(source_root, args.field_dir)
        if args.field_dir
        else data_dir / "test_field"
    )
    output_zip = (
        resolve_under_root(source_root, args.processed_zip)
        if args.processed_zip
        else output_dir.with_suffix(".zip")
    )
    field_zip = (
        resolve_under_root(source_root, args.field_zip)
        if args.field_zip
        else field_dir.with_suffix(".zip")
    )

    if args.max_per_class <= 0:
        raise ValueError("--max-per-class must be positive")
    if args.image_size <= 0:
        raise ValueError("--image-size must be positive")
    if args.robust_count < 0:
        raise ValueError("--robust-count cannot be negative")

    if not args.no_clean:
        if raw_dir is not None:
            clean_path(raw_dir)
        clean_path(output_dir)
        clean_path(field_dir)
        clean_path(output_zip)
        clean_path(field_zip)

    rng = random.Random(args.seed)

    test_images, summary = build_main_dataset(
        source_root=source_root,
        raw_dir=raw_dir,
        output_dir=output_dir,
        rng=rng,
        max_per_class=args.max_per_class,
        image_size=args.image_size,
    )
    field_count = build_robustness_set(
        test_images=test_images,
        field_dir=field_dir,
        rng=rng,
        robust_count=args.robust_count,
        image_size=args.image_size,
    )

    zip_directory(output_dir, output_zip)
    zip_directory(field_dir, field_zip)

    print_summary(summary, field_count)
    if raw_dir is not None:
        print(f"\nWrote: {raw_dir}")
    else:
        print()
    print(f"Wrote: {output_dir}")
    print(f"Wrote: {field_dir}")
    print(f"Wrote: {output_zip}")
    print(f"Wrote: {field_zip}")


if __name__ == "__main__":
    main()
