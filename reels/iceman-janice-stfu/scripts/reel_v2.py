"""ICEMAN // JANICE STFU (v2) — 30s 16:9 hook-first kinetic edit.

Hook: a 3D chat/player-card mini story ("Janice" texts, he types "stfu") whose
sent bubble swells to fill the screen, cracks like ice in the pre-drop silence
and shatters into flying shards on the 808 drop. The body is the poster-collage
edit (B&W halftone cutouts, giant type) with phone-UI cards, zoom-blur
tunnels, arc-warped and motion-blurred type, and the ice-cube / ice-shatter
elements. Payoff: Janice gets blocked, the screen shatters, logo with god rays.

Every frame is a pure function of its time, so frames render in parallel and
pipe straight into ffmpeg. Timing is in beats of the song (125.82 BPM).
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.environ.get("REEL_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = f"{ROOT}/assets"
FONTS = f"{ROOT}/fonts"

W, H, FPS, DUR = 1920, 1080, 30, 30.0
NF = int(DUR * FPS)
BEAT = 3.8151 / 8  # seconds per beat (125.82 BPM)
# the edit ends exactly on a bar line, 56 beats after the drop (beat 8)
DROP_T = DUR - 56 * BEAT
K0 = 8 - DROP_T / BEAT  # beat number at t = 0
LEAD = 0.02  # pictures lead the audio by a hair so hits land on the frame the 808 starts


def tb(k):
    """edit time (s) of beat k"""
    return (k - K0) * BEAT


INK = (10, 11, 15)
PAPER = (236, 238, 241)
ICE = (38, 104, 255)
DEEP = (9, 26, 78)
FROST = (178, 226, 255)
GREY = (128, 132, 140)
UIGREY = (46, 46, 52)

HITS = [8, 11, 16, 19, 24, 27, 32, 35, 40, 43, 48, 51, 56, 59]
BARS = {8, 16, 24, 32, 40, 48, 56}
HOOK_TAPS = [3, 4, 5, 5.5, 6, 6.5, 7]

# ---------------------------------------------------------------- utilities


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def eo_expo(p):
    p = clamp(p)
    return 1 - 2 ** (-10 * p) if p < 1 else 1.0


def eo_back(p, s=1.9):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def eio(p):
    p = clamp(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


INTER = "/usr/share/fonts/opentype/inter"
FONT_FILES = {
    "anton": f"{FONTS}/Anton-Regular.ttf",
    "wide": f"{FONTS}/Unbounded%5Bwght%5D.ttf",
    "inter": f"{INTER}/Inter-Bold.otf",
    "interm": f"{INTER}/Inter-SemiBold.otf",
    "disp": f"{INTER}/InterDisplay-Bold.otf",
    "dispx": f"{INTER}/InterDisplay-Black.otf",
}
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


@lru_cache(maxsize=256)
def F(key, size):
    f = ImageFont.truetype(FONT_FILES[key], size)
    if key == "wide":
        f.set_variation_by_axes([900])
    return f


@lru_cache(maxsize=1024)
def cap(key, size):
    return -F(key, size).getbbox("H", anchor="ls")[1]


@lru_cache(maxsize=1500)
def glyph(key, size, ch, fill, stroke=0):
    """Sprite for one character; returns (img, dx, dy) relative to the baseline origin."""
    f = F(key, size)
    l, t, r, b = f.getbbox(ch, anchor="ls", stroke_width=stroke)
    im = Image.new("RGBA", (max(1, r - l + 4), max(1, b - t + 4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if stroke:
        d.text((-l + 2, -t + 2), ch, font=f, anchor="ls", fill=(0, 0, 0, 0),
               stroke_width=stroke, stroke_fill=fill)
    else:
        d.text((-l + 2, -t + 2), ch, font=f, anchor="ls", fill=fill)
    return im, l - 2, t - 2


@lru_cache(maxsize=512)
def tsprite(key, size, s, fill):
    """Whole string (keeps kerning). Returns (img, dx, dy) relative to baseline-left origin."""
    f = F(key, size)
    l, t, r, b = f.getbbox(s, anchor="ls")
    im = Image.new("RGBA", (max(1, r - l + 4), max(1, b - t + 4)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l + 2, -t + 2), s, font=f, anchor="ls", fill=fill)
    return im, l - 2, t - 2


@lru_cache(maxsize=32)
def emoji(ch, px):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((px, int(px * im.height / im.width)), Image.LANCZOS)


def layout(key, size, word, track=0.0):
    f = F(key, size)
    xs, x = [], 0.0
    for ch in word:
        xs.append(x)
        x += f.getlength(ch) + track * size
    return xs, x - track * size


def comp(c, sp, x, y):
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sp.width, c.width - x), min(sp.height, c.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, sp.width, sp.height):
        sp = sp.crop((sx0, sy0, sx1, sy1))
    c.alpha_composite(sp, (x + sx0, y + sy0))


def fade(sp, a):
    if a >= 1:
        return sp
    sp = sp.copy()
    al = sp.getchannel("A").point(lambda v: int(v * a))
    sp.putalpha(al)
    return sp


def scaled(im, s):
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    return im if (w, h) == im.size else im.resize((w, h), Image.BILINEAR)


def fill(c, col):
    c.paste(rgba(col), (0, 0, c.width, c.height))


def texture_glyph(sp, gx, gy, tex):
    """Replace a glyph sprite's colour with the texture under it (keeps alpha)."""
    region = tex.crop((int(gx), int(gy), int(gx) + sp.width, int(gy) + sp.height)).convert("RGBA")
    region.putalpha(sp.getchannel("A"))
    return region


def draw_word(c, key, size, word, x, base, fill_col, *, track=0.0, appear=None, lb=0.0,
              stroke=0, slam=0.3, grey_flash=True, align="left", tex=None):
    """Draw a word letter by letter. appear: list of beat times per letter (None = all visible)."""
    xs, total = layout(key, size, word, track)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        at = appear[i] if appear is not None else -99
        if lb < at:
            continue
        age = lb - at
        col = fill_col
        flash_now = grey_flash and age < 0.12 and appear is not None
        if flash_now:
            col = (PAPER if tex is not None else GREY) if not stroke else fill_col
        sp, dx, dy = glyph(key, size, ch, rgba(col), stroke)
        s = 1 + slam * (1 - eo_expo(age / 0.3)) if appear is not None else 1.0
        gx, gy = x + xs[i] + dx, base + dy
        if s != 1.0:
            sp2 = scaled(sp, s)
            gx -= (sp2.width - sp.width) / 2
            gy -= (sp2.height - sp.height) / 2
            sp = sp2
        if tex is not None and not flash_now:
            sp = texture_glyph(sp, gx, gy, tex)
        comp(c, sp, gx, gy)
    return total


def word_sprite(key, size, word, col, track=0.0, stroke=0, pad=10):
    xs, total = layout(key, size, word, track)
    f = F(key, size)
    l, t, r, b = f.getbbox(word, anchor="ls", stroke_width=stroke)
    hgt = b - t + 2 * pad
    im = Image.new("RGBA", (int(total + 2 * pad + 2 * stroke + 4), int(hgt)), (0, 0, 0, 0))
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        sp, dx, dy = glyph(key, size, ch, rgba(col), stroke)
        im.alpha_composite(sp, (int(pad + xs[i] + dx + stroke), int(pad - t + dy)))
    return im


def box_text(key, size, word, col, box_col, padx=0.18, pady=0.16, track=0.0):
    """Word on a solid box (caption chip). Returns sprite."""
    ws = word_sprite(key, size, word, col, track, pad=0)
    ch = cap(key, size)
    px, py = int(size * padx), int(size * pady)
    f = F(key, size)
    l, t, r, b = f.getbbox(word, anchor="ls")
    im = Image.new("RGBA", (ws.width + 2 * px, ch + 2 * py), rgba(box_col))
    im.alpha_composite(ws, (px, py + (t + ch)))
    return im


def burst(d, cx, cy, r_out, r_in, n, rot, col):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=col)


def rays(d, cx, cy, n, rot, col, r=4000, width=0.5):
    for i in range(n):
        a0 = rot + 2 * math.pi * i / n
        a1 = a0 + 2 * math.pi / n * width
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=col)


def rot_sprite(sp, deg):
    return sp.rotate(deg, Image.BICUBIC, expand=True) if deg else sp


def put(c, sp, cx, cy, s=1.0, rot=0.0, a=1.0):
    """Composite sprite centred at (cx, cy) with scale/rotation/alpha."""
    sp = scaled(sp, s)
    sp = rot_sprite(sp, rot)
    sp = fade(sp, a)
    comp(c, sp, cx - sp.width / 2, cy - sp.height / 2)


def put_bottom(c, im, cx, bottom, h, rot=0.0, a=1.0, flip=False):
    sp = scaled(im, h / im.height)
    if flip:
        sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        put(c, sp, cx, bottom - sp.height / 2, 1.0, rot, a)
        return
    sp = fade(sp, a)
    comp(c, sp, cx - sp.width / 2, bottom - sp.height)


def cover(im, w, h, fx=0.5, fy=0.4, z=1.0):
    s = max(w / im.width, h / im.height) * z
    sp = scaled(im, s)
    x0 = int((sp.width - w) * fx)
    y0 = int((sp.height - h) * fy)
    return sp.crop((x0, y0, x0 + w, y0 + h))


