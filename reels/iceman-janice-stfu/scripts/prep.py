"""Prepare treated assets: tight-cropped B&W/halftone cutouts + Iceman logo mask."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

A = sys.argv[1]  # assets dir


def tight(im):
    a = np.array(im)[..., 3]
    ys, xs = np.where(a > 8)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def bw(im, black=0.06, white=0.92, gamma=0.95, halftone=0.0, cell=7):
    """High-contrast mono with optional halftone texture blended in."""
    arr = np.asarray(im).astype(np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3]
    g = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    g = np.clip((g - black) / (white - black), 0, 1) ** gamma
    # s-curve for punch
    g = g * g * (3 - 2 * g) * 0.55 + g * 0.45
    if halftone > 0:
        h, w = g.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        # 45deg rotated dot screen
        u = (xx + yy) / (cell * 1.4142)
        v = (xx - yy) / (cell * 1.4142)
        d = np.sqrt((u - np.round(u)) ** 2 + (v - np.round(v)) ** 2) / 0.7071  # 0 centre -> 1 corner
        # dark tone -> big dot
        dot = (d > np.sqrt(np.clip(1 - g, 0, 1)) * 1.0).astype(np.float32)
        soft = np.clip((d - np.sqrt(np.clip(1 - g, 0, 1))) * 6 + 0.5, 0, 1)
        g = g * (1 - halftone) + soft * halftone
    out = np.dstack([g, g, g, a])
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def save(im, name):
    im.save(f"{A}/{name}.png")
    print(name, im.size)


# --- cutouts ---------------------------------------------------------------
glove = tight(Image.open(f"{A}/1_birefnet-portrait.png").convert("RGBA"))
grin = Image.open(f"{A}/2_birefnet-portrait.png").convert("RGBA")
# erase the second person's head behind the left shoulder
m = Image.new("L", grin.size, 0)
ImageDraw.Draw(m).ellipse((105, 425, 262, 668), fill=255)
m = m.filter(ImageFilter.GaussianBlur(10))
a = np.array(grin)
a[..., 3] = (a[..., 3] * (1 - np.array(m) / 255)).astype(np.uint8)
grin = tight(Image.fromarray(a, "RGBA"))
stage = tight(Image.open(f"{A}/3_birefnet-portrait.png").convert("RGBA"))
coat = tight(Image.open(f"{A}/4top_birefnet-portrait.png").convert("RGBA"))
coat = coat.resize((coat.width * 2, coat.height * 2), Image.LANCZOS)
seat = tight(Image.open(f"{A}/4bot_birefnet-portrait.png").convert("RGBA"))
seat = seat.resize((seat.width * 3, seat.height * 3), Image.LANCZOS)

for name, im, kw in [
    ("glove", glove, dict(black=0.03, white=0.85)),
    ("grin", grin, dict(black=0.08, white=0.95)),
    ("stage", stage, dict(black=0.02, white=0.75, gamma=0.85)),
    ("coat", coat, dict(black=0.25, white=0.98, gamma=1.2)),
    ("seat", seat, dict(black=0.35, white=0.55)),
]:
    save(bw(im, **kw), f"{name}_bw")
    save(bw(im, halftone=0.55, cell=6, **kw), f"{name}_ht")
# colour versions kept for the glove sparkle shots
save(glove, "glove_rgb")

# full-frame mono backplates (for panels / collage)
for src, name in [("2.jpg", "grin_plate"), ("3.jpg", "stage_plate"), ("4top.jpg", "coat_plate"), ("1.jpg", "glove_plate")]:
    im = Image.open(f"{A}/{src}").convert("RGBA")
    save(bw(im, black=0.04, white=0.9, halftone=0.35, cell=6), name)

# --- Iceman logo ---------------------------------------------------------------
src = np.asarray(Image.open(f"{A}/4.jpg").convert("RGB")).astype(np.float32)[0:140, 540:1080]
mn = src.min(2)
mask = np.clip((mn - 150) / 60, 0, 1)
mask[:, :24] = 0  # ice block on the left
mask[:30, 380:460] = 0  # CN tower tip
mask[:52, 395:430] = 0
L = Image.fromarray((mask * 255).astype(np.uint8), "L")
L = L.resize((L.width * 4, L.height * 4), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2.2))
la = np.asarray(L).astype(np.float32) / 255
la = np.clip((la - 0.5) * 5 + 0.5, 0, 1)  # re-sharpen to vector-like edge
logo = np.zeros((*la.shape, 4), np.uint8)
logo[..., :3] = 255
logo[..., 3] = (la * 255).astype(np.uint8)
save(tight(Image.fromarray(logo, "RGBA")), "logo")
