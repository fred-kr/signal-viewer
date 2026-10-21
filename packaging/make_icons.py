"""
Generates the platform icon files used by PyInstaller from the app's PNG icon.

Run from the repo root after changing `signal_viewer/icons/app_icon.png`:

    uv run python packaging/make_icons.py

Writes `packaging/icons/app_icon.ico` (Windows) and `packaging/icons/app_icon.icns` (macOS). Both are committed so
CI builds do not depend on this script.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "signal_viewer" / "icons" / "app_icon.png"
OUT_DIR = ROOT / "packaging" / "icons"

ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE).convert("RGBA")

    # Pillow derives the smaller ICO sizes from the full-size image; the ICNS writer resizes to each required slot.
    # macOS expects a 1024 px master for Retina sizes, so upscale once if the source is smaller.
    master = image if max(image.size) >= 1024 else image.resize((1024, 1024), Image.Resampling.LANCZOS)

    image.save(OUT_DIR / "app_icon.ico", format="ICO", sizes=ICO_SIZES)
    master.save(OUT_DIR / "app_icon.icns", format="ICNS")

    for file in ("app_icon.ico", "app_icon.icns"):
        size_kb = (OUT_DIR / file).stat().st_size / 1024
        print(f"{OUT_DIR / file}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