def round_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def smear_sprite(sp, k):
    """Horizontal motion blur for a moving sprite (k = blur factor >= 1)."""
    if k <= 1.2:
        return sp
    w, h = sp.size
    return sp.resize((max(2, int(w / k)), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)


def shear_sprite(sp, sh):
    """Italic-style shear (positive leans right)."""
    if abs(sh) < 0.01:
        return sp
    w, h = sp.size
    extra = int(abs(sh) * h)
    off = -sh * h if sh > 0 else 0
    return sp.transform((w + extra, h), Image.AFFINE, (1, sh, off, 0, 1, 0), Image.BICUBIC)


def arc_warp(sp, amount):
    """Bend a sprite into an arch: centre columns rise, edges drop (Illustrator 'Arc')."""
    a = np.asarray(sp)
    h, w = a.shape[:2]
    amt = int(amount)
    xs = (np.arange(w) - w / 2) / (w / 2)
    shift = (amt * xs ** 2).astype(np.int32)
    rows = np.arange(h + amt)[:, None] - shift[None, :]
    valid = (rows >= 0) & (rows < h)
    out = a[np.clip(rows, 0, h - 1), np.arange(w)[None, :]]
    out = out * valid[..., None]
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- 3D cards


def _rot(rx, ry, rz):
    ax, ay, az = map(math.radians, (rx, ry, rz))
    ca, sa, cb, sb, cc, sc = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def proj_pts(pts, R, s, cx, cy, f=1700.0):
    P = (np.asarray(pts, float) * s) @ R.T
    z = P[:, 2] + f
    return np.stack([cx + f * P[:, 0] / z, cy + f * P[:, 1] / z], 1)


def put3d(c, sp, cx, cy, rx=0.0, ry=0.0, rz=0.0, s=1.0, a=1.0, f=1700.0):
    """Composite a flat sprite rotated in 3D and perspective-projected, centred at (cx, cy)."""
    w, h = sp.size
    quad = proj_pts([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]],
                    _rot(rx, ry, rz), s, cx, cy, f)
    x0 = max(0, int(math.floor(quad[:, 0].min())))
    y0 = max(0, int(math.floor(quad[:, 1].min())))
    x1 = min(c.width, int(math.ceil(quad[:, 0].max())))
    y1 = min(c.height, int(math.ceil(quad[:, 1].max())))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    dst = quad - [x0, y0]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    M, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        M.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        B.append(X)
        M.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        B.append(Y)
    co = np.linalg.solve(np.array(M), np.array(B))
    out = sp.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    c.alpha_composite(fade(out, a), (x0, y0))


def proj_point(px, py, w, h, rx, ry, rz, s, cx, cy, f=1700.0):
    return proj_pts([[px - w / 2, py - h / 2, 0]], _rot(rx, ry, rz), s, cx, cy, f)[0]


# ---------------------------------------------------------------- assets

def load(name):
    return Image.open(f"{ASSETS}/{name}.png").convert("RGBA")


A = {n: load(n) for n in [
    "glove_bw", "glove_ht", "grin_bw", "grin_ht", "stage_bw", "stage_ht", "coat_bw", "coat_ht",
    "seat_bw", "seat_ht", "grin_plate", "stage_plate", "coat_plate", "glove_plate", "logo"]}
ICE_TEX = Image.open(f"{ASSETS}/ice_tex.jpg").convert("RGB")
ICE_BG = Image.open(f"{ASSETS}/ice_bg.jpg").convert("RGB")  # 1.15x frame size
ICE_HOOK = Image.open(f"{ASSETS}/ice_hook.jpg").convert("RGB")  # 1.15x frame size
SHAT = Image.open(f"{ASSETS}/ice_shatter.jpg").convert("RGB")
ART = Image.open(f"{ASSETS}/art_glove.jpg").convert("RGB").resize((248, 248), Image.LANCZOS)
ART_R = ART.convert("RGBA")
ART_R.putalpha(round_mask(248, 248, 26))

SWIRL = Image.new("RGBA", (2400, 1500), (0, 0, 0, 0))
_d = ImageDraw.Draw(SWIRL)
for (sx, sy, sr, turns, ph) in [(300, 260, 360, 2.3, 0.0), (1150, 1050, 420, 2.6, 1.3),
                                (2050, 330, 380, 2.4, 2.4), (1950, 1300, 300, 2.0, 0.7),
                                (500, 1250, 300, 2.1, 3.1), (1250, 200, 260, 1.8, 4.0)]:
    for i in range(2600):
        u = i / 2599
        a = ph + u * turns * 2 * math.pi
        r = sr * (0.12 + 0.88 * u)
        px, py = sx + r * math.cos(a), sy + r * math.sin(a)
        _d.ellipse((px - 31, py - 31, px + 31, py + 31), fill=(255, 255, 255, 255))
del _d

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.75)) ** 2)
_t = np.clip(_r, 0, 1)[..., None]
END_BG = Image.fromarray((np.array(DEEP) * (1 - _t) + np.array(INK) * _t).astype(np.uint8), "RGB").convert("RGBA")
VIG = (1 - 0.32 * np.clip(_r - 0.45, 0, 1) ** 1.5)[..., None].astype(np.float32)
DIST_C = np.sqrt((_xx - W / 2) ** 2 + (_yy - H / 2) ** 2).astype(np.float32)
del _yy, _xx, _r, _t

LOGO = scaled(A["logo"], 1320 / A["logo"].width)


def glow_of(sp, col, radius, pad=120):
    g = Image.new("RGBA", (sp.width + 2 * pad, sp.height + 2 * pad), (0, 0, 0, 0))
    tint = Image.new("RGBA", sp.size, rgba(col))
    tint.putalpha(sp.getchannel("A"))
    g.alpha_composite(tint, (pad, pad))
    return g.filter(ImageFilter.GaussianBlur(radius))


LOGO_GLOW = glow_of(LOGO, ICE, 28, 100)


