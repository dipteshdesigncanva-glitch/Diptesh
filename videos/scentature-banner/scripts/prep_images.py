"""Build the image assets in public/ from the original product photos.

Usage: python3 scripts/prep_images.py <dir with 1.png 2.webp 3.webp 4.webp 5.webp>

- logo-white.png: the black-on-white Scentature logo turned into white on transparent.
- bottles/<id>.png: each bottle cut out of its 1086x1448 photo. All four photos use
  the same bottle mockup in the same spot, so one hand-measured mask (a rounded cap
  plus a rounded glass body) fits every bottle.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "public"

PRODUCTS = {
    "bad-girl": "2.webp",
    "floral-kiss": "3.webp",
    "hawas-classic": "4.webp",
    "hawas-ice": "5.webp",
}

# Bottle geometry in the source photos (pixels)
CAP = (439, 358, 638, 606)
BODY = (312, 597, 773, 1224)
CROP = (296, 346, 789, 1238)


def make_logo() -> None:
    im = Image.open(SRC / "1.png").convert("L")
    # Dark ink becomes opaque, white paper becomes transparent
    alpha = np.asarray(im).astype(np.float32)
    alpha = np.clip((255 - alpha) * 1.15, 0, 255).astype(np.uint8)
    bbox = Image.fromarray(alpha).point(lambda v: 255 if v > 20 else 0).getbbox()
    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = alpha
    Image.fromarray(rgba).crop(bbox).save(OUT / "logo-white.png")


def bottle_mask(size: tuple[int, int]) -> Image.Image:
    # Draw at 4x and scale down for smooth, anti-aliased edges
    s = 4
    mask = Image.new("L", (size[0] * s, size[1] * s), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([v * s for v in CAP], radius=10 * s, fill=255)
    x0, y0, x1, y1 = BODY
    d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=72 * s, fill=255)
    # Square off the bottom corners a little: the base is flatter than the shoulders
    d.rounded_rectangle([x0 * s, (y0 + 200) * s, x1 * s, y1 * s], radius=44 * s, fill=255)
    mask = mask.resize(size, Image.LANCZOS)
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def make_bottle(product_id: str, filename: str) -> None:
    photo = Image.open(SRC / filename).convert("RGB")
    rgba = photo.convert("RGBA")
    rgba.putalpha(bottle_mask(photo.size))
    rgba.crop(CROP).save(OUT / "bottles" / f"{product_id}.png")


if __name__ == "__main__":
    (OUT / "bottles").mkdir(parents=True, exist_ok=True)
    make_logo()
    for pid, fn in PRODUCTS.items():
        make_bottle(pid, fn)
    print("done")
