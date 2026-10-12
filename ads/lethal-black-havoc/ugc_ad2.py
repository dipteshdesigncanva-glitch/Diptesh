"""LETHAL BLACK HAVOC — 25s 9:16 ad (v2): on-brand, 60 fps, smooth motion system.

Brand system (from lethalblack.com): crimson #BC002E, charcoal gradients, Montserrat (heavy + light),
red letter-spaced eyebrows, black cards with crimson borders, panther emblem.
Layout grid: eyebrow y=290, headline from y=410, product zone ~600-1320, captions y=1450, all centred.
Motion: eased line-mask reveals, staggered entrances, slide-stack / crimson sweep / zoom transitions,
no shakes or flashes. Frames are pure functions of time -> parallel render -> ffmpeg.
"""
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.environ.get("AD_ROOT", os.path.dirname(os.path.abspath(__file__)))
AS, CL, VO_DIR, FONTS = f"{ROOT}/assets", f"{ROOT}/clips", f"{ROOT}/vo", f"{ROOT}/fonts"

W, H, FPS, DUR = 1080, 1920, 60, 25.0
NF = int(DUR * FPS)
BPM = 124.8
BEAT = 60 / BPM


def tb(b):
    return b * BEAT


# ---------------------------------------------------------------- brand tokens
CRIMSON = (188, 0, 46)  # #BC002E
CRIMSON_LT = (234, 40, 82)  # legible crimson for small text on charcoal
WHITE = (255, 255, 255)
GREY = (164, 167, 174)
CARD = (12, 12, 14)
GOLD = (245, 166, 35)
CX = W // 2
EY = 290  # eyebrow centre
HB = 412  # first headline baseline
CAP_Y = 1450  # caption centre

VO_AT = {"hook": 0.10, "meet": 2.62, "venom": 4.45, "layers": 6.38, "gasket": 8.28, "swap": 9.22, "pbt": 10.22,
         "specs": 12.15, "gaming": 17.92, "price": 19.85, "cta": 22.72}
HOOK_KEYS = [0.0, 0.5, 1.0, 1.25, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5, 3.75, 4.0, 4.25, 4.5]
# absolute times of UI events, snapped to the 16th-note grid; ugc_audio2.py puts a tick/chime on each
S16 = BEAT / 4
EV = {"venom": [tb(10) + i * S16 for i in range(4)], "chips": [tb(14.5) + i * S16 for i in range(3)],
      "gasket": [tb(17.75) + i * S16 / 2 for i in range(9)], "swap": 9.18,
      "keycap": [tb(22), tb(22.5)], "cards": [tb(26) + i * S16 for i in range(4)], "rgb": 16.35,
      "stars": 20.25, "perks": [tb(43.5) + i * S16 for i in range(4)], "tap": 23.18, "end": 24.05}

# ---------------------------------------------------------------- easing / helpers


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def prog(t, t0, d):
    return clamp((t - t0) / d)


def e_out3(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def e_out5(p):
    p = clamp(p)
    return 1 - (1 - p) ** 5


def e_in3(p):
    p = clamp(p)
    return p ** 3


def e_io3(p):
    p = clamp(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def e_back(p, s=1.25):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def rgba(c, a=255):
    return (c[0], c[1], c[2], int(a))


MONT = f"{FONTS}/Montserrat-VariableFont_wght.ttf"
INTER = "/usr/share/fonts/opentype/inter"


@lru_cache(maxsize=256)
def MF(size, wght):
    f = ImageFont.truetype(MONT, size)
    f.set_variation_by_axes([wght])
    return f


@lru_cache(maxsize=64)
def IF(size, bold=False):
    return ImageFont.truetype(f"{INTER}/Inter-{'Bold' if bold else 'SemiBold'}.otf", size)


class Txt:
    """Text sprite cropped to ink horizontally; keeps a fixed line box vertically (baseline known)."""

    def __init__(self, im, base):
        self.im, self.base = im, base
        self.w, self.h = im.size


@lru_cache(maxsize=2048)
def text(s, size, wght=800, col=WHITE, track=0.0, inter=False, bold=False):
    f = IF(size, bold) if inter else MF(size, wght)
    asc, desc = f.getmetrics()
    xs, x = [], 0.0
    for ch in s:
        xs.append(x)
        x += f.getlength(ch) + track * size
    pad = int(size * 0.2) + 4
    im = Image.new("RGBA", (int(x) + 2 * pad + 4, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if track:
        for i, ch in enumerate(s):
            d.text((pad + xs[i], pad), ch, font=f, fill=rgba(col))
    else:
        d.text((pad, pad), s, font=f, fill=rgba(col))
    bb = im.getbbox() or (0, 0, 1, 1)
    im = im.crop((bb[0], 0, bb[2], im.height))
    return Txt(im, pad + asc)


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
    if a >= 0.999:
        return sp
    sp = sp.copy()
    sp.putalpha(sp.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return sp


def scaled(im, s):
    w, h = max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))
    return im if (w, h) == im.size else im.resize((w, h), Image.BILINEAR)


def put(c, sp, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.003:
        return
    sp = scaled(sp, s)
    if rot:
        sp = sp.rotate(rot, Image.BICUBIC, expand=True)
    comp(c, fade(sp, a), cx - sp.width / 2, cy - sp.height / 2)


def layer_draw(c, fn):
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    c.alpha_composite(lay)


def round_mask(w, h, r, feather=0):
    m = Image.new("L", (w, h), 0)
    inset = feather
    ImageDraw.Draw(m).rounded_rectangle((inset, inset, w - 1 - inset, h - 1 - inset), r, fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather / 2)) if feather else m


def _rot(rx, ry, rz):
    ax, ay, az = map(math.radians, (rx, ry, rz))
    ca, sa, cb, sb, cc, sc = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    return (np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]]) @ np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
            @ np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]))


def proj(pts, R, s, cx, cy, f=1900.0):
    P = (np.asarray(pts, float) * s) @ R.T
    z = P[:, 2] + f
    return np.stack([cx + f * P[:, 0] / z, cy + f * P[:, 1] / z], 1)


def put3d(c, sp, cx, cy, rx=0.0, ry=0.0, rz=0.0, s=1.0, a=1.0):
    """Perspective-projected sprite; sub-pixel accurate (smooth at 60 fps)."""
    if a <= 0.003:
        return
    w, h = sp.size
    quad = proj([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], _rot(rx, ry, rz), s,
                cx, cy)
    x0, y0 = max(0, int(math.floor(quad[:, 0].min()))), max(0, int(math.floor(quad[:, 1].min())))
    x1, y1 = min(c.width, int(math.ceil(quad[:, 0].max()))), min(c.height, int(math.ceil(quad[:, 1].max())))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    M, Bv = [], []
    for (x, y), (X, Y) in zip(quad - [x0, y0], [(0, 0), (w, 0), (w, h), (0, h)]):
        M += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
        Bv += [X, Y]
    co = np.linalg.solve(np.array(M), np.array(Bv))
    out = sp.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    c.alpha_composite(fade(out, a), (x0, y0))


