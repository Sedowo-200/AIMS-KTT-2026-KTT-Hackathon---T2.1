"""Check the exported INT8 TFLite artifact."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model.tflite"
MAX_MB = 10.0


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "model.tflite was not found. Run notebooks/training_quantization.ipynb first."
        )

    size_mb = MODEL_PATH.stat().st_size / (1024 * 1024)
    print(f"model.tflite size: {size_mb:.3f} MB")
    if size_mb > MAX_MB:
        raise SystemExit(f"Model exceeds {MAX_MB:.1f} MB target.")
    print("INT8 export artifact is present and below the 10 MB target.")


if __name__ == "__main__":
    main()