def _god_rays():
    """Logo light rays: radial (zoom) blur of the logo, as in the reference end cards."""
    base = Image.new("L", (W // 2, H // 2), 0)
    lg = scaled(LOGO.getchannel("A"), 0.5)
    base.paste(lg, (W // 4 - lg.width // 2, H // 4 - 20 - lg.height // 2))
    cx, cy = W / 4, H / 4 - 20
    acc = np.zeros((H // 2, W // 2), np.float32)
    n = 32
    for i in range(n):
        z = 1 + 1.4 * i / (n - 1)
        a = 1 / z
        tr = base.transform(base.size, Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy), Image.BILINEAR)
        acc += np.asarray(tr, np.float32) * (1 - i / n) ** 1.2
    acc = acc / acc.max()
    img = Image.fromarray((np.clip(acc * 1.6, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(img).astype(np.float32) / 255


RAYS = _god_rays()

_rng = np.random.default_rng(7)
SNOW = [(float(_rng.uniform(0, W)), float(_rng.uniform(0, H)), float(_rng.uniform(1.5, 5.5)),
        float(_rng.uniform(25, 90)), float(_rng.uniform(0, 6.28))) for _ in range(150)]
GRAIN = []
for i in range(6):
    g = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    GRAIN.append(np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR)))


def snow(c, t, alpha=120, speed=1.0):
    dr = ImageDraw.Draw(c)
    for (x, y, r, sp, ph) in SNOW:
        yy = (y + sp * t * speed) % H
        xx = x + 18 * math.sin(t * 0.9 + ph)
        dr.ellipse((xx - r, yy - r, xx + r, yy + r), fill=rgba(FROST, alpha))


def kb(big, zoom, ox=0.0, oy=0.0):
    """Ken-Burns crop from a 1.15x backdrop: zoom 1.0 = widest."""
    q = 1.0 / zoom
    w, h = int(W * 1.15 * q), int(H * 1.15 * q)
    x0 = int((big.width - w) / 2 + ox)
    y0 = int((big.height - h) / 2 + oy)
    x0 = max(0, min(big.width - w, x0))
    y0 = max(0, min(big.height - h, y0))
    return big.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BILINEAR).convert("RGBA")


# ---------------------------------------------------------------- ice shatter geometry


class Shatter:
    """Voronoi shard map with radial seed rings around an impact point."""

    def __init__(self, seed, cx, cy, n=17, rings=(85, 200, 360, 570, 840, 1180, 1650)):
        rng = np.random.default_rng(seed)
        self.cx, self.cy = cx, cy
        hs = 2
        ys, xs = np.mgrid[0:H // hs, 0:W // hs].astype(np.float32)
        dx, dy = xs * hs + 1 - cx, ys * hs + 1 - cy
        r = np.sqrt(dx * dx + dy * dy)
        th = np.arctan2(dy, dx)
        # jagged radial cracks
        ph1, ph2 = rng.uniform(0, 6.28, 2)
        thw = (th + (0.016 * np.sin(r / 23 + ph1) + 0.009 * np.sin(r / 8 + ph2)) * np.minimum(1, 300 / (r + 1))
               ) % (2 * np.pi)
        a0 = rng.uniform(0, 2 * np.pi)
        ang = np.sort((a0 + (np.arange(n) + rng.uniform(-0.32, 0.32, n)) * 2 * np.pi / n) % (2 * np.pi))
        sec = np.searchsorted(ang, thw) % n  # sector between ang[sec-1] and ang[sec]
        lo = ang[(sec - 1) % n]
        hi = ang[sec]
        width = (hi - lo) % (2 * np.pi)
        mid = lo + width / 2
        rel = (thw - mid + np.pi) % (2 * np.pi) - np.pi
        ring = np.zeros(r.shape, np.int16)
        for R in rings:  # concentric cracks as straight chords between neighbouring rays
            Rs = (R * rng.uniform(0.8, 1.2, n)).astype(np.float32)
            rc = Rs[sec] * np.cos(width / 2) / np.maximum(np.cos(rel), 0.2)
            ring += (r > rc).astype(np.int16)
        lab = (ring * n + sec).astype(np.int16)
        self.lab = np.repeat(np.repeat(lab, hs, 0), hs, 1)
        e = (self.lab != np.roll(self.lab, 1, 0)) | (self.lab != np.roll(self.lab, 1, 1))
        e[0, :] = e[:, 0] = False
        self.edge = e.astype(np.float32)
        self.glow = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(5))).astype(np.float32) / 255 * 2.2
        self.dist = np.sqrt((np.arange(W)[None, :] - cx) ** 2 + (np.arange(H)[:, None] - cy) ** 2).astype(np.float32)
        self.shards = []
        order = np.argsort(lab, axis=None, kind="stable")
        flat = lab.ravel()[order]
        bounds = np.searchsorted(flat, np.arange(lab.max() + 2))
        for i in range(lab.max() + 1):
            idx = order[bounds[i]:bounds[i + 1]]
            if len(idx) == 0:
                continue
            ys_, xs_ = np.unravel_index(idx, lab.shape)
            x0, x1 = xs_.min() * hs, (xs_.max() + 1) * hs
            y0, y1 = ys_.min() * hs, (ys_.max() + 1) * hs
            mx, my = xs_.mean() * hs, ys_.mean() * hs
            vx, vy = mx - cx, my - cy
            dd = math.hypot(vx, vy) + 1e-3
            speed = 1300 + 2600 * math.exp(-dd / 450) + rng.uniform(-200, 200)
            self.shards.append(dict(i=i, box=(x0, y0, x1, y1), c=((x0 + x1) / 2, (y0 + y1) / 2),
                                    dir=(vx / dd, vy / dd), v=speed, w=rng.uniform(-340, 340),
                                    grow=0.3 + 1.0 * math.exp(-dd / 600)))

    def draw_cracks(self, arr, radius, strength=1.0):
        """Draw glowing ice cracks out to radius (arr: HxWx3 float32/uint8 -> returns float32)."""
        m = (self.dist < radius).astype(np.float32)
        out = arr.astype(np.float32)
        g = np.clip(self.glow * m * strength, 0, 1)[..., None]
        out = out * (1 - g * 0.55) + np.array(FROST, np.float32) * g * 0.55
        e = (self.edge * m * strength)[..., None]
        return out * (1 - e) + 255 * e

    def sprites(self, img):
        """Cut the outgoing frame into shard sprites (with bright cut edges)."""
        arr = np.asarray(img.convert("RGB"))
        out = []
        for s in self.shards:
            x0, y0, x1, y1 = s["box"]
            m = self.lab[y0:y1, x0:x1] == s["i"]
            rgb = arr[y0:y1, x0:x1].astype(np.float32)
            e = self.edge[y0:y1, x0:x1][..., None] * m[..., None]
            rgb = rgb * (1 - e) + np.array((235, 248, 255), np.float32) * e
            rgba_ = np.dstack([rgb.astype(np.uint8), (m * 255).astype(np.uint8)])
            out.append(Image.fromarray(rgba_, "RGBA"))
        return out

    def draw_shards(self, c, sprites, tau, dur=0.5):
        """tau: seconds since the break."""
        if tau >= dur:
            return
        g = 1500.0
        for s, sp in zip(self.shards, sprites):
            tt = tau
            dx = s["dir"][0] * s["v"] * tt
            dy = s["dir"][1] * s["v"] * tt + 0.5 * g * tt * tt
            sc = 1 + s["grow"] * tt * 2.2
            a = clamp(1 - (tau - 0.16) / 0.3)
            put(c, sp, s["c"][0] + dx, s["c"][1] + dy, sc, s["w"] * tt, a)


SHATTERS = {8: Shatter(11, W / 2, H / 2), 56: Shatter(23, W / 2, H / 2 - 30)}


# ---------------------------------------------------------------- HUD

HUD_ITEMS = [
    ("tl", "ARTIST", "DRAKE"), ("tc", "ICEMAN", "TRACK 04 / 18"), ("tr", "OVO", "2026"),
    ("bl", "NOW PLAYING", "JANICE STFU"), ("bc", "126 BPM", "16:9 CUT"), ("br", "TC", None),
]


@lru_cache(maxsize=64)
def hud_text(s, size, key, col):
    f = F(key, size)
    l, t, r, b = f.getbbox(s)
    xs, total = layout(key, size, s, 0.12)
    im = Image.new("RGBA", (int(total + 6), b + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(s):
        d.text((xs[i] + 2, 0), ch, font=f, fill=col)
    return im


def hud(c, t, k, dark=False, a=1.0):
    main = rgba(INK if dark else PAPER, int(235 * a))
    sub = rgba(INK if dark else PAPER, int(140 * a))
    fr = int(round(t * FPS))
    tc = f"00:{int(t):02d}:{fr % FPS:02d}"
    for pos, l1, l2 in HUD_ITEMS:
        if l2 is None:
            l2 = tc
        s1 = hud_text(l1, 15, "interm", sub)
        s2 = hud_text(l2, 19, "inter", main)
        y = 40 if pos[0] == "t" else H - 40 - s1.height - s2.height - 2
        for j, sp in enumerate((s1, s2)):
            if pos[1] == "l":
                x = 56
            elif pos[1] == "r":
                x = W - 56 - sp.width
            else:
                x = W / 2 - sp.width / 2
            comp(c, sp, x, y + (0 if j == 0 else s1.height + 2))
    if k % 1 < 0.5:
        ImageDraw.Draw(c).ellipse((W - 56 - 150, H - 40 - 28, W - 56 - 138, H - 40 - 16), fill=rgba(ICE))


# ---------------------------------------------------------------- hook UI


def player_card(t):
    w, h = 900, 318
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=(16, 18, 26, 236), outline=(255, 255, 255, 46), width=2)
    im.alpha_composite(ART_R, (35, 35))
    d.text((312, 92), "Janice STFU", font=F("disp", 56), fill=(255, 255, 255, 255), anchor="ls")
    d.rounded_rectangle((640, 58, 668, 86), 6, fill=(150, 156, 170, 255))
    d.text((654, 72), "E", font=F("inter", 19), fill=(16, 18, 26, 255), anchor="mm")
    d.text((312, 140), "Drake  ·  ICEMAN", font=F("interm", 32), fill=(156, 162, 178, 255), anchor="ls")
    pos = 42.4657 + t  # song position of this frame
    total = 237.39
    x0, x1, y = 312, 862, 196
    d.rounded_rectangle((x0, y - 4, x1, y + 4), 4, fill=(255, 255, 255, 60))
    xp = x0 + (x1 - x0) * pos / total
    d.rounded_rectangle((x0, y - 4, xp, y + 4), 4, fill=(255, 255, 255, 235))
    d.ellipse((xp - 9, y - 9, xp + 9, y + 9), fill=(255, 255, 255, 255))
    f = F("interm", 22)
    d.text((x0, y + 36), f"{int(pos // 60)}:{int(pos % 60):02d}", font=f, fill=(150, 156, 170, 255), anchor="ls")
    rem = total - pos
    d.text((x1, y + 36), f"-{int(rem // 60)}:{int(rem % 60):02d}", font=f, fill=(150, 156, 170, 255), anchor="rs")
    cx, cy = 587, 272
    wh = (255, 255, 255, 255)
    for sgn in (-1, 1):  # prev / next double triangles
        bx = cx + sgn * 120
        for o in (0, 22):
            ox = bx + sgn * (o - 11)
            if sgn > 0:
                d.polygon([(ox - 11, cy - 14), (ox + 11, cy), (ox - 11, cy + 14)], fill=wh)
            else:
                d.polygon([(ox + 11, cy - 14), (ox - 11, cy), (ox + 11, cy + 14)], fill=wh)
    d.rounded_rectangle((cx - 16, cy - 20, cx - 5, cy + 20), 3, fill=wh)  # pause
    d.rounded_rectangle((cx + 5, cy - 20, cx + 16, cy + 20), 3, fill=wh)
    return im


@lru_cache(maxsize=16)
def bubble(text, mine, size=36, emo=None):
    f = F("interm", size)
    tw = f.getlength(text)
    ew = int(size * 1.15) if emo else 0
    padx, pady = 30, 19
    bw, bh = int(tw + ew + (10 if emo else 0) + 2 * padx), int(size * 1.22 + 2 * pady)
    im = Image.new("RGBA", (bw + 16, bh + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = rgba(ICE) if mine else rgba(UIGREY)
    x0 = 0 if mine else 16
    d.rounded_rectangle((x0, 0, x0 + bw, bh), 34, fill=col)
    if mine:  # tail bottom-right
        d.polygon([(x0 + bw - 30, bh - 26), (x0 + bw + 14, bh + 2), (x0 + bw - 46, bh - 4)], fill=col)
    else:
        d.polygon([(x0 + 30, bh - 26), (x0 - 14, bh + 2), (x0 + 46, bh - 4)], fill=col)
    d.text((x0 + padx, bh / 2 + 2), text, font=f, fill=(255, 255, 255, 255), anchor="lm")
    if emo:
        e = emoji(emo, ew)
        im.alpha_composite(e, (int(x0 + padx + tw + 10), int(bh / 2 - e.height / 2)))
    return im


def typing_dots(k):
    im = Image.new("RGBA", (130, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((16, 0, 128, 66), 33, fill=rgba(UIGREY))
    d.ellipse((0, 52, 18, 70), fill=rgba(UIGREY))
    for j in range(3):
        ph = (k * 2.2 - j * 0.22) % 1
        a = 110 + int(145 * max(0.0, math.sin(ph * math.pi)))
        y = 33 - 5 * max(0.0, math.sin(ph * math.pi))
        d.ellipse((44 + j * 24 - 8, y - 8, 44 + j * 24 + 8, y + 8), fill=(200, 200, 210, a))
    return im


@lru_cache(maxsize=1)
def hook_caption():
    """On-screen hook text, readable from frame 0."""
    f = F("disp", 64)
    l1, l2 = "when janice texts you", "right before the drop"
    w = int(max(f.getlength(l1), f.getlength(l2) + 90)) + 40
    im = Image.new("RGBA", (w, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((20, 70), l1, font=f, fill=(255, 255, 255, 255), anchor="ls")
    d.text((20, 158), l2, font=f, fill=(255, 255, 255, 255), anchor="ls")
    e = emoji("🙄", 72)
    im.alpha_composite(e, (int(20 + f.getlength(l2) + 16), 92))
    sh = glow_of(im, INK, 16, 40)
    out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    out.alpha_composite(fade(sh, 0.85))
    out.alpha_composite(im, (40, 40))
    return out


CW, CH = 720, 960
KEYS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
TYPED = [(5.0, "s"), (5.5, "t"), (6.0, "f"), (6.5, "u")]
STFU_BUBBLE = (CW - 30, 548)  # right-bottom anchor of the sent bubble inside the chat panel


def key_pos(ch):
    for r, row in enumerate(KEYS):
        if ch in row:
            i = row.index(ch)
            x0 = (CW - (len(row) * 60 + (len(row) - 1) * 8)) / 2
            return x0 + i * 68, 700 + r * 84
    return None


def chat_panel(k):
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, CW - 1, CH - 1), 56, fill=(12, 13, 18, 228), outline=(255, 255, 255, 40), width=2)
    d.ellipse((CW / 2 - 34, 28, CW / 2 + 34, 96), fill=rgba(ICE))
    d.text((CW / 2, 63), "J", font=F("disp", 38), fill=(255, 255, 255, 255), anchor="mm")
    d.text((CW / 2, 132), "Janice", font=F("interm", 26), fill=(255, 255, 255, 255), anchor="ms")
    d.line((40, 160, CW - 40, 160), fill=(255, 255, 255, 26), width=2)

    def pop(sp, at, ax, ay, anchor_right=False):
        q = eo_back((k - at) / 0.32, 2.2)
        s = max(0.05, 0.25 + 0.75 * q)
        sp2 = scaled(sp, s)
        x = ax - sp2.width if anchor_right else ax
        comp(im, sp2, x, ay - sp2.height)

    if 2.35 <= k < 3:
        comp(im, typing_dots(k), 26, 292 - 72)
    if k >= 3:
        pop(bubble("we need to talk.", False), 3, 26, 292)
    if 3.4 <= k < 4:
        comp(im, typing_dots(k), 26, 410 - 72)
    if k >= 4:
        pop(bubble("why u so cold lately", False, 36, "🥶"), 4, 26, 410)
    if 7 <= k < 7.25:
        pop(bubble("stfu", True), 7, STFU_BUBBLE[0], STFU_BUBBLE[1], anchor_right=True)
        d.text((CW - 40, STFU_BUBBLE[1] + 30), "Delivered", font=F("interm", 18), fill=(150, 150, 160, 255),
               anchor="rs")
    # input bar
    y = 604
    typed = "".join(ch for at, ch in TYPED if k >= at) if k < 7 else ""
    d.rounded_rectangle((24, y, 616, y + 66), 33, fill=(28, 28, 34, 255), outline=(70, 70, 80, 255), width=2)
    if typed:
        d.text((52, y + 34), typed, font=F("interm", 34), fill=(255, 255, 255, 255), anchor="lm")
        tx = 52 + F("interm", 34).getlength(typed)
    else:
        d.text((52, y + 34), "Message", font=F("interm", 30), fill=(110, 110, 120, 255), anchor="lm")
        tx = 50
    if (k * 2) % 1 < 0.6 and 4.4 <= k < 7:
        d.rectangle((tx + 3, y + 16, tx + 6, y + 50), fill=rgba(ICE))
    press = 6.85 <= k < 7.05
    r = 30 if press else 27
    d.ellipse((668 - r, y + 33 - r, 668 + r, y + 33 + r), fill=rgba(ICE) if typed else (60, 60, 68, 255))
    d.polygon([(668, y + 18), (680, y + 33), (656, y + 33)], fill=(255, 255, 255, 255))
    d.rectangle((665, y + 30, 671, y + 48), fill=(255, 255, 255, 255))
    # keyboard
    hot = None
    for at, ch in TYPED:
        if 0 <= k - at < 0.24:
            hot = ch
    fk = F("interm", 30)
    for row in KEYS:
        for ch in row:
            kx, ky = key_pos(ch)
            d.rounded_rectangle((kx, ky, kx + 60, ky + 76), 10, fill=(66, 66, 74, 255))
            d.text((kx + 30, ky + 40), ch, font=fk, fill=(255, 255, 255, 255), anchor="mm")
    if hot:
        kx, ky = key_pos(hot)
        d.rounded_rectangle((kx - 14, ky - 96, kx + 74, ky + 76), 16, fill=(120, 124, 136, 255))
        d.text((kx + 30, ky - 40), hot, font=F("interm", 54), fill=(255, 255, 255, 255), anchor="mm")
    return im


CARD_POSE = dict(cx=560, cy=500, rx=6, ry=22, rz=-3, s=1.0)
CHAT_POSE = dict(cx=1370, cy=548, rx=4, ry=-16, rz=1.5, s=0.98)


def sc_hook(c, k, d, t):
    z = 1.1 - 0.08 * clamp((k - K0) / 6.5)
    comp(c, kb(ICE_HOOK, z, 30 * math.sin(k * 0.4), 0), 0, 0)
    snow(c, t, 90, 0.6)
    info = {"hud": None}
    if k < 7.62:
        # player card swings in on the very first frames (hook!)
        p = eo_back(0.35 + 0.65 * (k - K0) / 0.6, 1.4)
        pose = dict(CARD_POSE)
        pose["ry"] = lerp(78, CARD_POSE["ry"], p) + 2.5 * math.sin(k * 1.3)
        pose["cx"] = lerp(240, CARD_POSE["cx"], p)
        pose["rx"] += 2 * math.sin(k * 0.9)
        if k >= 3:  # pushed back once messages arrive
            q = eo_expo((k - 3) / 0.5)
            pose["s"] *= 1 - 0.1 * q
            pose["cy"] += 40 * q
        put3d(c, player_card(t), **pose)
        if k >= 1.55:
            q = eo_expo((k - 1.55) / 0.5)
            pose = dict(CHAT_POSE)
            pose["cx"] = lerp(W + 500, CHAT_POSE["cx"], q)
            pose["ry"] = lerp(-55, CHAT_POSE["ry"], q) + 1.5 * math.sin(k * 1.1)
            put3d(c, chat_panel(k), **pose)
    if k < 7.3:
        s = 1.1 - 0.1 * eo_expo((k - K0) / 0.3)
        put(c, hook_caption(), 560, 175, s, -2)
    if k >= 7.25:
        # the sent bubble swells to fill the screen
        bx, by = proj_point(STFU_BUBBLE[0] - 60, STFU_BUBBLE[1] - 38, CW, CH, CHAT_POSE["rx"], CHAT_POSE["ry"],
                            CHAT_POSE["rz"], CHAT_POSE["s"], CHAT_POSE["cx"], CHAT_POSE["cy"])
        p = clamp((k - 7.25) / 0.32) ** 2.2
        cx, cy = lerp(bx, W / 2, p), lerp(by, H / 2, p)
        bw, bh = lerp(124, W + 200, p), lerp(76, H + 200, p)
        rad = lerp(34, 0, p)
        ImageDraw.Draw(c).rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), rad,
                                            fill=rgba(ICE))
        size = int(lerp(36, 470, clamp((k - 7.25) / 0.32) ** 1.6) / 4) * 4
        tremble = 0.0
        if k >= 7.57:
            tremble = 6 * math.sin(t * 90)
        sp, dx, dy = tsprite("disp", max(16, size), "stfu", (255, 255, 255, 255))
        comp(c, sp, cx - sp.width / 2 + tremble, cy - sp.height / 2 + 4)
        info["zb"] = 0.3 * math.sin(math.pi * clamp((k - 7.25) / 0.34))
        if k >= 7.57:  # pre-drop silence: the screen cracks like ice
            r = 1500 * clamp((k - 7.57) / 0.4) ** 1.25
            arr = SHATTERS[8].draw_cracks(np.asarray(c.convert("RGB")), r + 40)
            c.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA"))
    return info


# ---------------------------------------------------------------- body scenes (poster world)


def sc_ice(c, lb, d, t):
    fill(c, DEEP)
    dr = ImageDraw.Draw(c)
    for j in range(5):
        dr.rectangle((70, 640 + j * 38, 300 - j * 30, 660 + j * 38), fill=rgba(ICE))
    size = 1420
    base = H / 2 + cap("anton", size) / 2 + 30
    draw_word(c, "anton", size, "ICE", W / 2, base, PAPER, track=0.03, appear=[0, 1, 2], lb=lb,
              align="center", slam=0.25, tex=ICE_TEX)
    put_bottom(c, A["stage_ht"], W / 2 + 40, H + 140 - 20 * lb / 3, 1250 * (1 + 0.035 * lb / 3))
    if lb >= 1.5:
        q = eo_expo((lb - 1.5) / 0.35)
        put(c, box_text("anton", 120, "ICEMAN", PAPER, ICE), W - 330 + (1 - q) * 500, 790, 1, -3)
    if lb >= 2.0:
        q = eo_expo((lb - 2.0) / 0.35)
        put(c, box_text("anton", 92, "ERA", INK, PAPER), W - 250 + (1 - q) * 500, 925, 1, -3)
    return {"hud": "light"}


def sc_badge(c, lb, d, t):
    fill(c, INK)
    dr = ImageDraw.Draw(c)
    dr.polygon([(860, 0), (1600, 0), (1500, H), (760, H)], fill=rgba(ICE))
    plate = cover(A["grin_plate"], 330, H, 0.15, 0.3, 1.25)
    comp(c, fade(plate, 0.55), 0, 0)
    put_bottom(c, A["grin_ht"], 1190 + 25 * lb / 2, H + 20, 1010)
    q = eo_back(lb / 0.4)
    bx, by, R = 600, 560, 270 * q
    if R > 2:
        burst(dr, bx, by, R, R * 0.85, 30, lb * 0.25, rgba(ICE))
        if lb > 0.2:
            draw_word(c, "anton", 165, "SIX", bx, by - 8, PAPER, appear=[0.25, 0.38, 0.51], lb=lb, align="center")
            draw_word(c, "anton", 165, "GOD", bx, by + cap("anton", 165) + 14, PAPER, appear=[0.75, 0.88, 1.01],
                      lb=lb, align="center")
    return {"hud": "light"}


def panel_img(w, h, bg, letter, lcol, subj, sh, lb_in, stroke=0, fx=0.5):
    p = Image.new("RGBA", (w, h), rgba(bg))
    size = 1000
    xs, total = layout("anton", size, letter)
    base = h / 2 + cap("anton", size) / 2
    sp, dx, dy = glyph("anton", size, letter, rgba(lcol), stroke)
    p.alpha_composite(sp, (int(w / 2 - total / 2 + dx), int(base + dy)))
    sc = 1 + 0.04 * clamp(lb_in / 3)
    sp2 = scaled(A[subj], sh * sc / A[subj].height)
    p.alpha_composite(sp2, (int(w * fx - sp2.width / 2), int(h + 10 - sp2.height)))
    return p


def sc_collage(c, lb, d, t):
    fill(c, INK)
    specs = [
        (45, ICE, "O", PAPER, "stage_ht", 960, 0, 0.5),
        (662, PAPER, "V", ICE, "grin_ht", 900, 0, 0.62),
        (1279, DEEP, "O", PAPER, "coat_ht", 930, 10, 0.5),
    ]
    zoom = 1 + 0.05 * eio(clamp((lb - 2.3) / 0.7))
    for i, (x, bg, L, lc, subj, sh, stroke, fx) in enumerate(specs):
        if lb < i:
            continue
        q = eo_back((lb - i) / 0.42, 1.3)
        pw, ph = 596, 1000
        p = panel_img(pw, ph, bg, L, lc, subj, sh, lb - i, stroke, fx)
        p.putalpha(round_mask(pw, ph, 22))
        # cards flip in on the Y axis, like the reference's 3D UI cards
        put3d(c, p, x + pw / 2, H / 2, rx=0, ry=lerp(-88 if i % 2 == 0 else 88, (i - 1) * 6, q), rz=(1 - i) * 1.2,
              s=1.0)
    return {"hud": "light", "zoom": zoom}


KIN = [("too", 0.0, -1, 0), ("cold", 0.75, 1, 0), ("for", 1.5, -1, 1), ("you.", 2.25, 1, 1)]


def sc_kinetic(c, lb, d, t):
    """White-page kinetic captions with motion blur + skew (reference style)."""
    fill(c, PAPER)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 270
    f = F("dispx", size)
    lines = {0: "too cold", 1: "for you."}
    bases = {0: 470, 1: 760}
    for word, at, dirn, li in KIN:
        if lb < at:
            continue
        line = lines[li]
        lw = f.getlength(line)
        x0 = W / 2 - lw / 2 + f.getlength(line[:line.index(word)])
        q = eo_expo((lb - at) / 0.38)
        x = x0 + dirn * 520 * (1 - q)
        sp, dx, dy = tsprite("dispx", size, word, rgba(ICE))
        sp = shear_sprite(smear_sprite(sp, 1 + 9 * (1 - q)), -0.35 * dirn * (1 - q))
        comp(layer, sp, x + dx, bases[li] + dy)
        if word == "cold":
            qe = eo_back((lb - at - 0.25) / 0.35)
            if lb - at > 0.25:
                put(layer, emoji("🥶", 170), x0 + f.getlength("cold") + 110, bases[li] - 110, max(0.05, qe),
                    12 * math.sin(lb * 3))
    if lb >= 2.55:
        p = eio((lb - 2.55) / 0.45)
        put3d(c, layer, W / 2, H / 2, rx=8 * p, ry=-38 * p, rz=-4 * p, s=1 + 0.5 * p)
    else:
        c.alpha_composite(layer)
    return {"hud": "dark"}


def bezier(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        u = i / n
        a, b, cc, e = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        pts.append((a * p0[0] + b * p1[0] + cc * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + cc * p2[1] + e * p3[1]))
    return pts


SWOOSH = bezier((-80, 980), (500, -150), (1250, 1250), (2000, 260), 260)


def sc_wide(c, lb, d, t):
    fill(c, INK)
    q1 = eo_expo(lb / 0.35)
    drift = -30 * lb
    sub = word_sprite("wide", 300, "SUB", ICE)
    comp(c, smear_sprite(sub, 1 + 12 * (1 - q1)), 100 + (1 - q1) * W + drift, 430 - cap("wide", 300) - 10)
    if lb >= 0.9:
        q2 = eo_expo((lb - 0.9) / 0.35)
        sp = smear_sprite(word_sprite("wide", 300, "ZERO", ICE, stroke=7), 1 + 12 * (1 - q2))
        comp(c, sp, W - 110 - sp.width - (1 - q2) * W - drift, 520)
    put_bottom(c, A["stage_ht"], W * 0.3, H + 560 - 160 * eo_expo(lb / 1.2), 1450)
    n = int(len(SWOOSH) * eio(clamp(lb / 1.4)))
    if n > 2:
        ImageDraw.Draw(c).line(SWOOSH[:n], fill=rgba(PAPER), width=7, joint="curve")
    if lb >= 0.5:
        lab = rot_sprite(hud_text("−40°C  //  TORONTO", 30, "inter", rgba(PAPER)), 90)
        comp(c, lab, W - 120, H / 2 - lab.height / 2)
    return {"hud": "light"}


def seats_bg(c, lb):
    dr = ImageDraw.Draw(c)
    off = (lb * 40) % 220
    for row in range(-1, 7):
        y = row * 180 + off * 0.8 - 60
        for col in range(-1, 10):
            x = col * 220 + (row % 2) * 110 + off
            dr.rounded_rectangle((x, y, x + 170, y + 120), 26, fill=rgba(DEEP, 85))
            dr.rectangle((x + 10, y + 128, x + 160, y + 146), fill=rgba(DEEP, 60))


def sc_seats(c, lb, d, t):
    fill(c, ICE)
    seats_bg(c, lb)
    size = 560
    xs, tot = layout("wide", size, "BOY")
    base = H / 2 + cap("wide", size) / 2 + 40
    draw_word(c, "wide", size, "BOY", W / 2, base, PAPER, appear=[0.25, 0.5, 0.75], lb=lb, align="center")
    if lb >= 0.05:
        sp = box_text("wide", 70, "THE", PAPER, INK)
        put(c, sp, W / 2 - tot / 2 + sp.width / 2, base - cap("wide", size) - 70, eo_back(lb / 0.3), -4)
    put_bottom(c, A["seat_bw"], W / 2, H + 10, 720 * (1 + 0.04 * lb / 2.5))
    return {"hud": "light"}


@lru_cache(maxsize=4)
def stfu_sprite():
    ws = word_sprite("anton", 860, "STFU", PAPER, track=0.02, pad=20)
    # ice texture fill
    tex = cover(ICE_TEX, ws.width, ws.height, 0.5, 0.5).convert("RGBA")
    tex.putalpha(ws.getchannel("A"))
    return tex


def sc_tilt(c, lb, d, t):
    fill(c, INK)
    pan = Image.new("RGBA", (2600, 760), rgba(DEEP))
    q = eo_expo(lb / 0.5)
    s = 1.35 - 0.35 * q - 0.03 * lb
    put(c, pan, W / 2, H / 2 + 20, s, 12)
    put(c, stfu_sprite(), W / 2, H / 2 + 10, s * 0.98, 12)
    return {"hud": "light"}


def sc_tiltcoat(c, lb, d, t):
    fill(c, INK)
    ImageDraw.Draw(c).polygon([(0, 0), (520, 0), (380, H), (0, H)], fill=rgba(DEEP))
    sp = scaled(A["coat_ht"], 1150 / A["coat_ht"].height)
    put(c, sp, 1250 - 30 * lb, H / 2 + 70, 1 + 0.03 * lb, -14)
    if lb >= 0.15:
        put(c, box_text("anton", 170, "JANICE", PAPER, ICE), 470, 420, eo_back((lb - 0.15) / 0.3), -5)
    if lb >= 0.65:
        put(c, box_text("anton", 170, "STFU", INK, PAPER), 560, 640, eo_back((lb - 0.65) / 0.3), -5)
    return {"hud": "light"}


def sc_swirl(c, lb, d, t):
    inv = lb >= 3
    fill(c, INK if inv else ICE)
    sw = SWIRL.crop((int(100 + 40 * lb), int(80 + 20 * lb), int(100 + 40 * lb) + W, int(80 + 20 * lb) + H))
    if inv:
        tint = Image.new("RGBA", sw.size, rgba(ICE))
        tint.putalpha(sw.getchannel("A"))
        sw = tint
    comp(c, sw, 0, 0)
    word = "ICEMAN"
    size = int(700 * (W - 110) / layout("anton", 700, word, 0.01)[1])
    base = H / 2 + cap("anton", size) / 2 - 40
    draw_word(c, "anton", size, word, W / 2, base, PAPER if inv else INK, track=0.01,
              appear=[0, 0.35, 0.7, 1.05, 1.4, 1.75], lb=lb, align="center", grey_flash=not inv)
    hh = 1080 * (1.12 if inv else 1 + 0.03 * lb / 3)
    put_bottom(c, A["glove_ht"], W / 2 + 30, H + 140, hh, rot=2.5 * math.sin(lb * 1.6))
    return {"hud": "light" if inv else "dark", "rgb": 6 if inv and (lb % 0.5) < 0.12 else 0}


RAPID = [  # (start, bg, subject, word, word colour, stroke, x)
    (0.0, ICE, "stage_ht", "ICE", PAPER, 0, 0.5),
    (1.0, PAPER, "grin_ht", "COLD", ICE, 0, 0.62),
    (2.0, INK, "coat_ht", "SIX", PAPER, 12, 0.5),
    (3.0, DEEP, "glove_ht", "GOD", ICE, 0, 0.5),
    (4.0, None, "stage_plate", "TORONTO", PAPER, 0, 0.5),
    (5.0, ICE, "seat_bw", "OVO", INK, 0, 0.5),
    (6.0, INK, "grin_ht", "I", ICE, 0, 0.74),
    (6.5, PAPER, "stage_ht", "C", INK, 0, 0.27),
    (7.0, ICE, "coat_ht", "E", PAPER, 0, 0.72),
    (7.5, INK, "glove_ht", "MAN", PAPER, 0, 0.5),
]


def sc_rapid(c, lb, d, t):
    idx = max(i for i, r in enumerate(RAPID) if lb >= r[0])
    st, bg, subj, word, wc, stroke, fx = RAPID[idx]
    nxt = RAPID[idx + 1][0] if idx + 1 < len(RAPID) else d
    ll = (lb - st) / (nxt - st)
    z = 1.07 - 0.07 * eo_expo(ll * 1.5)
    if bg is None:
        comp(c, cover(A[subj], W, H, 0.5, 0.25, 1.1 * z), 0, 0)
        put(c, box_text("anton", 210, word, PAPER, ICE), 520, H - 300, 1 + 0.15 * (1 - eo_expo(ll * 3)), -4)
        return {"hud": "light", "cut": st}
    fill(c, bg)
    size = 900
    xs, tot = layout("anton", size, word, 0.02)
    if tot > W - 160:
        size = int(size * (W - 160) / tot)
    base = H / 2 + cap("anton", size) / 2
    if stroke:
        xs, tot = layout("anton", size, word, 0.02)
        for j, L in enumerate(word):
            sp, dx, dy = glyph("anton", size, L, rgba(wc), stroke)
            sp = scaled(sp, z)
            comp(c, sp, W / 2 - tot * z / 2 + xs[j] * z + dx, base + dy * z)
    else:
        put(c, word_sprite("anton", size, word, wc, 0.02), W / 2, H / 2 + 10, z)
    hh = (1000 if subj != "seat_bw" else 760) * (1 + 0.05 * ll)
    put_bottom(c, A[subj], W * fx, H + (120 if subj in ("stage_ht", "glove_ht") else 10), hh)
    return {"hud": "dark" if bg == PAPER else "light", "cut": st}


def sc_white(c, lb, d, t):
    fill(c, PAPER)
    dr = ImageDraw.Draw(c)
    rays(dr, W * 0.86, -80, 26, 1.75 + 0.05 * lb, rgba(ICE), r=2600, width=0.42)
    size, word, base = 600, "DRAKE", 610
    draw_word(c, "anton", size, word, W / 2, base, INK, track=0.02, appear=[0.0, 0.18, 0.36, 0.54, 0.72], lb=lb,
              align="center")
    if lb >= 0.9:
        ws = word_sprite("anton", size, word, INK, 0.02, pad=0)
        ref = ws.transpose(Image.FLIP_TOP_BOTTOM).resize((ws.width, int(ws.height * 0.62)), Image.BILINEAR)
        grad = np.linspace(0.55, 0.0, ref.height)[:, None] * np.ones((1, ref.width))
        al = (np.asarray(ref.getchannel("A")).astype(np.float32) * grad * clamp((lb - 0.9) / 0.3)).astype(np.uint8)
        ref.putalpha(Image.fromarray(al, "L"))
        comp(c, ref, W / 2 - ws.width / 2, base + 16)
    put_bottom(c, A["stage_ht"], W / 2 + 10, H + 130, 1120 * (1 + 0.03 * lb / 3))
    fr = Image.new("RGBA", (W, H), rgba(INK))
    m = Image.new("L", (W, H), 255)
    ImageDraw.Draw(m).rounded_rectangle((26, 26, W - 27, H - 27), 46, fill=0)
    fr.putalpha(m)
    c.alpha_composite(fr)
    return {"hud": "dark"}


def sc_words(c, lb, d, t):
    fill(c, INK)
    dr = ImageDraw.Draw(c)
    burst(dr, W - 140, 110, 470, 400, 34, lb * 0.2, rgba(ICE))
    put_bottom(c, A["grin_ht"], W - 520, H + 30, 1040)
    rows = [("ICE", PAPER, ICE, 200, 330), ("IN MY", INK, PAPER, 150, 560), ("VEINS", PAPER, ICE, 220, 800)]
    for j, (wd, tc_, bc, size, y) in enumerate(rows):
        if lb >= j:
            q = eo_expo((lb - j) / 0.32)
            b = smear_sprite(box_text("wide", size, wd, tc_, bc), 1 + 8 * (1 - q))
            put(c, b, 120 + b.width / 2 - (1 - q) * 900, y, 1 + 0.12 * (1 - q), -5)
    z, inv, rgb = 1.0, False, 0
    if lb >= 3:
        z = 1 + 0.2 * eo_expo((lb - 3) / 0.5)
    if lb >= 4:
        inv = (lb - 4) % 0.5 < 0.18
        rgb = 10 if inv else 4
    return {"hud": "light", "zoom": z, "focus": (W - 560, 420), "invert": inv, "rgb": rgb}


@lru_cache(maxsize=8)
def arc_line(text_visible, size, amount):
    f = F("dispx", size)
    full = "COLD AS"
    l, t, r, b = f.getbbox(full, anchor="ls")
    im = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20 - l
    for wd in full.split(" "):
        if wd in text_visible:
            d.text((x, 20 - t), wd, font=f, fill=(255, 255, 255, 255), anchor="ls")
        x += f.getlength(wd + " ")
    return arc_warp(im, amount)


def sc_cubes(c, lb, d, t):
    """Ice-cube element backdrop + arc-warped type + giant ICE behind the coat."""
    comp(c, kb(ICE_BG, 1.12 - 0.1 * clamp(lb / 4), -40 * lb, 10 * lb), 0, 0)
    vis = tuple(w for w, at in (("COLD", 0.0), ("AS", 0.5)) if lb >= at)
    if lb >= 2:
        q = eo_expo((lb - 2) / 0.35)
        size = int(1000 * 700 / cap("anton", 1000))
        base = H - 30
        ws = word_sprite("anton", size, "ICE", PAPER, 0.03, pad=0)
        sh = glow_of(ws, INK, 22, 60)
        put(c, fade(sh, 0.7), W / 2, base - cap("anton", size) / 2 + 30, 1.25 - 0.25 * q)
        put(c, ws, W / 2, base - cap("anton", size) / 2, 1.25 - 0.25 * q, 0, q)
    put_bottom(c, A["coat_ht"], W * 0.66, H + 20, 960 * (1 + 0.03 * lb / 4))
    if vis:
        sp = arc_line(vis, 210, 100)
        q = eo_back(lb / 0.35)
        put(c, sp, W * 0.33, 185, 0.6 + 0.4 * q)
    return {"hud": "light"}


def contact_card(lb):
    w, h = 760, 860
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 56, fill=(18, 20, 28, 240), outline=(255, 255, 255, 44), width=2)
    d.ellipse((w / 2 - 105, 50, w / 2 + 105, 260), fill=rgba(ICE))
    d.text((w / 2, 158), "J", font=F("disp", 120), fill=(255, 255, 255, 255), anchor="mm")
    d.text((w / 2, 352), "Janice", font=F("disp", 76), fill=(255, 255, 255, 255), anchor="ms")
    d.text((w / 2, 400), "mobile", font=F("interm", 30), fill=(150, 156, 170, 255), anchor="ms")
    rows = ["Send Message", "Share Contact", "Add to Favourites", "Block this Caller"]
    y0 = 450
    d.rounded_rectangle((40, y0, w - 40, y0 + 4 * 92), 28, fill=(32, 34, 44, 255))
    for j, label in enumerate(rows):
        y = y0 + j * 92
        if j == 3 and 1.0 <= lb < 1.6:  # tap highlight
            d.rounded_rectangle((40, y, w - 40, y + 92), 28, fill=(60, 64, 80, 255))
            rr = 30 + 400 * (lb - 1.0)
            d.ellipse((160 - rr, y + 46 - rr * 0.3, 160 + rr, y + 46 + rr * 0.3), fill=(255, 255, 255, 30))
        col = rgba(ICE) if j == 3 else (255, 255, 255, 255)
        d.text((80, y + 48), label, font=F("interm", 34), fill=col, anchor="lm")
        if j < 3:
            d.line((80, y + 92, w - 40, y + 92), fill=(255, 255, 255, 22), width=2)
    return im


@lru_cache(maxsize=2)
def blocked_pill():
    w, h = 640, 170
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 85, fill=rgba(ICE))
    # padlock
    lx, ly = 110, 92
    d.rounded_rectangle((lx - 34, ly - 14, lx + 34, ly + 42), 10, fill=(255, 255, 255, 255))
    d.arc((lx - 24, ly - 56, lx + 24, ly - 8), 180, 360, fill=(255, 255, 255, 255), width=10)
    d.line((lx - 24, ly - 32, lx - 24, ly - 12), fill=(255, 255, 255, 255), width=10)
    d.line((lx + 24, ly - 32, lx + 24, ly - 12), fill=(255, 255, 255, 255), width=10)
    d.ellipse((lx - 7, ly + 6, lx + 7, ly + 20), fill=rgba(ICE))
    d.text((190, h / 2 + 4), "Blocked.", font=F("disp", 96), fill=(255, 255, 255, 255), anchor="lm")
    return im


@lru_cache(maxsize=2)
def blocked_glow():
    return glow_of(blocked_pill(), ICE, 40, 160)


def sc_block(c, lb, d, t):
    c.paste(END_BG, (0, 0))
    if lb >= 2:
        sp = word_sprite("anton", 520, "BLOCKED", ICE, 0.02, stroke=0, pad=0)
        put(c, sp, W / 2, H / 2, 1.1 - 0.05 * lb / 4, -4, 0.35 * clamp((lb - 2) / 0.2))
    p = eo_back(lb / 0.45, 1.3)
    ry = lerp(70, -12, p) + 2 * math.sin(lb * 2)
    put3d(c, contact_card(lb), 760 - 120 * (lb >= 2) * eo_expo((lb - 2) / 0.4), H / 2 + 20, rx=5, ry=ry, rz=-2,
          s=0.95 * (1 - 0.12 * (lb >= 2) * eo_expo((lb - 2) / 0.4)))
    if lb >= 2:
        q = eo_back((lb - 2) / 0.4, 2.4)
        s = max(0.05, 0.3 + 0.7 * q)
        put(c, blocked_glow(), 960, H / 2 + 230, s * 1.05, -4, 0.9)
        put3d(c, blocked_pill(), 960, H / 2 + 230, rx=-8, ry=14, rz=-4, s=s)
    if lb >= 2.5:
        q = eo_expo((lb - 2.5) / 0.4)
        put_bottom(c, A["grin_ht"], W - 250 + (1 - q) * 700, H + 30, 920)
    return {"hud": "light"}


@lru_cache(maxsize=1)
def notif_banner():
    w, h = 860, 150
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 38, fill=(30, 32, 42, 240), outline=(255, 255, 255, 40), width=2)
    d.ellipse((28, 37, 104, 113), fill=rgba(ICE))
    d.text((66, 76), "J", font=F("disp", 44), fill=(255, 255, 255, 255), anchor="mm")
    d.text((130, 62), "Janice", font=F("inter", 32), fill=(255, 255, 255, 255), anchor="ls")
    d.text((w - 34, 62), "now", font=F("interm", 26), fill=(150, 156, 170, 255), anchor="rs")
    body = "u really blocked me??"
    f = F("interm", 32)
    d.text((130, 112), body, font=f, fill=(220, 224, 232, 255), anchor="ls")
    e = emoji("💀", 38)
    im.alpha_composite(e, (int(130 + f.getlength(body) + 10), 80))
    return im


def sc_end(c, lb, d, t):
    c.paste(END_BG, (0, 0))
    snow(c, t, 120, 1.0 + 0.6 * (lb >= 3))
    q = eo_expo(lb / 0.35)
    s = 1.25 - 0.25 * q + 0.07 * lb / 8 + 0.05 * math.exp(-max(0.0, lb - 3) / 0.25) * (lb >= 3)
    g = 0.55 + 0.45 * math.exp(-max(0.0, lb - 3) / 0.6) * (lb >= 3)
    put(c, LOGO_GLOW, W / 2, H / 2 - 40, s, 0, g)
    put(c, LOGO, W / 2, H / 2 - 40, s, 0, clamp(lb / 0.1))
    dr = ImageDraw.Draw(c)
    if lb >= 0.8:
        a = clamp((lb - 0.8) / 0.4)
        put(c, hud_text("DRAKE   —   JANICE STFU", 34, "inter", rgba(PAPER)), W / 2, H / 2 + 150 + 20 * (1 - a), 1,
            0, a)
    if lb >= 1.3:
        a = clamp((lb - 1.3) / 0.4)
        put(c, hud_text("ICEMAN  ·  TRACK 04  ·  2026", 20, "interm", rgba(FROST)), W / 2, H / 2 + 205, 1, 0, a)
        dr.rectangle((W / 2 - 60 * a, H / 2 + 240, W / 2 + 60 * a, H / 2 + 243), fill=rgba(ICE))
    # closing gag: Janice's notification drops in, then gets swiped away
    if 4 <= lb < 6.6:
        qin = eo_back((lb - 4) / 0.4, 1.6)
        qout = clamp((lb - 6.1) / 0.35) ** 2
        y = lerp(-120, 190, qin) - 420 * qout
        put3d(c, notif_banner(), W / 2, y, rx=-6, ry=0, rz=0, s=1.0)
    # light rays (added in post so they glow over everything)
    pulse = 0.55 + 0.45 * math.exp(-lb / 0.5) + 0.5 * math.exp(-max(0.0, lb - 3) / 0.45) * (lb >= 3)
    return {"hud": "light", "rays": pulse * clamp(lb / 0.15), "rays_s": s}


SCENES = [
    (0, 8, sc_hook), (8, 11, sc_ice), (11, 13, sc_badge), (13, 16, sc_collage), (16, 19, sc_kinetic),
    (19, 21.5, sc_wide), (21.5, 24, sc_seats), (24, 25.5, sc_tilt), (25.5, 27, sc_tiltcoat), (27, 32, sc_swirl),
    (32, 40, sc_rapid), (40, 43, sc_white), (43, 48, sc_words), (48, 52, sc_cubes), (52, 56, sc_block),
    (56, 99, sc_end),
]
TRANS = {11: "zoom", 13: "slice", 16: "zoom", 19: "zoom", 21.5: "blocks", 24: "flash", 25.5: "whip", 27: "zoom",
         32: "slice", 35: "zoom", 37: "blocks", 40: "invert", 43: "whip", 48: "zoom", 52: "blocks", 55.75: "zoomout"}
SHARD_FX = [(8, 0.75, 0), (24, 0.5, 40), (40, 0.45, -30), (51, 0.55, 15), (56, 0.75, 180), (59, 0.4, 90)]

# ---------------------------------------------------------------- post FX


def affine(arr, z, dx, dy, rot, focus):
    if abs(z - 1) < 1e-4 and abs(dx) < 0.5 and abs(dy) < 0.5 and abs(rot) < 1e-4:
        return arr
    fx, fy = focus
    th = math.radians(rot)
    cs, sn = math.cos(th), math.sin(th)
    a, b, d, e = cs / z, sn / z, -sn / z, cs / z
    cx, cy = fx + dx, fy + dy
    im = Image.fromarray(arr).transform((W, H), Image.AFFINE, (a, b, fx - (a * cx + b * cy), d, e, fy - (d * cx + e * cy)),
                                        Image.BILINEAR)
    return np.asarray(im)


def smear(arr, strength, shift):
    k = max(1, int(strength))
    im = Image.fromarray(arr).resize((max(16, W // k), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    out = np.asarray(im)
    return np.roll(out, int(shift), axis=1) if shift else out


def zoom_blur(arr, amount, center=(W / 2, H / 2), n=9):
    """Radial (tunnel) blur like the reference transitions."""
    if amount < 0.004:
        return arr
    small = Image.fromarray(arr).resize((W // 2, H // 2), Image.BILINEAR)
    cx, cy = center[0] / 2, center[1] / 2
    acc = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(n):
        a = 1 / (1 + amount * i / (n - 1))
        acc += np.asarray(small.transform(small.size, Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy),
                                          Image.BILINEAR), np.float32)
    blurred = np.asarray(Image.fromarray((acc / n).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32)
    mix = clamp(amount / 0.06)
    return (arr.astype(np.float32) * (1 - mix) + blurred * mix).astype(np.uint8)


def slice_glitch(arr, rng, strength):
    out = arr.copy()
    y = 0
    while y < H:
        h = int(rng.integers(10, 110))
        r = rng.random()
        if r < 0.5:
            out[y:y + h] = np.roll(arr[y:y + h], int(rng.normal(0, strength)), axis=1)
        elif r < 0.68:
            x0 = int(rng.integers(0, W - 1))
            out[y:y + h, x0:] = arr[y:y + h, x0:x0 + 1]
        y += h
    return out


def block_glitch(arr, rng, p):
    """Datamosh-style macroblock glitch."""
    out = arr.copy()
    for _ in range(int(220 * p)):
        bw, bh = int(rng.choice([32, 64, 128])), int(rng.choice([16, 32, 64]))
        x, y = int(rng.integers(0, W - bw)), int(rng.integers(0, H - bh))
        sx = int(np.clip(x + rng.normal(0, 160), 0, W - bw))
        sy = int(np.clip(y + rng.normal(0, 40), 0, H - bh))
        blk = arr[sy:sy + bh, sx:sx + bw]
        r = rng.random()
        if r < 0.22:
            blk = (blk * 0.35 + np.array(ICE) * 0.65).astype(np.uint8)
        elif r < 0.32:
            blk = blk[..., ::-1]
        elif r < 0.4:
            blk = np.repeat(blk[:, :1], bw, axis=1)
        out[y:y + bh, x:x + bw] = blk
    return out


def negative(arr):
    y = (arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114).astype(np.uint8)
    return np.repeat((255 - y)[..., None], 3, axis=2)


def rgb_split(arr, d):
    d = int(d)
    if d == 0:
        return arr
    out = arr.copy()
    out[..., 0] = np.roll(arr[..., 0], d, axis=1)
    out[..., 2] = np.roll(arr[..., 2], -d, axis=1)
    return out


def screen_shatter(arr, tau, strength, rot):
    """Ice-shatter element exploding from the centre (screen blend)."""
    a = strength * clamp(1 - tau / 0.38)
    if a <= 0.01:
        return arr
    s = (0.9 + 3.0 * eo_expo(tau / 0.35)) * W / SHAT.width * 0.8
    sp = SHAT.resize((int(SHAT.width * s), int(SHAT.height * s)), Image.BILINEAR)
    if rot:
        sp = sp.rotate(rot, Image.BILINEAR, expand=True)
    x0, y0 = int(W / 2 - sp.width / 2), int(H / 2 - sp.height / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(W, x0 + sp.width), min(H, y0 + sp.height)
    o = np.asarray(sp, np.float32)[sy0:sy0 + (Y1 - Y0), sx0:sx0 + (X1 - X0)] * a
    out = arr.copy()
    reg = out[Y0:Y1, X0:X1].astype(np.float32)
    out[Y0:Y1, X0:X1] = (255 - (255 - reg) * (255 - o) / 255).astype(np.uint8)
    return out


def scene_at(k):
    for s, e, fn in SCENES:
        if s <= k < e:
            return s, e, fn
    return SCENES[-1]


@lru_cache(maxsize=2)
def outgoing(kf):
    """Content of the frame right before a shatter (no post FX), cut into shards."""
    s, e, fn = scene_at(kf)
    c = Image.new("RGBA", (W, H), rgba(INK))
    fn(c, kf - s, e - s, tb(kf))
    return c


@lru_cache(maxsize=2)
def shard_sprites(kb_):
    return SHATTERS[kb_].sprites(outgoing(kb_ - 0.012))


def render(fi):
    t = fi / FPS + LEAD
    k = t / BEAT + K0
    rng = np.random.default_rng(fi * 7919 + 13)
    s, e, fn = scene_at(k)
    c = Image.new("RGBA", (W, H), rgba(INK))
    info = fn(c, k - s, e - s, t) or {}
    # flying shards over the new scene
    for kb_, sh in SHATTERS.items():
        tau = t - tb(kb_)
        if 0 <= tau < 0.5:
            sh.draw_shards(c, shard_sprites(kb_), tau)
    arr = np.asarray(c.convert("RGB"))

    # ---- camera: hit punches, beat pulse, shake
    z = info.get("zoom", 1.0)
    dx = dy = rot = 0.0
    flash = 0.0
    rgb = info.get("rgb", 0)
    for hk in HITS:
        dt = t - tb(hk)
        if 0 <= dt < 0.6:
            big = hk in BARS
            z *= 1 + (0.075 if big else 0.05) * math.exp(-dt / 0.12)
            amp = (30 if big else 18) * math.exp(-dt / 0.1)
            dx += rng.normal(0, amp)
            dy += rng.normal(0, amp * 0.7)
            rot += rng.normal(0, amp * 0.02)
            flash = max(flash, (0.55 if hk in SHATTERS else 0.9 if big else 0.55) * math.exp(-dt / 0.045))
            rgb = max(rgb, 16 * math.exp(-dt / 0.07))
    for hk in HOOK_TAPS:
        dt = t - tb(hk)
        if 0 <= dt < 0.3:
            z *= 1 + 0.018 * math.exp(-dt / 0.08)
            dx += rng.normal(0, 4 * math.exp(-dt / 0.06))
    if k >= 8:
        z *= 1 + 0.012 * math.exp(-((k % 1) * BEAT) / 0.08)
    if s == 32 and "cut" in info:
        dt = t - tb(32 + info["cut"])
        if 0 <= dt < 0.2 and info["cut"] not in (0.0, 3.0):
            flash = max(flash, 0.3 * math.exp(-dt / 0.04))
            dx += rng.normal(0, 12 * math.exp(-dt / 0.08))
    zoom_extra = 1 + (abs(dx) + abs(dy)) / W * 2.2
    arr = affine(arr, z * zoom_extra, dx, dy, rot, info.get("focus", (W / 2, H / 2)))

    # ---- transitions
    zb = info.get("zb", 0.0)
    if k < K0 + 0.5:  # opening tunnel reveal
        zb = max(zb, 0.07 * (1 - eo_expo((k - K0) / 0.35)))
    for tk, kind in TRANS.items():
        dt = t - tb(tk)
        if kind == "whip" and -0.14 <= dt < 0.12:
            if dt < 0:
                p = 1 + dt / 0.14
                arr = smear(arr, 4 + 70 * p ** 2, -260 * p ** 2)
            else:
                p = 1 - dt / 0.12
                arr = smear(arr, 4 + 70 * p ** 2, 260 * p ** 2)
        elif kind == "zoom" and -0.13 <= dt < 0.13:
            zb = max(zb, 0.32 * (1 - abs(dt) / 0.13) ** 1.5)
        elif kind == "zoomout" and 0 <= dt < tb(56) - tb(tk):
            zb = max(zb, 0.35 * eio(dt / (tb(56) - tb(tk))))
        elif kind == "slice" and -0.1 <= dt < 0.08:
            p = 1 - abs(dt) / 0.1
            arr = slice_glitch(arr, rng, 160 * p)
            rgb = max(rgb, 10 * p)
        elif kind == "blocks" and -0.09 <= dt < 0.09:
            arr = block_glitch(arr, rng, 1 - abs(dt) / 0.09)
        elif kind == "invert" and 0 <= dt < 0.07:
            arr = negative(arr)
    arr = zoom_blur(arr, zb)
    if info.get("invert"):
        arr = negative(arr)
    for hk, st, rr in SHARD_FX:
        tau = t - tb(hk)
        if 0 <= tau < 0.4:
            arr = screen_shatter(arr, tau, st, rr)
    if "rays" in info:
        rs = info.get("rays_s", 1.0)
        ray = RAYS if abs(rs - 1) < 0.01 else np.asarray(
            Image.fromarray((RAYS * 255).astype(np.uint8)).transform(
                (W, H), Image.AFFINE, (1 / rs, 0, W / 2 - W / 2 / rs, 0, 1 / rs, (H / 2 - 40) - (H / 2 - 40) / rs),
                Image.BILINEAR)).astype(np.float32) / 255
        add = ray[..., None] * info["rays"] * np.array((150, 200, 255), np.float32)
        arr = np.clip(arr.astype(np.float32) + add, 0, 255).astype(np.uint8)
    if t > DUR - 0.2:
        p = (t - (DUR - 0.2)) / 0.2
        arr = slice_glitch(arr, rng, 300 * p)
        arr = (arr.astype(np.float32) * (1 - p)).astype(np.uint8)
    arr = rgb_split(arr, rgb)
    if flash > 0.01:
        arr = (arr.astype(np.float32) + (255 - arr.astype(np.float32)) * flash).astype(np.uint8)

    # ---- HUD (stable, not shaken)
    if info.get("hud"):
        hc = Image.fromarray(arr).convert("RGBA")
        hud(hc, t, k, dark=info["hud"] == "dark" and not info.get("invert"), a=clamp((k - 8) / 0.8))
        arr = np.asarray(hc.convert("RGB"))

    g = GRAIN[fi % len(GRAIN)]
    out = arr.astype(np.float32) * VIG + g[..., None] * 6.5
    return np.clip(out, 0, 255).astype(np.uint8).tobytes()


def main():
    out = sys.argv[1]
    frames = sys.argv[2] if len(sys.argv) > 2 else None
    if frames:  # preview stills: comma separated frame indices
        os.makedirs(out, exist_ok=True)
        for fi in [int(x) for x in frames.split(",")]:
            Image.frombytes("RGB", (W, H), render(fi)).save(f"{out}/f{fi:04d}.jpg", quality=90)
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(int(os.environ.get("REEL_PROCS", "4"))) as pool:
        for i, buf in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
