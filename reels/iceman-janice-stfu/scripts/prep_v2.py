"""v2 elements: ice-cube backdrops/texture, shatter overlay, player-card art."""
import sys

import numpy as np
from PIL import Image, ImageFilter

IMG, A = sys.argv[1], sys.argv[2]  # source images dir, assets dir
W, H = 1920, 1080
INK = np.array((10, 11, 15), np.float32)
DEEP = np.array((9, 26, 78), np.float32)
ICE = np.array((38, 104, 255), np.float32)
FROST = np.array((178, 226, 255), np.float32)
WHITE = np.array((255, 255, 255), np.float32)


def cover(im, w, h, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    y0 = int((im.height - h) * fy)
    x0 = (im.width - w) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def gradmap(lum, stops):
    """lum 0..1 -> colour along stops [(pos, rgb), ...]"""
    out = np.zeros(lum.shape + (3,), np.float32)
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        m = (lum >= p0) & (lum <= p1)
        u = ((lum[m] - p0) / (p1 - p0))[:, None]
        out[m] = c0 * (1 - u) + c1 * u
    return out


def lum_of(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    return a @ np.array([0.299, 0.587, 0.114], np.float32)


cubes = Image.open(f"{IMG}/5.webp").convert("RGB")
big = cover(cubes, int(W * 1.15), int(H * 1.15), 0.45)
L = lum_of(big)
Lc = np.clip((L - 0.12) / 0.8, 0, 1)
# bright ice texture for letter fills
tex = gradmap(Lc ** 0.9, [(0, DEEP), (0.35, ICE), (0.75, FROST), (1.0, WHITE)])
Image.fromarray(tex.astype(np.uint8)).crop((0, 0, W, H)).save(f"{A}/ice_tex.jpg", quality=93)
# mid-dark scene backdrop (white puffer must pop on it)
bg = gradmap(Lc ** 1.25, [(0, INK), (0.45, DEEP), (0.85, ICE * 0.85), (1.0, FROST)])
Image.fromarray(bg.astype(np.uint8)).save(f"{A}/ice_bg.jpg", quality=93)
# very dark, defocused hook backdrop (UI cards sit on it)
hook = Image.fromarray((gradmap(Lc ** 1.4, [(0, INK), (0.6, DEEP), (1.0, ICE * 0.7)])).astype(np.uint8))
hook.filter(ImageFilter.GaussianBlur(9)).save(f"{A}/ice_hook.jpg", quality=93)

# shatter overlay: keep as-is (bright shards on black, used with screen blend)
Image.open(f"{IMG}/6.webp").convert("RGB").save(f"{A}/ice_shatter.jpg", quality=95)

# album-style art for the player card: colour glove crop
g = Image.open(f"{A}/1.jpg").convert("RGB")
g.crop((150, 400, 850, 1100)).resize((500, 500), Image.LANCZOS).save(f"{A}/art_glove.jpg", quality=93)
print("ok")