def proj_point(px, py, w, h, rx, ry, rz, s, cx, cy):
    return proj([[px - w / 2, py - h / 2, 0]], _rot(rx, ry, rz), s, cx, cy)[0]


def light_sweep(sp, p, width=0.16, strength=0.75):
    if p <= 0 or p >= 1:
        return sp
    w, h = sp.size
    xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.4
    pos = lerp(-0.25, 1.25, p) * (w + h * 0.4)
    band = np.clip(1 - np.abs(xx - pos) / (width * w), 0, 1) ** 2 * strength
    a = np.asarray(sp).astype(np.float32)
    a[..., :3] += (255 - a[..., :3]) * band[..., None] * (a[..., 3:4] / 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def radial(size, col, power=2.0, alpha=1.0):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    o = np.zeros((size, size, 4), np.uint8)
    o[..., :3] = col
    o[..., 3] = (np.clip(1 - r, 0, 1) ** power * 255 * alpha).astype(np.uint8)
    return Image.fromarray(o, "RGBA")


# ---------------------------------------------------------------- assets


def load(n):
    return Image.open(f"{AS}/{n}.png").convert("RGBA")


A = {n: load(n) for n in ["logo", "havoc", "kb_tilt", "kb_gasket", "keycap", "kb_swap", "kb_hero", "sw_top",
                          "sw_stem", "sw_spring", "sw_base", "display"]}
RGB_MATTE = Image.open(f"{AS}/rgb_matte.png").convert("L")
_lg = A["logo"]
PANTHER = _lg.crop((575, 0, _lg.width, _lg.height))
PANTHER = PANTHER.crop(PANTHER.getbbox())

GLOW = radial(1500, CRIMSON, 2.2)
GLOW_S = radial(900, (225, 20, 60), 2.0)
SPOT = radial(1300, (255, 255, 255), 2.6)
KEYGLOW = radial(230, (255, 255, 255), 2.2)
SHADOW = Image.new("RGBA", (1000, 220), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).ellipse((120, 70, 880, 150), fill=(0, 0, 0, 200))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(28))
WMARK = fade(scaled(PANTHER, 1150 / PANTHER.width), 0.045)

_g = np.linspace(0, 1, H)[:, None, None]
_bg = np.array((13, 14, 16)) * (1 - _g) + np.array((34, 37, 41)) * _g
BG = Image.fromarray(np.repeat(_bg, W, axis=1).astype(np.uint8), "RGB").convert("RGBA")
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.78)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIG = (1 - 0.3 * np.clip(_r - 0.55, 0, 1) ** 1.3)[..., None].astype(np.float32)
del _yy, _xx, _r, _g, _bg
_rng = np.random.default_rng(5)
GRAIN = [np.asarray(Image.fromarray(_rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))
         for _ in range(6)]


@lru_cache(maxsize=None)
def clip_frames(name):
    import glob
    return [Image.open(p).convert("RGB") for p in sorted(glob.glob(f"{CL}/{name}/[0-9]*.jpg"))]


def clip_at(name, f):
    """Sub-frame interpolated clip frame (30 fps source -> smooth 60 fps)."""
    fr = clip_frames(name)
    f = clamp(f, 0, len(fr) - 1)
    i = int(f)
    u = f - i
    if u < 0.02 or i + 1 >= len(fr):
        return fr[i]
    return Image.blend(fr[i], fr[i + 1], u)


@lru_cache(maxsize=1)
def display_card():
    sp = A["display"].convert("RGB")
    w = 980
    im = sp.resize((w, int(sp.height * w / sp.width)), Image.LANCZOS).convert("RGBA")
    im.putalpha(round_mask(im.width, im.height, 46, 26))
    return im


@lru_cache(maxsize=64)
def layers_frame(i):
    fr = clip_frames("layers")[i]
    a = np.asarray(fr).astype(np.float32)
    a = (255 * (1 - (1 - a / 255) ** 2.2)).astype(np.uint8)  # lift the dark exploded layers, keep highlights
    w = 900
    im = Image.fromarray(a).resize((w, int(fr.height * w / fr.width)), Image.BILINEAR).convert("RGBA")
    yy, xx = np.mgrid[0:im.height, 0:im.width].astype(np.float32)
    r = np.sqrt(((xx - im.width / 2) / (im.width * 0.5)) ** 2 + ((yy - im.height / 2) / (im.height * 0.5)) ** 2)
    im.putalpha(Image.fromarray((np.clip((1 - r) / 0.35, 0, 1) * 255).astype(np.uint8), "L"))
    return im


@lru_cache(maxsize=1)
def game_mask():
    fr = clip_frames("game")[0]
    w = 960
    return round_mask(w, int(fr.height * w / fr.width), 26)


def gasket_points():
    a = np.asarray(A["kb_gasket"]).astype(np.int16)
    red = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 2] < 120) & (a[..., 3] > 100)
    ys, xs = np.nonzero(red)
    pts, used = [], np.zeros(len(xs), bool)
    for i in range(len(xs)):
        if used[i]:
            continue
        m = (np.abs(xs - xs[i]) < 60) & (np.abs(ys - ys[i]) < 60)
        used |= m
        if m.sum() > 40:
            pts.append((float(xs[m].mean()), float(ys[m].mean())))
    return pts


GASKETS = gasket_points()

# ---------------------------------------------------------------- reusable design blocks


def reveal(L, tx, x, y, p, a=1.0):
    """Line-mask reveal: the line rises into its own box (y = box top)."""
    if p <= 0.001 or a <= 0.003:
        return
    w, h = tx.im.size
    off = int(round((1 - p) * h * 0.95))
    if off >= h:
        return
    comp(L, fade(tx.im.crop((0, 0, w, h - off)), a * clamp(p * 1.3)), x, y + off)


def conceal(L, tx, x, y, q, a=1.0):
    """Exit: the line slides up out of its box."""
    if q >= 0.999:
        return
    w, h = tx.im.size
    off = int(round(q * h * 0.95))
    comp(L, fade(tx.im.crop((0, off, w, h)), a * (1 - q)), x, y)


def line_anim(L, tx, cx, base, t_in, lt, t_out=None, dur=0.62, out_dur=0.34):
    x, y = cx - tx.w / 2, base - tx.base
    if t_out is not None and lt >= t_out:
        conceal(L, tx, x, y, e_in3(prog(lt, t_out, out_dur)))
    else:
        reveal(L, tx, x, y, e_out5(prog(lt, t_in, dur)))


def eyebrow(L, s, lt, t_in=0.0, t_out=None, y=EY, col=CRIMSON_LT, out_dur=0.3):
    tx = text(s, 23, 700, col, 0.34)
    line_anim(L, tx, CX, y + 9, t_in, lt, t_out, 0.55, out_dur)
    u = e_out5(prog(lt, t_in + 0.1, 0.6))
    if t_out is not None and lt >= t_out:
        u *= 1 - e_in3(prog(lt, t_out, out_dur))
    if u > 0.01:
        d_len = 34 * u
        gx = tx.w / 2 + 18

        def _d(d):
            for sgn in (-1, 1):
                x0 = CX + sgn * gx
                d.line((x0, y, x0 + sgn * d_len, y), fill=rgba(col, 255 * u), width=3)
        layer_draw(L, _d)


