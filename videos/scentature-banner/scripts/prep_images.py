"""Build the image assets in public/ from the original product photos.

Usage: python3 scripts/prep_images.py <dir with 1.png 2.webp 3.webp 4.webp 5.webp>

- logo-white.png: the black-on-white Scentature logo turned into white on transparent.
- plates/<id>.jpg: each 1086x1448 bottle photo placed on a 1920x1080 canvas with the
  bottle on the right. The empty area is filled by stretching the photo's own edge
  columns, so the black wall and grey floor continue seamlessly.
- cards/<id>.jpg: a tight portrait crop of each bottle for the closing line-up.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SRC = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "public"
W, H = 1920, 1080

# Photo scale and placement in the 1920x1080 plate
SCALE = 0.82
PHOTO_LEFT = 905
PHOTO_TOP = -82

PRODUCTS = {
    "bad-girl": "2.webp",
    "floral-kiss": "3.webp",
    "hawas-classic": "4.webp",
    "hawas-ice": "5.webp",
}


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


def edge_fill(strip: np.ndarray, width: int) -> np.ndarray:
    """Repeat the average of an edge strip horizontally, lightly blurred vertically."""
    col = strip.mean(axis=1, keepdims=True)
    col_img = Image.fromarray(np.repeat(col, 8, axis=1).astype(np.uint8))
    col = np.asarray(col_img.filter(ImageFilter.GaussianBlur(3))).astype(np.float32)[:, :1]
    return np.repeat(col, width, axis=1)


def make_plate(product_id: str, filename: str) -> None:
    photo = Image.open(SRC / filename).convert("RGB")
    pw, ph = int(photo.width * SCALE), int(photo.height * SCALE)
    photo = photo.resize((pw, ph), Image.LANCZOS)

    canvas = Image.new("RGB", (W, H))
    canvas.paste(photo, (PHOTO_LEFT, PHOTO_TOP))
    arr = np.asarray(canvas).astype(np.float32)

    right = PHOTO_LEFT + pw
    left_fill = edge_fill(arr[:, PHOTO_LEFT + 2 : PHOTO_LEFT + 18], PHOTO_LEFT)
    arr[:, :PHOTO_LEFT] = left_fill
    if right < W:
        right_fill = edge_fill(arr[:, right - 18 : right - 2], W - right)
        arr[:, right:] = right_fill

    # Feather the seams so the stretched area melts into the photo
    for seam, direction in ((PHOTO_LEFT, 1), (right, -1)):
        if seam >= W:
            continue
        for i in range(60):
            x = seam + direction * i
            t = i / 60
            src = arr[:, seam - direction * 1]
            arr[:, x] = arr[:, x] * t + src * (1 - t)

    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
        OUT / "plates" / f"{product_id}.jpg", quality=92
    )


def make_card(product_id: str, filename: str) -> None:
    photo = Image.open(SRC / filename).convert("RGB")
    card = photo.crop((193, 170, 893, 1448))  # 700x1278, bottle centred
    card = card.resize((420, 767), Image.LANCZOS)
    card.save(OUT / "cards" / f"{product_id}.jpg", quality=92)


if __name__ == "__main__":
    (OUT / "plates").mkdir(parents=True, exist_ok=True)
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    make_logo()
    for pid, fn in PRODUCTS.items():
        make_plate(pid, fn)
        make_card(pid, fn)
    print("done")
