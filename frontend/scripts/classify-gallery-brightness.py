#!/usr/bin/env python3
"""Classify cover_gallery images by brightness (light vs dark).

Generates a metadata manifest so the home/landing page can use only the
light images. This does NOT move, rename, or delete any file, and it does
NOT touch the /platform cover logic (that one keeps its own <100 threshold
in usePlatformCustomTheme.measureBrightness).

Metric: perceptual luminance (0.299*R + 0.587*G + 0.114*B) averaged over a
64x64 resize — the exact same formula the frontend uses in
frontend/utils/colorUtils.js::measureBrightness, so values are comparable.

Usage:
    python3 frontend/scripts/classify-gallery-brightness.py
    python3 frontend/scripts/classify-gallery-brightness.py --threshold 120
    python3 frontend/scripts/classify-gallery-brightness.py --report   # print only, no write
"""
import argparse
import json
import os
from urllib.parse import quote

from PIL import Image

# Paths resolved relative to this script: frontend/scripts/ -> repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
GALLERY_DIR = os.path.join(REPO_ROOT, "backend", "static", "cover_gallery")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "..", "assets", "data", "cover-gallery.json")

SIZE = 64
STATIC_PREFIX = "/static/cover_gallery"
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def brightness(path):
    """Average perceptual luminance (0-255) of an image on a 64x64 resize."""
    img = Image.open(path).convert("RGB").resize((SIZE, SIZE))
    px = img.load()
    total = 0.0
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b = px[x, y]
            total += r * 0.299 + g * 0.587 + b * 0.114
    return total / (SIZE * SIZE)


def display_name(filename):
    """Mirror backend cover_gallery_view: strip imgi_XX_ prefix, Title Case."""
    name_part = filename.rsplit(".", 1)[0]
    parts = name_part.split("_", 2)
    name = parts[2] if len(parts) > 2 else name_part
    return name.replace("_", " ").title()


def collect(threshold):
    images = []
    for category in sorted(os.listdir(GALLERY_DIR)):
        cat_path = os.path.join(GALLERY_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for filename in sorted(os.listdir(cat_path)):
            if not filename.lower().endswith(EXTS):
                continue
            rel = f"{category}/{filename}"
            b = round(brightness(os.path.join(cat_path, filename)), 1)
            images.append({
                "category": category,
                "filename": filename,
                "name": display_name(filename),
                "path": rel,
                "url": f"{STATIC_PREFIX}/{quote(category)}/{quote(filename)}",
                "brightness": b,
                "tone": "light" if b >= threshold else "dark",
            })
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=120,
                        help="brightness >= threshold => light (default: 120)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="output JSON path")
    parser.add_argument("--report", action="store_true",
                        help="print classification only, do not write the file")
    args = parser.parse_args()

    if not os.path.isdir(GALLERY_DIR):
        raise SystemExit(f"Gallery dir not found: {GALLERY_DIR}")

    images = collect(args.threshold)
    light = [i for i in images if i["tone"] == "light"]
    dark = [i for i in images if i["tone"] == "dark"]

    # Per-category summary to stdout
    print(f"threshold={args.threshold}  total={len(images)}  "
          f"light={len(light)}  dark={len(dark)}\n")
    cats = {}
    for i in images:
        cats.setdefault(i["category"], []).append(i)
    print(f"{'category':34s} light dark")
    for cat in sorted(cats):
        ci = cats[cat]
        nl = sum(1 for x in ci if x["tone"] == "light")
        print(f"{cat:34s} {nl:4d} {len(ci) - nl:4d}")

    if args.report:
        print("\n(report mode: no file written)")
        return

    manifest = {
        "generatedBy": "frontend/scripts/classify-gallery-brightness.py",
        "metric": "perceptual luminance (0.299R+0.587G+0.114B) on 64x64 resize; "
                  "matches frontend/utils/colorUtils.js measureBrightness",
        "threshold": args.threshold,
        "counts": {"total": len(images), "light": len(light), "dark": len(dark)},
        "images": images,
    }
    out_path = os.path.normpath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