def fit_size(lines, size, wght, maxw=900, track=0.0):
    while size > 40:
        if max(text(l, size, wght, WHITE, track).w for l in lines) <= maxw:
            return size
        size -= 2
    return size


def heading(L, lt, eb, lines, t_out=None, light=False, size=None, y_base=HB, out_dur=0.34):
    eyebrow(L, eb, lt, 0.0, t_out, out_dur=min(out_dur, 0.3))
    wght = 300 if light else 900
    size = fit_size(lines, size or (66 if light else 96), wght)
    lh = int(size * (1.14 if light else 1.04))
    for i, l in enumerate(lines):
        tx = text(l, size, wght, WHITE, 0.01 if light else 0.0)
        line_anim(L, tx, CX, y_base + i * lh, 0.08 + i * 0.07, lt, None if t_out is None else t_out + i * 0.04,
                  out_dur=out_dur)
    return y_base + (len(lines) - 1) * lh


def product(L, sp, cx, cy, s=1.0, rx=0.0, ry=0.0, rz=0.0, a=1.0, glow=0.55, shadow=True):
    if a <= 0.003:
        return
    hh = sp.height * s
    if glow:
        put(L, GLOW_S, cx, cy + hh * 0.36, s * 1.05, glow * a)
    if shadow:
        put(L, SHADOW, cx, cy + hh * 0.44, s * sp.width / 900, 0.8 * a)
    put3d(L, sp, cx, cy, rx, ry, rz, s, a)


def card_bg(w, h, r=22, border=CRIMSON, fill=CARD, alpha=236):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((1, 1, w - 2, h - 2), r, fill=rgba(fill, alpha), outline=rgba(border),
                                         width=2)
    return im


