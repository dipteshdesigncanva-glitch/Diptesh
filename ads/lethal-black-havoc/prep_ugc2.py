"""Luminance mattes with hole-fill for products on near-black backgrounds."""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FR, CL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]


def tight(im, pad=4):
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 10)
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad + 1, ys.max() + pad + 1))


def silhouette(rgb, thr=60, fill_holes=True, close=3, feather=1.2):
    """alpha = inside the outer silhouette of bright pixels."""
    a = np.asarray(rgb.convert("RGB")).astype(np.int16)
    bright = (a.max(2) > thr).astype(np.uint8) * 255
    m = Image.fromarray(bright, "L")
    if close:  # dilate then erode to close tiny gaps in the outline
        m = m.filter(ImageFilter.MaxFilter(close * 2 + 1)).filter(ImageFilter.MinFilter(close * 2 + 1))
    if fill_holes:
        pad = Image.new("L", (m.width + 2, m.height + 2), 0)
        pad.paste(m, (1, 1))
        ImageDraw.floodfill(pad, (0, 0), 100)
        arr = np.asarray(pad)[1:-1, 1:-1]
        m = Image.fromarray(np.where(arr == 100, 0, 255).astype(np.uint8), "L")
    # drop isolated specks
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    return m.filter(ImageFilter.GaussianBlur(feather))


def soft_matte(rgb, lo=45, hi=85):
    a = np.asarray(rgb.convert("RGB")).astype(np.float32).max(2)
    al = np.clip((a - lo) / (hi - lo), 0, 1)
    return Image.fromarray((al * 255).astype(np.uint8), "L")


def save(rgb, alpha, name, drop_red=False):
    im = rgb.convert("RGBA")
    if drop_red:
        a = np.asarray(rgb.convert("RGB")).astype(np.int16)
        red = (a[..., 0] > 140) & (a[..., 1] < 70) & (a[..., 2] < 110)
        al = np.asarray(alpha).copy()
        al[red] = 0
        alpha = Image.fromarray(al, "L")
    im.putalpha(alpha)
    im = tight(im)
    im.save(f"{OUT}/{name}.png")
    print(name, im.size)


# RGB keyboard clip: one static silhouette from the fully lit frame, reused per frame
lit = Image.open(f"{CL}/rgb/069.jpg")
sil = silhouette(lit, 40, True, 4)
sil.save(f"{OUT}/rgb_matte.png")
save(lit, sil, "kb_rgb")

hero = Image.open(f"{FR}/t1.0.png").convert("RGB").crop((86, 340, 1000, 880))
save(hero, silhouette(hero, 55, True, 4), "kb_hero")
gas = Image.open(f"{FR}/t8.6.png").convert("RGB").crop((440, 290, 1460, 665))
save(gas, silhouette(gas, 70, True, 4), "kb_gasket")

vt = Image.open(f"{CL}/venom/013.jpg").convert("RGB").crop((105, 560, 398, 818))
save(vt, soft_matte(vt, 50, 90), "sw_top", drop_red=True)
vb = Image.open(f"{CL}/venom/038.jpg").convert("RGB")
base = vb.crop((85, 280, 440, 535))
save(base, soft_matte(base, 50, 90), "sw_base", drop_red=True)
spr = vb.crop((235, 68, 320, 275))
save(spr, soft_matte(spr, 50, 95), "sw_spring", drop_red=True)
stem = Image.open(f"{CL}/venom/026.jpg").convert("RGB").crop((190, 195, 350, 460))
save(stem, soft_matte(stem, 50, 90), "sw_stem", drop_red=True)