@lru_cache(maxsize=32)
def chip(s, size=22):
    tx = text(s, size, 700, WHITE, 0.16)
    w, h = tx.w + 46, int(size * 2.5)
    im = card_bg(w, h, h // 2)
    im.alpha_composite(tx.im, ((w - tx.w) // 2, (h - tx.h) // 2 + 1))
    return im


def check_badge(s, w=420, h=64):
    im = card_bg(w, h, h // 2, border=(70, 72, 78))
    d = ImageDraw.Draw(im)
    d.ellipse((14, 12, 54, 52), fill=rgba(CRIMSON))
    d.line((24, 33, 31, 40), fill=rgba(WHITE), width=4)
    d.line((31, 40, 44, 26), fill=rgba(WHITE), width=4)
    tx = text(s, 21, 700, WHITE, 0.08)
    sc = min(1.0, (w - 90) / tx.w)
    ti = scaled(tx.im, sc)
    im.alpha_composite(ti, (68, (h - ti.height) // 2 + 1))
    return im


def star_pts(x, y, size, s=1.0):
    return [(x + s * (size / 2 if j % 2 == 0 else size * 0.22) * math.cos(-math.pi / 2 + j * math.pi / 5),
             y + s * (size / 2 if j % 2 == 0 else size * 0.22) * math.sin(-math.pi / 2 + j * math.pi / 5))
            for j in range(10)]


STAR, STAR_GAP = 30, 8
STARS_W = 5 * STAR + 4 * STAR_GAP


def stars(L, x_left, cy, lt, t0, rating=4.68, step=0.06):
    """Five stars popping in one by one (step apart); gold fill is clipped, so 4.68 shows a partial 5th star."""
    pad = STAR
    w, h = STARS_W + 2 * pad, STAR + 2 * pad
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i in range(5):
        u = prog(lt, t0 + i * step, 0.4)
        if u <= 0:
            continue
        s = e_back(u, 2.4)
        x = pad + i * (STAR + STAR_GAP) + STAR / 2
        st = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(st).polygon(star_pts(x, h / 2, STAR, s), fill=(70, 72, 78, 255))
        f = clamp(rating - i)
        if f > 0:
            g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(g).polygon(star_pts(x, h / 2, STAR, s), fill=rgba(GOLD))
            if f < 1:
                g = g.crop((0, 0, int(round(x - STAR * s / 2 + STAR * s * f)), h))
            st.alpha_composite(g, (0, 0))
        lay.alpha_composite(fade(st, clamp(u * 2.5)))
    comp(L, lay, x_left - pad, cy - h / 2)


# ---------------------------------------------------------------- scenes (L: transparent layer, lt: local time)


def sc_hook(L, lt, t):
    # RGB board lights up under a slow, smooth dolly; key glows on every thock
    fr = clip_at("rgb", max(0.0, t - 0.06) * 30).convert("RGBA")
    fr.putalpha(RGB_MATTE)
    rng = np.random.default_rng(9)
    rows = [35, 92, 150, 205, 258, 312]
    for b in HOOK_KEYS:
        x, y = rng.uniform(90, 1050), rows[int(rng.integers(0, 6))]
        age = t - (tb(b) + 0.03)
        if -0.03 < age < 0.4:
            a = clamp((age + 0.03) / 0.04) * (1 - e_out3(clamp(age / 0.4)))
            comp(fr, fade(KEYGLOW, a), x - 115, y - 115)
    u = e_io3(prog(t, 0, 2.6))
    lit = clamp((t - 0.15) / 0.5)
    put(L, GLOW_S, 540, 1060, 1.5, 0.25 + 0.45 * lit)
    # slow dolly-out: macro close-up of the keys -> the whole board, centred, before the sweep
    put3d(L, fr, 540, 900 + 60 * u, rx=30 - 8 * u, ry=-14 + 14 * u, rz=-6 + 5 * u, s=1.22 - 0.42 * u)
    # SOUND ON pill (brand crimson) with pulsing waves
    q = e_back(prog(t, -0.18, 0.5), 1.4)
    pill = sound_pill(t)
    put(L, pill, CX, EY + 10, 0.85 + 0.15 * q, clamp(q * 1.6))


def sound_pill(t):
    tx = text("SOUND ON", 30, 800, WHITE, 0.12)
    w, h = tx.w + 140, 84
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba(CRIMSON))
    sx, sy = 34, h // 2
    d.rectangle((sx, sy - 8, sx + 9, sy + 8), fill=rgba(WHITE))
    d.polygon([(sx + 9, sy - 8), (sx + 22, sy - 18), (sx + 22, sy + 18), (sx + 9, sy + 8)], fill=rgba(WHITE))
    for i, r in enumerate((10, 18)):
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 7 - i * 1.1))
        d.arc((sx + 24 - r, sy - r, sx + 24 + r, sy + r), -50, 50, fill=rgba(WHITE, 255 * a), width=3)
    im.alpha_composite(tx.im, (82, (h - tx.h) // 2 + 1))
    return im


def sc_reveal(L, lt, t):
    lg = scaled(A["logo"], 72 / A["logo"].height)
    tx_logo = Txt(lg, lg.height)
    reveal(L, tx_logo, CX - lg.width / 2, 250, e_out5(prog(lt, 0.0, 0.7)))
    hv = scaled(A["havoc"], 880 / A["havoc"].width)
    p = e_out5(prog(lt, 0.12, 0.9))
    if p > 0:
        wipe = int(hv.width * p)
        sp = light_sweep(hv, prog(lt, 0.75, 0.9))
        sp = sp.crop((0, 0, max(1, wipe), sp.height))
        s = 1.05 - 0.05 * p
        comp(L, fade(scaled(sp, s), clamp(p * 1.4)), CX - hv.width * s / 2, 470 - hv.height * s / 2)
    u = e_out5(prog(lt, 0.45, 0.7))
    if u > 0:
        layer_draw(L, lambda d: d.line((CX - 150 * u, 538, CX + 150 * u, 538), fill=rgba(CRIMSON), width=4))
    tx = text("75% WIRELESS MECHANICAL KEYBOARD", 21, 600, GREY, 0.3)
    line_anim(L, tx, CX, 596, 0.55, lt)
    q = e_out5(prog(lt, 0.1, 1.1))
    product(L, A["kb_tilt"], CX, 1010 + 170 * (1 - q) + 7 * math.sin(t * 2.0), 0.96, rx=12, ry=-9 + 7 * e_io3(
        prog(lt, 0, 2.2)), rz=0, a=clamp(q * 1.5))


VENOM = [("sw_top", 715, "TOP HOUSING", "lets the RGB through"), ("sw_stem", 905, "STEM", "2.0mm pre-travel"),
         ("sw_spring", 1068, "SPRING", "45gf actuation"), ("sw_base", 1212, "BASE", "5-pin · 50M keystrokes")]


def sc_venom(L, lt, t):
    heading(L, lt, "VENOM LINEAR SWITCH", ["SMOOTH, TOP", "TO BOTTOM."])
    cx = 330
    for i, (nm, ey, lab, sub) in enumerate(VENOM):
        q = e_out5(prog(lt, 0.12 + i * 0.05, 0.85))
        y = lerp(960, ey, q) + 4 * math.sin(t * 2.2 + i)
        put(L, A[nm], cx, y, 1.0, clamp(prog(lt, 0.02, 0.3) * 1.2))
    for i, (nm, ey, lab, sub) in enumerate(VENOM):
        # leader lines styled like the product page: crimson rule, dot on the part, square node at the label
        x0 = cx + A[nm].width / 2 + 10
        x1 = 585
        t_c = loc(EV["venom"][i], "venom")
        u = e_out3(prog(lt, t_c, 0.4))
        if u > 0:
            def _d(d, x0=x0, ey=ey, u=u):
                xe = lerp(x0, x1, u)
                d.line((x0, ey, xe, ey), fill=rgba(CRIMSON_LT, 230 * u), width=2)
                r = 5 * e_back(u, 2)
                d.ellipse((x0 - r, ey - r, x0 + r, ey + r), fill=rgba(CRIMSON_LT))
                q = 6 * clamp((u - 0.8) / 0.2)
                if q > 0:
                    d.rectangle((xe - q, ey - q, xe + q, ey + q), fill=rgba(CRIMSON))
            layer_draw(L, _d)
        t1 = text(lab, 30, 800, WHITE, 0.02)
        t2 = text(sub, 22, 0, GREY, 0.0, inter=True)
        reveal(L, t1, 604, ey - 4 - t1.base + 6, e_out5(prog(lt, t_c + 0.16, 0.55)))
        reveal(L, t2, 605, ey + 30 - t2.base + 4, e_out5(prog(lt, t_c + 0.24, 0.55)))


def sc_acoustic(L, lt, t):
    heading(L, lt, "5-LAYER SOUND DAMPENING", ["RICH, MUTED", "THOCK."])
    # exploded-layer footage decelerates to a stop (like the waveform settling); sub-frame blended for 60 fps
    fi = 38 * e_out3(prog(lt, 0.0, 2.3))
    i0 = int(fi)
    sp = layers_frame(i0)
    if fi - i0 > 0.02:
        sp = Image.blend(sp, layers_frame(i0 + 1), fi - i0)
    q = e_out5(prog(lt, 0.1, 0.9))
    put(L, sp, CX, 930 + 90 * (1 - q), 0.96 + 0.04 * q, clamp(q * 1.3))
    # crimson waveform that settles (dampening)
    amp = 46 * (1 - e_io3(prog(lt, 0.4, 1.4))) + 4
    a = clamp(prog(lt, 0.3, 0.4))
    if a > 0:
        pts = []
        for x in range(170, 911, 5):
            u = (x - 170) / 740
            env = math.sin(math.pi * u)
            pts.append((x, 1222 + amp * env * math.sin(u * 30 - lt * 7) * (0.7 + 0.3 * math.sin(u * 9 + lt * 3))))
        layer_draw(L, lambda d: d.line(pts, fill=rgba(CRIMSON_LT, 255 * a), width=4, joint="curve"))
    labels = ["FOAM", "SWITCH FILMS", "SILICONE"]
    sps = [chip(s) for s in labels]
    total = sum(s.width for s in sps) + 18 * (len(sps) - 1)
    x = CX - total / 2
    for i, sp in enumerate(sps):
        u = e_out5(prog(lt, loc(EV["chips"][i], "acoustic"), 0.6))
        comp(L, fade(sp, u), x, 1300 - sp.height / 2 + 26 * (1 - u))
        x += sp.width + 18


def sc_build(L, lt, t):
    ts = loc(EV["swap"], "build")  # gasket -> hot-swap
    # text roll: the old lines leave through the top of their boxes before the new ones rise in
    heading(L, lt, "NO BOLTS · NO STRESS POINTS", ["GASKET", "MOUNTED."], t_out=ts - 0.3, out_dur=0.24)
    if lt >= ts:
        heading(L, lt - ts, "3 & 5-PIN · NO SOLDERING", ["HOT-SWAP", "ANY SWITCH."])
    xo = e_in3(prog(lt, ts - 0.28, 0.3))  # gasket board accelerates out...
    x = e_out3(prog(lt, ts - 0.04, 0.55))  # ...hot-swap board decelerates in
    q = e_out5(prog(lt, 0.08, 0.9))
    sp = A["kb_gasket"]
    pose = dict(cx=CX, cy=990 + 130 * (1 - q) - 60 * xo, rx=40, ry=-7 + 9 * e_io3(prog(lt, 0, 1.2)), rz=-2,
                s=0.98 - 0.04 * xo)
    a_g = clamp(q * 1.4) * (1 - xo)
    product(L, sp, a=a_g, **{k: pose[k] for k in pose})
    if a_g > 0.05:
        def _rings(d):
            for i, (px, py) in enumerate(GASKETS):
                X, Y = proj_point(px, py, sp.width, sp.height, pose["rx"], pose["ry"], pose["rz"], pose["s"],
                                  pose["cx"], pose["cy"])
                age = lt - loc(EV["gasket"][i % len(EV["gasket"])], "build")
                if age > 0:
                    ph = (age / 0.9) % 1
                    r = 10 + 34 * e_out3(ph)
                    d.ellipse((X - r, Y - r * 0.55, X + r, Y + r * 0.55), outline=rgba(CRIMSON_LT, 255 * (1 - ph) * a_g),
                              width=3)
                    d.ellipse((X - 5, Y - 5, X + 5, Y + 5), fill=rgba(WHITE, 255 * a_g))
        layer_draw(L, _rings)
    if x > 0:
        product(L, A["kb_swap"], CX, 1000 + 70 * (1 - x) + 6 * math.sin(t * 2.2), 0.98 + 0.03 * (1 - x), rx=10,
                ry=-10 + 8 * x, rz=-1, a=clamp(x * 1.4), glow=0.45)


def sc_keycaps(L, lt, t):
    heading(L, lt, "DOUBLESHOT PBT KEYCAPS", ["LEGENDS THAT", "NEVER WEAR OFF."])
    sp = A["keycap"]
    s = 1.34
    q = e_out5(prog(lt, 0.1, 0.9))
    cy = 905 + 80 * (1 - q)
    img = light_sweep(sp, prog(lt, 0.55, 1.0), 0.14, 0.7)
    put(L, GLOW_S, CX, cy + 160, 1.2, 0.35 * q)
    put(L, img, CX, cy, s, clamp(q * 1.4))
    left = CX - sp.width * s / 2
    for i, (fx, lab, sub) in enumerate([(125 / 640, "MOLDED-IN LEGEND", "never printed on top"),
                                        (455 / 640, "THICKER WALLS", "a rounder, deeper tone")]):
        x = left + fx * sp.width * s
        t_c = loc(EV["keycap"][i], "keycaps")
        u = e_out3(prog(lt, t_c, 0.4))
        if u > 0:
            y0 = cy + sp.height * s / 2 + 18

            def _d(d, x=x, y0=y0, u=u):
                d.line((x, y0, x, y0 + 46 * u), fill=rgba(CRIMSON_LT), width=2)
                r = 5 * e_back(u, 2)
                d.ellipse((x - r, y0 - r, x + r, y0 + r), fill=rgba(CRIMSON_LT))
            layer_draw(L, _d)
        t1 = text(lab, 28, 800, WHITE, 0.03)
        t2 = text(sub, 22, 0, GREY, inter=True)
        reveal(L, t1, x - t1.w / 2, 1172 - t1.base, e_out5(prog(lt, t_c + 0.12, 0.55)))
        reveal(L, t2, x - t2.w / 2, 1208 - t2.base, e_out5(prog(lt, t_c + 0.2, 0.55)))


def sc_perf(L, lt, t):
    heading(L, lt, "TRI-MODE WIRELESS", ["BUILT WITHOUT", "COMPROMISE."])
    cw, ch, gap = 420, 210, 24
    x0, y0 = CX - (2 * cw + gap) / 2, 960 - (2 * ch + gap) / 2 + 20
    cards = [("BATTERY", 4000, "mAh", None), ("POLLING RATE", 1000, "Hz", None),
             ("CONNECTIVITY", None, "", ("BT 5.0", "2.4G · wired · 3 devices")), ("LAYOUT", 75, "%", None)]
    for i, (lab, val, unit, alt) in enumerate(cards):
        r, cidx = divmod(i, 2)
        x, y = x0 + cidx * (cw + gap), y0 + r * (ch + gap)
        t_c = loc(EV["cards"][i], "perf")
        u = e_out5(prog(lt, t_c, 0.7))
        if u <= 0.003:
            continue
        cl = card_bg(cw, ch)
        d = ImageDraw.Draw(cl)
        tl = text(lab, 19, 0, GREY, 0.18, inter=True)
        cl.alpha_composite(tl.im, (30, 30))
        if val is not None:
            pv = e_out3(prog(lt, t_c + 0.12, 1.1))
            num = text(f"{int(round(val * pv))}", 78, 900, WHITE)
            un = text(unit, 34, 700, CRIMSON_LT)
            bx = 30
            cl.alpha_composite(num.im, (bx, ch - 34 - num.base))
            cl.alpha_composite(un.im, (bx + num.w + 8, ch - 34 - un.base))
            if lab == "BATTERY":
                d.rounded_rectangle((cw - 112, 30, cw - 40, 58), 6, outline=rgba(WHITE, 200), width=3)
                d.rectangle((cw - 39, 38, cw - 34, 50), fill=rgba(WHITE, 200))
                d.rectangle((cw - 106, 36, cw - 106 + 60 * pv, 52), fill=rgba(CRIMSON_LT))
        else:
            big = text(alt[0], 60, 900, WHITE)
            sm = text(alt[1], 21, 0, GREY, inter=True)
            cl.alpha_composite(big.im, (30, ch - 66 - big.base))
            cl.alpha_composite(sm.im, (32, ch - 26 - sm.base))
        comp(L, fade(cl, clamp(u * 1.3)), x, y + 40 * (1 - u))


def sc_display(L, lt, t):
    ts = loc(EV["rgb"], "display")
    heading(L, lt, "BUILT-IN LED DISPLAY", ["VIVID LED DISPLAY.", "OWN YOUR IDENTITY."], t_out=ts - 0.3, light=True,
            out_dur=0.24)
    xo = e_in3(prog(lt, ts - 0.3, 0.32))
    x = e_out3(prog(lt, ts - 0.04, 0.6))
    q = e_out5(prog(lt, 0.05, 0.9))
    if xo < 1:
        sp = display_card()
        z = 1.0 + 0.05 * prog(lt, 0, ts)
        put(L, sp, CX, 975 + 70 * (1 - q) - 70 * xo, z * (1 - 0.04 * xo), clamp(q * 1.3) * (1 - xo))
    if lt >= ts:
        heading(L, lt - ts, "THE HAVOC EXPERIENCE", ["LIGHT IT", "YOUR WAY."], light=True)
        fr = clip_at("rgb", 20 + (lt - ts) * 30 * 1.2).convert("RGBA")
        fr.putalpha(RGB_MATTE)
        put(L, GLOW_S, CX, 1080, 1.3, 0.45 * x)
        put3d(L, fr, CX, 960 + 70 * (1 - x), rx=22, ry=-6 + 8 * prog(lt, ts, 1.5), rz=0, s=0.84 + 0.04 * (1 - x),
              a=clamp(x * 1.2))


def sc_gaming(L, lt, t):
    heading(L, lt, "THE LETHAL BLACK EDGE", ["BUILT FOR", "COMPETITIVE", "GAMING."], size=86)
    fr = clip_at("game", min(37.0, lt * 30 * 0.5))
    m = game_mask()
    q = e_out5(prog(lt, 0.12, 0.9))
    z = 1.0 + 0.05 * prog(lt, 0, 2.0)
    w, h = m.size
    big = fr.resize((int(w * z), int(h * z)), Image.BILINEAR)
    ox, oy = (big.width - w) // 2, (big.height - h) // 2
    card = big.crop((ox, oy, ox + w, oy + h)).convert("RGBA")
    card.putalpha(m)
    cy = 925 + 80 * (1 - q)
    put(L, GLOW_S, CX, cy + 160, 1.4, 0.4 * q)
    comp(L, fade(card, clamp(q * 1.3)), CX - w / 2, cy - h / 2)
    a = clamp(q * 1.3)
    layer_draw(L, lambda d: d.rounded_rectangle((CX - w / 2 - 1, cy - h / 2 - 1, CX + w / 2, cy + h / 2), 26,
                                                outline=rgba(CRIMSON, 255 * a), width=3))
    t1 = text("LETHAL TAP", 44, 900, WHITE, 0.02)
    t2 = text("LAST-INPUT PRIORITY", 20, 700, CRIMSON_LT, 0.3)
    line_anim(L, t1, CX, 1218, 0.5, lt)
    line_anim(L, t2, CX, 1262, 0.6, lt)


def sc_price(L, lt, t):
    eyebrow(L, "HAVOC · 75% WIRELESS", lt, 0.0)
    q = e_out5(prog(lt, 0.05, 1.0))
    product(L, A["kb_hero"], CX, 640 + 120 * (1 - q) + 6 * math.sin(t * 2), 0.76, a=clamp(q * 1.4), glow=0.7)
    pr = text("₹6,449", 150, 900, WHITE, 0.0)
    p = e_out5(prog(lt, 0.12, 0.7))
    if p > 0:
        sp = light_sweep(pr.im, prog(lt, loc(20.3, "price"), 0.8), 0.18, 0.6)
        reveal(L, Txt(sp, pr.base), CX - pr.w / 2, 1012 - pr.base, p)
    # rating row (stars + count) centred as one group
    rv = text("4.68 · 325 reviews", 24, 0, GREY, inter=True)
    x_left = CX - (STARS_W + 14 + rv.w) / 2
    t_s = loc(EV["stars"], "price")
    stars(L, x_left, 1080, lt, t_s)
    reveal(L, rv, x_left + STARS_W + 14, 1080 - rv.base + 9, e_out5(prog(lt, t_s + 0.12, 0.5)))
    perks = ["18-MONTH WARRANTY", "FREE DELIVERY · INDIA", "7-DAY REPLACEMENT", "EMI FROM ₹227/MO"]
    for i, s in enumerate(perks):
        r, cidx = divmod(i, 2)
        u = e_out5(prog(lt, loc(EV["perks"][i], "price"), 0.6))
        if u <= 0.003:
            continue
        b = check_badge(s)
        x = CX - (2 * 420 + 20) / 2 + cidx * 440
        y = 1160 + r * 80
        comp(L, fade(b, u), x, y - b.height / 2 + 24 * (1 - u))


@lru_cache(maxsize=1)
def shop_button():
    w, h = 700, 128
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba(CRIMSON))
    tx = text("SHOP NOW", 46, 900, WHITE, 0.06)
    x = (w - tx.w) // 2 - 30
    im.alpha_composite(tx.im, (x, (h - tx.h) // 2 + 1))
    ax = x + tx.w + 26
    d.line((ax, h / 2, ax + 44, h / 2), fill=rgba(WHITE), width=8)
    d.polygon([(ax + 54, h / 2), (ax + 32, h / 2 - 19), (ax + 32, h / 2 + 19)], fill=rgba(WHITE))
    return im


@lru_cache(maxsize=1)
def shop_mask():
    w, h = shop_button().size
    return round_mask(w, h, h // 2)


def shop_button_at(lt, tap):
    """SHOP NOW button with a soft ripple from the tap point, clipped to the pill."""
    btn = shop_button()
    age = lt - tap
    if age < 0 or age > 0.8:
        return btn
    btn = btn.copy()
    w, h = btn.size
    r = 24 + 640 * e_out3(age / 0.8)
    al = 0.36 * (1 - e_in3(age / 0.8))
    rip = Image.new("L", (w, h), 0)
    px = w / 2 + 150
    ImageDraw.Draw(rip).ellipse((px - r, h / 2 - r, px + r, h / 2 + r), fill=int(255 * al))
    white = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    white.putalpha(ImageChops.multiply(rip, shop_mask()))
    btn.alpha_composite(white)
    return btn


def sc_cta(L, lt, t):
    te = loc(EV["end"], "cta")  # -> end lockup
    tap = loc(EV["tap"], "cta")
    x = e_io3(prog(lt, te - 0.1, 0.6))
    if x < 1:
        a = 1 - x
        heading(L, lt, "AVAILABLE NOW", ["GRAB", "YOURS."], t_out=te - 0.1)
        q = e_out5(prog(lt, 0.08, 1.0))
        product(L, A["kb_tilt"], CX, 860 + 120 * (1 - q) + 6 * math.sin(t * 2.1), 0.6, rx=10,
                ry=-10 + 10 * prog(lt, 0, 2.4), a=clamp(q * 1.4) * a, glow=0.5)
        press = 1 - 0.035 * math.sin(math.pi * clamp((lt - tap) / 0.22)) if lt >= tap else 1.0
        breathe = 1 + 0.012 * math.sin(lt * 5)
        ub = e_back(prog(lt, 0.35, 0.6), 1.3)
        pulse = math.exp(-max(0.0, lt - tap) / 0.35) if lt >= tap else 0.0
        put(L, GLOW_S, CX, 1170, 1.0 * breathe, (0.5 + 0.4 * pulse) * clamp(ub) * a)
        put(L, shop_button_at(lt, tap), CX, 1170, (0.9 + 0.1 * ub) * press * breathe, clamp(ub * 1.5) * a)
        if lt < tap + 0.3:  # finger glides in and presses
            qq = e_io3(prog(lt, 0.3, tap - 0.3))
            fx, fy = lerp(880, CX + 150, qq), lerp(1380, 1176, qq)
            pr_ = clamp((lt - tap) / 0.3)
            fr_ = 26 - 6 * math.sin(math.pi * clamp((lt - tap) / 0.22))
            fa = clamp(prog(lt, 0.3, 0.2)) * (1 - e_in3(pr_)) * a
            layer_draw(L, lambda d: d.ellipse((fx - fr_, fy - fr_, fx + fr_, fy + fr_),
                                              fill=(255, 255, 255, int(110 * fa)),
                                              outline=(255, 255, 255, int(235 * fa)), width=3))
        url = text("lethalblack.com", 26, 0, GREY, 0.04, inter=True)
        line_anim(L, url, CX, 1272, 0.5, lt, te - 0.1)
    if x > 0:
        u = e_out5(prog(lt, te, 0.9))
        lg = light_sweep(scaled(A["logo"], 560 / A["logo"].width), prog(lt, te + 0.3, 0.8))
        put(L, GLOW, CX, 900, 0.6, 0.35 * u)
        put(L, lg, CX, 860 - 30 * (1 - u), 0.96 + 0.04 * u, clamp(u * 1.3))
        hv = scaled(A["havoc"], 520 / A["havoc"].width)
        put(L, hv, CX, 1035 + 30 * (1 - e_out5(prog(lt, te + 0.15, 0.8))), 1.0,
            clamp(e_out5(prog(lt, te + 0.15, 0.8)) * 1.3))
        eyebrow(L, "BUILT WITHOUT COMPROMISE", lt, te + 0.3, y=1110)


SCENES = [  # name, start, end, fn, incoming transition
    ("hook", 0.0, tb(5), sc_hook, None),
    ("reveal", tb(5), tb(9), sc_reveal, "sweep"),
    ("venom", tb(9), tb(13), sc_venom, "slide"),
    ("acoustic", tb(13), tb(17), sc_acoustic, "slide"),
    ("build", tb(17), tb(21), sc_build, "slide"),
    ("keycaps", tb(21), tb(25), sc_keycaps, "slide"),
    ("perf", tb(25), tb(31), sc_perf, "slide"),
    ("display", tb(31), tb(37), sc_display, "zoom"),
    ("gaming", tb(37), tb(41), sc_gaming, "sweep"),
    ("price", tb(41), tb(47), sc_price, "slide"),
    ("cta", tb(47), DUR + 1, sc_cta, "slide"),
]
# local-time offset: entrances start as the incoming layer becomes visible
LT_SHIFT = {None: 0.0, "slide": 0.02, "zoom": 0.02, "sweep": -0.08}
SCENE_OF = {n: (st, tin) for n, st, en, fn, tin in SCENES}


def loc(T, name):
    """Absolute time T -> that scene's local time (lt includes the entrance offset)."""
    st, tin = SCENE_OF[name]
    return T - st + LT_SHIFT[tin]


MOOD = {"hook": (0.22, 0.0), "reveal": (0.5, 0.1), "venom": (0.32, 0.07), "acoustic": (0.3, 0.06),
        "build": (0.32, 0.07), "keycaps": (0.3, 0.07), "perf": (0.34, 0.06), "display": (0.26, 0.05),
        "gaming": (0.42, 0.06), "price": (0.48, 0.1), "cta": (0.45, 0.08)}


# slide / zoom handoff: the outgoing layer accelerates out (ease-in) and is gone by the cut; the incoming layer
# enters already moving at about the same speed (ease-out), so motion is continuous and text never double-exposes.
OUT_D, IN_D = 0.38, 0.62
SL_OUT, SL_IN = 170.0, 200.0


def layer_state(i, t):
    """Transform of scene layer i at time t: (dy, scale, alpha, vy) or None when not visible."""
    name, s, e, fn, tin = SCENES[i]
    tout = SCENES[i + 1][4] if i + 1 < len(SCENES) else None
    if t < s - 0.6 or t > e + 0.6:
        return None
    dy, sc, a, vy = 0.0, 1.0, 1.0, 0.0
    # incoming
    if tin in ("slide", "zoom"):
        t0 = s - 0.02
        if t < t0:
            return None
        p = prog(t, t0, IN_D)
        a *= e_out3(clamp(p * IN_D / 0.32))
        if tin == "slide":
            dy += SL_IN * (1 - e_out5(p))
            vy += -SL_IN * 5 * (1 - p) ** 4 / IN_D if p < 1 else 0.0
        else:
            sc *= 0.92 + 0.08 * e_out5(p)
    elif tin == "sweep":
        if t < s:
            return None
        dy += 110 * (1 - e_out5(prog(t, s, 0.5)))
    # outgoing
    if tout in ("slide", "zoom"):
        t1 = e + 0.02
        if t >= t1:
            return None
        p = prog(t, t1 - OUT_D, OUT_D)
        a *= 1 - e_in3(p)
        if tout == "slide":
            dy -= SL_OUT * e_in3(p)
            vy -= SL_OUT * 3 * p ** 2 / OUT_D if 0 < p < 1 else 0.0
        else:
            sc *= 1 + 0.12 * e_in3(p)
    elif tout == "sweep":
        if t >= e:
            return None
        dy -= 90 * e_in3(prog(t, e - 0.45, 0.45))
    return dy, sc, a, vy


def mood_at(t):
    w_tot, g, sp = 0.0, 0.0, 0.0
    for name, s, e, fn, tin in SCENES:
        w = clamp(min(t - s + 0.3, e - t + 0.3) / 0.6)
        if w > 0:
            g += MOOD[name][0] * w
            sp += MOOD[name][1] * w
            w_tot += w
    return (g / w_tot, sp / w_tot) if w_tot else (0.3, 0.05)


@lru_cache(maxsize=1)
def sweep_panel():
    ph = int(H * 1.36)
    pw = W + 40
    slant = int(W * math.tan(math.radians(7)))
    im = Image.new("RGBA", (pw, ph + slant), (0, 0, 0, 0))
    g = np.linspace(0, 1, ph + slant)[:, None]
    col = (np.array((150, 0, 36)) * g + np.array((205, 8, 56)) * (1 - g)).astype(np.uint8)
    fill = Image.fromarray(np.repeat(col[:, None, :], pw, axis=1).reshape(ph + slant, pw, 3), "RGB").convert("RGBA")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon([(0, slant), (pw, 0), (pw, ph), (0, ph + slant)], fill=255)
    im.paste(fill, (0, 0), m)
    lg = scaled(A["logo"], 520 / A["logo"].width)
    im.alpha_composite(lg, ((pw - lg.width) // 2, (im.height - lg.height) // 2))
    return im


SW_IN, SW_HOLD, SW_OUT = 0.30, 0.06, 0.32  # crimson brand sweep: glide in, hold on the logo, glide out


def sweep_pos(t, s):
    """Panel centre y and velocity (px/s) for the sweep that cuts to the scene starting at s."""
    half = sweep_panel().height / 2
    y0, ym, y1 = H + half + 10, H / 2, -half - 10  # starts and ends fully off-screen
    ta = s - SW_HOLD - SW_IN
    if t < ta or t > s + SW_OUT:
        return None, 0.0
    if t < s - SW_HOLD:
        p = (t - ta) / SW_IN
        return lerp(y0, ym, e_out3(p)), (ym - y0) * 3 * (1 - p) ** 2 / SW_IN
    if t < s:
        return ym, 0.0
    p = (t - s) / SW_OUT
    return lerp(ym, y1, e_in3(p)), (y1 - ym) * 3 * p ** 2 / SW_OUT


def draw_sweep(c, t):
    for name, s, e, fn, tin in SCENES:
        if tin != "sweep":
            continue
        yc, v = sweep_pos(t, s)
        if yc is None:
            continue
        panel = sweep_panel()
        k = 1 + abs(v) / FPS / 14
        sp = panel
        if k > 1.04:
            sp = panel.resize((panel.width, max(2, int(panel.height / k))), Image.BILINEAR).resize(panel.size,
                                                                                                 Image.BILINEAR)
        comp(c, sp, -20, yc - panel.height / 2)


# ---------------------------------------------------------------- captions (gliding crimson pill)

VO_META = json.load(open(f"{VO_DIR}/vo.json"))


def build_words():
    words = []
    for key, t0 in VO_AT.items():
        txt = VO_META[key]["text"].upper().replace(",", "").replace(".", "")
        dur = VO_META[key]["dur"]
        ws = txt.split()
        wts = [len(w.replace("-", "")) + 2.0 for w in ws]
        tot, acc = sum(wts), 0.0
        chunks, cur = [], []
        for w in ws:
            if cur and (len(cur) == 3 or sum(len(x) + 1 for x in cur) + len(w) > 17):
                chunks.append(cur)
                cur = []
            cur.append(w)
        chunks.append(cur)
        idx = 0
        for ci, ch in enumerate(chunks):
            for w in ch:
                words.append(dict(key=key, w=w, st=t0 + 0.02 + acc / tot * dur * 0.95, ci=(key, ci), end=t0 + dur + 0.2))
                acc += wts[idx]
                idx += 1
    for i, w in enumerate(words):  # chunk end = next chunk start (same phrase) or phrase end
        nxt = [x["st"] for x in words[i + 1:] if x["key"] == w["key"] and x["ci"] != w["ci"]]
        w["cend"] = min(nxt[0], w["end"]) if nxt else w["end"]
    return words


WORDS = build_words()
CAP_SIZE = 54


@lru_cache(maxsize=256)
def cap_word(w):
    tx = text(w, CAP_SIZE, 800, WHITE, 0.02)
    sh = Image.new("RGBA", (tx.w + 30, tx.h + 30), (0, 0, 0, 0))
    k = Image.new("RGBA", tx.im.size, (0, 0, 0, 255))
    k.putalpha(tx.im.getchannel("A"))
    sh.alpha_composite(k, (15, 18))
    return tx, sh.filter(ImageFilter.GaussianBlur(7))


def caption_chunks():
    out = []
    for w in WORDS:
        if not out or out[-1][0]["ci"] != w["ci"]:
            out.append([])
        out[-1].append(w)
    return out


CHUNKS = caption_chunks()


def chunk_windows():
    """[c0, c1) per chunk; a chunk never outlives the start of the next one, so captions never stack."""
    wins = []
    for k, ch in enumerate(CHUNKS):
        c0, c1 = ch[0]["st"] - 0.04, ch[0]["cend"] - 0.04
        if k + 1 < len(CHUNKS):
            c1 = min(c1, CHUNKS[k + 1][0]["st"] - 0.04)
        wins.append((c0, c1))
    return wins


WINS = chunk_windows()


def captions(c, t):
    for chunk, (c0, c1) in zip(CHUNKS, WINS):
        if c0 <= t < c1:
            caption_chunk(c, chunk, t, c0, c1)


def caption_chunk(c, chunk, t, c0, c1):
    sprites = [cap_word(w["w"]) for w in chunk]
    gap = 18
    total = sum(s[0].w for s in sprites) + gap * (len(sprites) - 1)
    sc = min(1.0, 900 / total)
    x = CX - total * sc / 2
    xs = []
    for (tx, _sh) in sprites:
        xs.append(x)
        x += (tx.w + gap) * sc
    out = 1 - e_in3(prog(t, c1 - 0.13, 0.13))
    lift = -14 * (1 - out)
    spoken = [i for i, w in enumerate(chunk) if w["st"] <= t]
    lay = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    base_y = 80
    if spoken:
        i = spoken[-1]
        u = e_out3(prog(t, chunk[i]["st"], 0.14))
        tx = sprites[i][0]
        ph = int(CAP_SIZE * 1.32)
        x0, x1 = xs[i] - 14 * sc, xs[i] + tx.w * sc + 14 * sc
        if i > 0:
            px0, px1 = xs[i - 1] - 14 * sc, xs[i - 1] + sprites[i - 1][0].w * sc + 14 * sc
            x0, x1 = lerp(px0, x0, u), lerp(px1, x1, u)
            pa = 1.0
        else:
            cxp = (x0 + x1) / 2
            x0, x1 = lerp(cxp, x0, e_back(u, 1.6)), lerp(cxp, x1, e_back(u, 1.6))
            pa = clamp(u * 2)
        ImageDraw.Draw(lay).rounded_rectangle((x0, base_y - ph / 2, x1, base_y + ph / 2), 16,
                                              fill=rgba(CRIMSON, 255 * pa))
    for j, (tx, sh) in enumerate(sprites):
        e_in = e_out5(prog(t, c0 + j * 0.035, 0.3))
        a = e_in * (1.0 if j in spoken else 0.5)
        if a <= 0.003:
            continue
        dy = 22 * (1 - e_in)
        ts = scaled(tx.im, sc)
        top = base_y - ts.height / 2 + dy + 2
        comp(lay, fade(scaled(sh, sc), 0.55 * a), xs[j] - 15 * sc, top - 15 * sc + 3)
        comp(lay, fade(ts, a), xs[j], top)
    comp(c, fade(lay, out) if out < 1 else lay, 0, CAP_Y - base_y + lift)


# ---------------------------------------------------------------- frame


def background(t):
    c = BG.copy()
    g, sp = mood_at(t)
    put(c, GLOW, 230 + 90 * math.sin(t * 0.33), 520 + 90 * math.cos(t * 0.27), 1.0, g)
    put(c, GLOW, 860 + 70 * math.cos(t * 0.29), 1480 + 80 * math.sin(t * 0.21), 0.9, g * 0.75)
    comp(c, WMARK, 260 + 30 * math.sin(t * 0.15), 760 + 20 * math.cos(t * 0.12))
    put(c, SPOT, CX, 980, 1.0, sp)
    return c


def render(fi):
    t = fi / FPS
    c = background(t)
    for i, (name, s, e, fn, tin) in enumerate(SCENES):
        st = layer_state(i, t)
        if st is None:
            continue
        dy, sc, a, vy = st
        if a <= 0.003:
            continue
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(L, t - s + LT_SHIFT[tin], t)
        if abs(sc - 1) > 1e-3:
            Ls = L.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
            L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            comp(L, Ls, (W - Ls.width) / 2, (H - Ls.height) / 2)
        k = 1 + abs(vy) / FPS / 8  # vertical motion blur, fades out continuously
        if k > 1.04:
            L = L.resize((W, max(2, int(H / k))), Image.BILINEAR).resize((W, H), Image.BILINEAR)
        if a < 0.999:
            L = fade(L, a)
        comp(c, L, 0, dy)
    draw_sweep(c, t)
    captions(c, t)
    arr = np.asarray(c.convert("RGB")).astype(np.float32)
    out = arr * VIG + GRAIN[fi % len(GRAIN)][..., None] * 2.6
    if t > DUR - 0.28:
        out *= clamp((DUR - t) / 0.28)
    return np.clip(out, 0, 255).astype(np.uint8).tobytes()


def main():
    out = sys.argv[1]
    frames = sys.argv[2] if len(sys.argv) > 2 else None
    if frames:
        os.makedirs(out, exist_ok=True)
        for fi in [int(x) for x in frames.split(",")]:
            Image.frombytes("RGB", (W, H), render(fi)).save(f"{out}/f{fi:04d}.jpg", quality=92)
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(int(os.environ.get("AD_PROCS", "4"))) as pool:
        for i, buf in enumerate(pool.imap(render, range(NF), chunksize=6)):
            p.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
