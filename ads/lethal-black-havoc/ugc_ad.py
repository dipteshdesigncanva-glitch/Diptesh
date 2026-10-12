"""LETHAL BLACK HAVOC — 25s 9:16 UGC-style product ad.

Frames are pure functions of time (parallel render -> ffmpeg). Timing is in beats
of the 144 BPM soundtrack (60 beats = 25 s), so cuts, slams and pops land on the music.
Visuals come from the brand's own product-page recording (cutouts + clips).
"""
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.environ.get("AD_ROOT", os.path.dirname(os.path.abspath(__file__)))
AS = f"{ROOT}/assets"
CL = f"{ROOT}/clips"
VO_DIR = f"{ROOT}/vo"

W, H, FPS, DUR = 1080, 1920, 30, 25.0
NF = int(DUR * FPS)
BPM = 144
BEAT = 60 / BPM

INK = (8, 8, 10)
WHITE = (246, 246, 248)
GREY = (150, 153, 162)
RED = (220, 14, 60)
RED_HI = (255, 52, 92)
GOLD = (255, 196, 54)

IMPACTS = [6, 26, 36, 46, 56]
CUTS = [10, 14, 18, 20, 22, 26, 32, 34, 42, 52]
VO_AT = {"hook": 0.10, "meet": 2.60, "venom": 4.30, "layers": 5.92, "gasket": 7.56, "swap": 8.45, "pbt": 9.30,
         "specs": 10.97, "gaming": 15.10, "rating": 17.62, "price": 19.40, "cta": 21.85}
HOOK_KEYS = [0, 0.5, 1, 1.25, 1.5, 2, 2.5, 2.75, 3, 3.5, 3.75, 4, 4.5, 5, 5.25, 5.5]


def tb(b):
    return b * BEAT


# ---------------------------------------------------------------- helpers


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def eo_expo(p):
    p = clamp(p)
    return 1 - 2 ** (-10 * p) if p < 1 else 1.0


def eo_back(p, s=1.8):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def eio(p):
    p = clamp(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


INTER = "/usr/share/fonts/opentype/inter"
FONT_FILES = {
    "anton": f"{ROOT}/fonts/Anton-Regular.ttf",
    "inter": f"{INTER}/Inter-Bold.otf",
    "interm": f"{INTER}/Inter-SemiBold.otf",
    "disp": f"{INTER}/InterDisplay-Bold.otf",
    "dispx": f"{INTER}/InterDisplay-Black.otf",
}
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


@lru_cache(maxsize=256)
def F(key, size):
    return ImageFont.truetype(FONT_FILES[key], size)


@lru_cache(maxsize=800)
def tsprite(key, size, s, fill, stroke=0, stroke_fill=(0, 0, 0, 255), track=0.0):
    """Text sprite; returns (img, baseline_y)."""
    f = F(key, size)
    if track:
        xs, x = [], 0.0
        for ch in s:
            xs.append(x)
            x += f.getlength(ch) + track * size
        w = int(x - track * size)
    else:
        w = int(f.getlength(s))
    asc, desc = f.getmetrics()
    pad = stroke + 4
    im = Image.new("RGBA", (w + 2 * pad + 4, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if track:
        for i, ch in enumerate(s):
            d.text((pad + xs[i], pad), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    else:
        d.text((pad, pad), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


@lru_cache(maxsize=16)
def emoji(ch, px):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((px, int(px * im.height / im.width)), Image.LANCZOS)


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
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    return im if (w, h) == im.size else im.resize((w, h), Image.BILINEAR)


def put(c, sp, cx, cy, s=1.0, rot=0.0, a=1.0):
    if a <= 0.004:
        return
    sp = scaled(sp, s)
    if rot:
        sp = sp.rotate(rot, Image.BICUBIC, expand=True)
    sp = fade(sp, a)
    comp(c, sp, cx - sp.width / 2, cy - sp.height / 2)


def layer_draw(c, fn):
    """Draw semi-transparent shapes on their own layer, then alpha-composite onto c."""
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    c.alpha_composite(lay)


def dim(col, a):
    """Opaque colour approximating col at alpha a over a near-black background."""
    return (int(col[0] * a / 255), int(col[1] * a / 255), int(col[2] * a / 255), 255)


def round_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def smear_sprite(sp, k, vertical=False):
    if k <= 1.2:
        return sp
    w, h = sp.size
    if vertical:
        return sp.resize((w, max(2, int(h / k))), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    return sp.resize((max(2, int(w / k)), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)


def glow_of(sp, col, radius, pad=80, strength=1.0):
    g = Image.new("RGBA", (sp.width + 2 * pad, sp.height + 2 * pad), (0, 0, 0, 0))
    tint = Image.new("RGBA", sp.size, rgba(col))
    tint.putalpha(sp.getchannel("A").point(lambda v: int(v * strength)))
    g.alpha_composite(tint, (pad, pad))
    return g.filter(ImageFilter.GaussianBlur(radius))


def _rot(rx, ry, rz):
    ax, ay, az = map(math.radians, (rx, ry, rz))
    ca, sa, cb, sb, cc, sc = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def proj_pts(pts, R, s, cx, cy, f=1800.0):
    P = (np.asarray(pts, float) * s) @ R.T
    z = P[:, 2] + f
    return np.stack([cx + f * P[:, 0] / z, cy + f * P[:, 1] / z], 1)


def put3d(c, sp, cx, cy, rx=0.0, ry=0.0, rz=0.0, s=1.0, a=1.0, f=1800.0):
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
    M, Bv = [], []
    for (x, y), (X, Y) in zip(dst, src):
        M.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        Bv.append(X)
        M.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        Bv.append(Y)
    co = np.linalg.solve(np.array(M), np.array(Bv))
    out = sp.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    c.alpha_composite(fade(out, a), (x0, y0))


def proj_point(px, py, w, h, rx, ry, rz, s, cx, cy, f=1800.0):
    return proj_pts([[px - w / 2, py - h / 2, 0]], _rot(rx, ry, rz), s, cx, cy, f)[0]


# ---------------------------------------------------------------- assets


def load(n):
    return Image.open(f"{AS}/{n}.png").convert("RGBA")


A = {n: load(n) for n in ["logo", "havoc", "kb_tilt", "kb_gasket", "keycap", "kb_swap", "kb_hero", "sw_top",
                          "sw_stem", "sw_spring", "sw_base", "review0", "review1", "review2", "review3", "display"]}
RGB_MATTE = Image.open(f"{AS}/rgb_matte.png").convert("L")


@lru_cache(maxsize=None)
def clip_frames(name):
    import glob
    return [Image.open(p).convert("RGB") for p in sorted(glob.glob(f"{CL}/{name}/[0-9]*.jpg"))]


def clip(name, i):
    fr = clip_frames(name)
    return fr[int(clamp(i, 0, len(fr) - 1))]


def gasket_points():
    a = np.asarray(A["kb_gasket"]).astype(np.int16)
    red = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 2] < 120) & (a[..., 3] > 100)
    ys, xs = np.nonzero(red)
    pts = []
    used = np.zeros(len(xs), bool)
    for i in range(len(xs)):
        if used[i]:
            continue
        m = (np.abs(xs - xs[i]) < 60) & (np.abs(ys - ys[i]) < 60)
        used |= m
        if m.sum() > 40:
            pts.append((float(xs[m].mean()), float(ys[m].mean())))
    return pts


GASKETS = gasket_points()

# background: gradient + tech grid (taller for scrolling)
_g = np.linspace(0, 1, H)[:, None]
BG = Image.fromarray(np.repeat((np.array((18, 18, 22)) * (1 - _g) + np.array((5, 5, 7)) * _g)[:, None, :]
                               .astype(np.uint8).reshape(H, 1, 3), W, axis=1), "RGB").convert("RGBA")
GRID = Image.new("RGBA", (W, H + 120), (0, 0, 0, 0))
_d = ImageDraw.Draw(GRID)
for x in range(0, W, 120):
    _d.line((x, 0, x, H + 120), fill=(255, 255, 255, 9))
for y in range(0, H + 120, 120):
    _d.line((0, y, W, y), fill=(255, 255, 255, 9))
for x in range(0, W, 120):
    for y in range(0, H + 120, 120):
        _d.line((x - 6, y, x + 6, y), fill=(255, 255, 255, 30))
        _d.line((x, y - 6, x, y + 6), fill=(255, 255, 255, 30))
del _d


def radial(size, col, power=2.0):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** power
    o = np.zeros((size, size, 4), np.uint8)
    o[..., :3] = col
    o[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(o, "RGBA")


GLOW_RED = radial(1400, RED, 2.2)
GLOW_WHITE = radial(600, (255, 255, 255), 3.0)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.75)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIG = (1 - 0.45 * np.clip(_r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
del _yy, _xx, _r
_rng = np.random.default_rng(3)
DUST = [(float(_rng.uniform(0, W)), float(_rng.uniform(0, H)), float(_rng.uniform(1.0, 3.2)),
         float(_rng.uniform(20, 70)), bool(_rng.random() < 0.25)) for _ in range(70)]
GRAIN = [np.asarray(Image.fromarray(_rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))
         for _ in range(5)]


def background(c, t, glow_xy=(540, 900), glow_a=0.35, glow_s=1.0, grid_a=1.0):
    c.paste(BG, (0, 0))
    off = int((t * 30) % 120)
    if grid_a > 0:
        g = GRID.crop((0, off, W, off + H))
        comp(c, fade(g, grid_a), 0, 0)
    put(c, GLOW_RED, glow_xy[0], glow_xy[1], glow_s, 0, glow_a)
    d = ImageDraw.Draw(c)
    for (x, y, r, sp, red) in DUST:
        yy = (y - sp * t) % H
        col = dim(RED_HI, 150) if red else dim((255, 255, 255), 80)
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=col)


def frame_detail(c, k):
    """Thin inset frame + red corner brackets (premium/tech detailing)."""
    d = ImageDraw.Draw(c)
    m = 34
    d.rectangle((m, m, W - m, H - m), outline=dim((255, 255, 255), 30), width=2)
    L = 46
    for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=rgba(RED), width=5)
        d.line((x, y, x, y + sy * L), fill=rgba(RED), width=5)


# ---------------------------------------------------------------- text blocks


def chip(text, size=26, fg=WHITE, bg=RED):
    ts = tsprite("inter", size, text, rgba(fg), track=0.16)
    w, h = ts.width + 34, int(size * 1.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba(bg))
    im.alpha_composite(ts, (17 - 4, (h - ts.height) // 2))
    return im


def title_block(c, lb, chip_t, big, sub=None, y=330, size=112, big_col=WHITE):
    if lb >= 0:
        q = eo_back(lb / 0.3)
        put(c, chip(chip_t), W / 2, y, 0.6 + 0.4 * q, 0, clamp(lb / 0.12))
    if lb >= 0.1:
        q = eo_expo((lb - 0.1) / 0.35)
        lines = big if isinstance(big, (list, tuple)) else [big]
        yy = y + 60
        for i, line in enumerate(lines):
            sp = tsprite("dispx", size, line, rgba(big_col))
            qq = eo_expo((lb - 0.1 - i * 0.12) / 0.35)
            sp2 = smear_sprite(sp, 1 + 6 * (1 - qq), vertical=True)
            put(c, sp2, W / 2, yy + sp.height / 2 + 60 * (1 - qq), 1.0, 0, clamp(qq * 1.4))
            yy += int(size * 1.02)
        if sub and lb >= 0.3:
            q2 = clamp((lb - 0.3) / 0.3)
            sp = tsprite("interm", 30, sub, rgba(GREY), track=0.22)
            put(c, sp, W / 2, yy + 34, 1.0, 0, q2)


def light_sweep(sp, p, width=0.18, strength=0.85):
    """Diagonal white sheen across a sprite (p: 0..1 position)."""
    w, h = sp.size
    xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.35
    pos = lerp(-0.3, 1.3, p) * (w + h * 0.35)
    band = np.clip(1 - np.abs(xx - pos) / (width * w), 0, 1) ** 2 * strength
    a = np.asarray(sp).astype(np.float32)
    al = a[..., 3:4] / 255
    a[..., :3] = a[..., :3] + (255 - a[..., :3]) * band[..., None] * al
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def callout(c, x0, y0, x1, y1, label, sub, prog, align="left"):
    """Detailing callout: dot on the part, elbow line, label + sub text."""
    if prog <= 0:
        return
    d = ImageDraw.Draw(c)
    p1 = clamp(prog / 0.5)
    ex = lerp(x0, x1, p1)
    d.ellipse((x0 - 9, y0 - 9, x0 + 9, y0 + 9), outline=rgba(RED_HI), width=3)
    lc = dim(WHITE, 210)
    d.ellipse((x0 - 4, y0 - 4, x0 + 4, y0 + 4), fill=rgba(WHITE))
    elbow_x = x0 + (x1 - x0) * 0.35
    if ex <= elbow_x:
        d.line((x0, y0, ex, y0), fill=lc, width=3)
    else:
        u = (ex - elbow_x) / max(1, x1 - elbow_x)
        d.line((x0, y0, elbow_x, y0), fill=lc, width=3)
        d.line((elbow_x, y0, lerp(elbow_x, x1, u), lerp(y0, y1, u)), fill=lc, width=3)
    if prog > 0.45:
        q = eo_expo((prog - 0.45) / 0.4)
        sp = tsprite("dispx", 44, label, rgba(WHITE))
        sb = tsprite("interm", 28, sub, rgba(GREY))
        x = x1 + 14 if align == "left" else x1 - 14 - sp.width
        put(c, sp, x + sp.width / 2 + 30 * (1 - q), y1 - 20, 1, 0, q)
        put(c, sb, x + sb.width / 2 + 30 * (1 - q), y1 + 22, 1, 0, q)
        d.line((x1, y1, x1 + 10 if align == "left" else x1 - 10, y1), fill=rgba(RED_HI), width=4)


def stars(c, cx, cy, n_fill, size=64, gap=14):
    d = ImageDraw.Draw(c)
    total = 5 * size + 4 * gap
    for i in range(5):
        x = cx - total / 2 + i * (size + gap) + size / 2
        pts = []
        for j in range(10):
            r = size / 2 if j % 2 == 0 else size / 2 * 0.45
            a = -math.pi / 2 + j * math.pi / 5
            pts.append((x + r * math.cos(a), cy + r * math.sin(a)))
        fillv = clamp(n_fill - i)
        d.polygon(pts, fill=(60, 60, 66, 255))
        if fillv > 0:
            s = 0.6 + 0.4 * eo_back(fillv)
            pts2 = [(x + (px - x) * s, cy + (py - cy) * s) for px, py in pts]
            d.polygon(pts2, fill=rgba(GOLD))


# ---------------------------------------------------------------- captions (VO karaoke)

VO_META = json.load(open(f"{VO_DIR}/vo.json"))


def build_words():
    words = []
    for key, t0 in VO_AT.items():
        text = VO_META[key]["text"].upper().replace("PRE-LUBED", "PRE-LUBED").replace(",", "").replace(".", "")
        dur = VO_META[key]["dur"]
        ws = text.split()
        wts = [len(w.replace("-", "")) + 2.2 for w in ws]
        tot = sum(wts)
        acc = 0.0
        chunk, chunks = [], []
        for w in ws:
            chunk.append(w)
            if len(chunk) == 3 or sum(len(x) for x in chunk) > 13:
                chunks.append(chunk)
                chunk = []
        if chunk:
            chunks.append(chunk)
        ci = 0
        for ch in chunks:
            for w in ch:
                i = len([x for x in words if x["key"] == key])
                st = t0 + 0.02 + (acc / tot) * dur * 0.96
                acc += wts[i]
                words.append(dict(key=key, w=w, st=st, chunk=(key, ci), end_phrase=t0 + dur + 0.18))
            ci += 1
    return words


WORDS = build_words()
CAP_Y = 1395


def captions(c, t):
    act = [w for w in WORDS if w["st"] <= t < w["end_phrase"]]
    if not act:
        return
    cur = act[-1]
    chunk = [w for w in WORDS if w["chunk"] == cur["chunk"]]
    nxt_chunk_start = min([w["st"] for w in WORDS if w["key"] == cur["key"] and w["st"] > chunk[-1]["st"]] +
                          [cur["end_phrase"]])
    if t >= nxt_chunk_start:
        return
    size = 82
    sps = []
    for w in chunk:
        on = w is cur
        col = rgba(RED_HI) if on else rgba(WHITE)
        sps.append((tsprite("dispx", size, w["w"], col, stroke=9), on, w))
    gap = 22
    total = sum(s.width for s, _, _ in sps) + gap * (len(sps) - 1)
    scale = min(1.0, 940 / total)
    age = t - chunk[0]["st"]
    pq = eo_back(age / 0.14, 2.2)
    x = W / 2 - total * scale / 2
    # soft dark backdrop for legibility
    line_h = sps[0][0].height * scale
    d = ImageDraw.Draw(c)
    for sp, on, w in sps:
        s = scale * (0.82 + 0.18 * pq) * (1.1 if on else 1.0)
        if on:
            s *= 1 + 0.08 * (1 - eo_expo((t - w["st"]) / 0.12))
        put(c, sp, x + sp.width * scale / 2, CAP_Y, s, 0)
        x += sp.width * scale + gap * scale


# ---------------------------------------------------------------- scenes
KEY_ROWS = [35, 92, 150, 205, 258, 312]


def key_flash(sp, k):
    """Glow on 'pressed' keys at each hook keystroke."""
    rng = np.random.default_rng(7)
    picks = {b: (rng.uniform(80, 1060), KEY_ROWS[int(rng.integers(0, 6))]) for b in HOOK_KEYS}
    d = None
    for b, (x, y) in picks.items():
        age = (k - b) * BEAT
        if 0 <= age < 0.22:
            if d is None:
                sp = sp.copy()
            g = scaled(GLOW_WHITE, 0.32)
            comp(sp, fade(g, 1 - age / 0.22), x - g.width / 2, y - g.height / 2)
            d = True
    return sp


def sc_hook(c, lb, k, t):
    background(c, t, (540, 820), 0.18 + 0.2 * clamp(t / 0.5), 1.0, 0.6)
    fi = int(max(0.0, t - 0.12) * 30)
    fr = clip("rgb", fi).convert("RGBA")
    fr.putalpha(RGB_MATTE)
    fr = key_flash(fr, k)
    u = clamp(lb / 6)
    s = 1.32 - 0.12 * eio(u)
    put3d(c, fr, 560 - 60 * u, 830, rx=24 - 6 * u, ry=-16 + 10 * u, rz=-7 + 3 * u, s=s)
    # floor reflection glow
    put(c, GLOW_RED, 540, 1060, 0.55, 0, 0.25 * clamp(t / 0.4))
    # SOUND ON pill
    pulse = 1 + 0.06 * math.exp(-((lb % 1) * BEAT) / 0.09)
    pill = sound_pill()
    put(c, pill, W / 2, 330, pulse * (0.7 + 0.3 * eo_back(t / 0.25)), 0, clamp(t / 0.1))
    info = {}
    if lb >= 5.4:
        info["zb"] = 0.35 * eio((lb - 5.4) / 0.6)
    return info


@lru_cache(maxsize=1)
def sound_pill():
    ts = tsprite("dispx", 44, "SOUND ON", rgba(WHITE), track=0.06)
    e = emoji("🔊", 52)
    w, h = ts.width + e.width + 70, 92
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=rgba(RED))
    im.alpha_composite(e, (30, (h - e.height) // 2))
    im.alpha_composite(ts, (30 + e.width + 6, (h - ts.height) // 2 + 2))
    return im


def sc_reveal(c, lb, k, t):
    background(c, t, (540, 640), 0.55, 1.1)
    rot = lb * 0.08

    def _rays(d):
        for i in range(18):
            a0 = rot + 2 * math.pi * i / 18
            a1 = a0 + 0.07
            d.polygon([(540, 600), (540 + 2400 * math.cos(a0), 600 + 2400 * math.sin(a0)),
                       (540 + 2400 * math.cos(a1), 600 + 2400 * math.sin(a1))], fill=(255, 255, 255, 16))
    layer_draw(c, _rays)
    lg = scaled(A["logo"], 72 / A["logo"].height)
    put(c, lg, W / 2, 360, 1, 0, clamp((lb - 0.15) / 0.3))
    hv = scaled(A["havoc"], 940 / A["havoc"].width)
    q = eo_expo(lb / 0.35)
    hv2 = light_sweep(hv, clamp((lb - 0.4) / 0.9))
    put(c, glow_of(hv, RED, 26, 60), W / 2, 545, 1.5 - 0.5 * q, 0, 0.9 * q)
    put(c, smear_sprite(hv2, 1 + 10 * (1 - q)), W / 2, 545, 1.5 - 0.5 * q, 0, clamp(q * 1.5))
    if lb >= 0.5:
        sub = tsprite("interm", 28, "75% WIRELESS MECHANICAL KEYBOARD", rgba(WHITE), track=0.25)
        put(c, sub, W / 2, 660, 1, 0, clamp((lb - 0.5) / 0.3))
    qk = eo_expo((lb - 0.15) / 0.6)
    put(c, GLOW_RED, 540, 1240, 0.6, 0, 0.45 * qk)
    put3d(c, A["kb_tilt"], 540, 1010 + 260 * (1 - qk), rx=8 + 4 * math.sin(lb * 1.3), ry=-10 + 14 * lb / 4,
          rz=0, s=0.95 * (0.85 + 0.15 * qk), a=clamp(qk * 1.5))
    return {}


VENOM_PARTS = [  # name, exploded centre y, callout label, sub
    ("sw_top", 705, "TOP HOUSING", "lets the RGB through"),
    ("sw_stem", 905, "STEM", "2.0mm pre-travel"),
    ("sw_spring", 1072, "SPRING", "45gf actuation"),
    ("sw_base", 1222, "BASE", "5-pin · 50M keystrokes"),
]


def sc_venom(c, lb, k, t):
    background(c, t, (330, 950), 0.4)
    title_block(c, lb, "01 · SWITCHES", "VENOM", "PRE-LUBED LINEAR", y=300, size=130)
    qx = eo_back((lb - 0.2) / 0.7, 1.4)
    sc = 1.0
    cx = 320
    for i, (nm, ey, lab, sub) in enumerate(VENOM_PARTS):
        sp = A[nm]
        y = lerp(1000, ey, qx) + 6 * math.sin(lb * 2.2 + i)
        put(c, scaled(sp, sc), cx, y, 1, 0, clamp((lb - 0.05) / 0.2))
    for i, (nm, ey, lab, sub) in enumerate(VENOM_PARTS):
        sp = A[nm]
        x0 = cx + sp.width * sc / 2 - 10
        y0 = ey
        callout(c, x0, y0, 640, ey, lab, sub, (lb - (0.7 + i * 0.35)) / 0.6)
    return {}


def sc_layers(c, lb, k, t):
    background(c, t, (540, 900), 0.35)
    n = 1 + int(clamp((lb - 0.6) / 1.0) * 4.999)
    title_block(c, lb, "02 · ACOUSTICS", f"{n} LAYERS", "OF SOUND DAMPENING", y=290, size=120)
    fr = clip("layers", lb * BEAT * 30)
    arr = np.asarray(fr).astype(np.float32)
    arr = np.clip(arr * 1.45 + 8, 0, 255).astype(np.uint8)
    cw, ch = 980, 700
    card = Image.fromarray(arr).resize((cw, int(fr.height * cw / fr.width)), Image.BILINEAR)
    card = card.crop((0, 40, cw, 40 + ch)).convert("RGBA")
    card.putalpha(round_mask(cw, ch, 34))
    q = eo_expo((lb - 0.1) / 0.4)
    put(c, card, W / 2, 900 + 120 * (1 - q), 0.94 + 0.06 * q, 0, clamp(q * 1.3))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((W / 2 - cw / 2 * (0.94 + 0.06 * q), 900 + 120 * (1 - q) - ch / 2,
                         W / 2 + cw / 2, 900 + 120 * (1 - q) + ch / 2), 34, outline=dim(WHITE, 45), width=2)
    # sound wave getting dampened
    amp = 70 * (1 - clamp((lb - 0.5) / 2.6)) + 6
    pts = []
    for x in range(110, 971, 6):
        u = (x - 110) / 860
        y = 1180 + amp * math.sin(u * 26 + lb * 9) * math.exp(-1.5 * u) * (1 + 0.4 * math.sin(u * 7 + lb * 4))
        pts.append((x, y))
    d.line(pts, fill=rgba(RED_HI), width=5, joint="curve")
    for i, lab in enumerate(["FOAM", "SWITCH FILMS", "SILICONE"]):
        if lb >= 1.4 + i * 0.4:
            qq = eo_back((lb - 1.4 - i * 0.4) / 0.3)
            put(c, chip(lab, 24, WHITE, (40, 40, 48)), [270, 540, 810][i], 1270, 0.5 + 0.5 * qq)
    return {}


def sc_gasket(c, lb, k, t):
    background(c, t, (540, 920), 0.4)
    title_block(c, lb * 2, "03 · STRUCTURE", ["GASKET", "MOUNT"], "NO BOLTS · NO STRESS POINTS", y=300, size=118)
    sp = A["kb_gasket"]
    pose = dict(rx=34, ry=-8 + 8 * lb, rz=-3, s=1.0 + 0.06 * lb, cx=540, cy=980)
    put(c, GLOW_RED, 540, 1060, 0.5, 0, 0.35)
    put3d(c, sp, **pose)
    d = ImageDraw.Draw(c)
    for i, (px, py) in enumerate(GASKETS):
        x, y = proj_point(px, py, sp.width, sp.height, pose["rx"], pose["ry"], pose["rz"], pose["s"], pose["cx"],
                          pose["cy"])
        age = lb * 2 - 0.4 - i * 0.12
        if age > 0:
            r = 16 + 40 * ((age * 0.8) % 1)
            a = int(255 * (1 - (age * 0.8) % 1))
            d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), outline=dim(RED_HI, a), width=4)
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=rgba(WHITE))
    return {"zoom": 1 + 0.05 * lb / 2}


def sc_swap(c, lb, k, t):
    background(c, t, (540, 940), 0.4)
    title_block(c, lb * 2, "04 · HOT-SWAP", ["SWAP ANY", "SWITCH"], "3 & 5-PIN · NO SOLDERING", y=300, size=118)
    q = eo_expo(lb / 0.5)
    put3d(c, A["kb_swap"], 540 + 80 * (1 - q), 1010 - 18 * math.sin(lb * 2.5), rx=10, ry=-12 + 10 * lb, rz=-2,
          s=1.05, a=clamp(q * 1.4))
    return {}


def sc_pbt(c, lb, k, t):
    background(c, t, (540, 920), 0.35)
    title_block(c, lb, "05 · KEYCAPS", ["DOUBLESHOT", "PBT"], "LEGENDS THAT NEVER FADE", y=300, size=118)
    sp = A["keycap"]
    s = 1.42 + 0.08 * lb / 4
    q = eo_expo(lb / 0.45)
    swept = light_sweep(sp, clamp((lb - 0.5) / 1.2), 0.15, 0.7)
    cy = 960
    put(c, swept, 540, cy + 80 * (1 - q), s, 0, clamp(q * 1.4))
    # callouts: legend on the cap, wall thickness on the underside view
    lx, ly = 540 + (115 - sp.width / 2) * s, cy + (60 - sp.height / 2) * s
    callout(c, lx, ly, 330, 1185, "MOLDED-IN LEGEND", "never printed on top", (lb - 1.0) / 0.7)
    wx, wy = 540 + (300 - sp.width / 2) * s, cy + (150 - sp.height / 2) * s
    callout(c, wx, wy, 600, 760, "THICKER WALLS", "rounder, deeper tone", (lb - 1.6) / 0.7)
    return {}


def stat_card(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=(26, 26, 32, 235), outline=(255, 255, 255, 34), width=2)
    d.rounded_rectangle((0, 18, 8, h - 18), 4, fill=rgba(RED))
    return im


def sc_specs(c, lb, k, t):
    background(c, t, (540, 860), 0.35)
    title_block(c, lb, "06 · PERFORMANCE", ["TRI-MODE", "WIRELESS"], None, y=280, size=110)
    rows = [  # appear at, y, value-fn, unit, label
        (0.2, 715, lambda p: f"{int(4000 * p):,}".replace(",", ""), "mAh", "BATTERY"),
        (1.7, 925, lambda p: f"{int(1000 * p)}", "Hz", "POLLING RATE"),
        (3.2, 1135, None, "", "BT 5.0 · 2.4G · WIRED"),
    ]
    for at, y, fn, unit, lab in rows:
        if lb < at:
            continue
        q = eo_expo((lb - at) / 0.4)
        cw, chh = 900, 180
        card = stat_card(cw, chh)
        x = W / 2 + (1 - q) * 700
        comp(c, fade(card, clamp(q * 1.5)), x - cw / 2, y - chh / 2)
        if fn:
            p = eio(clamp((lb - at - 0.1) / 1.2))
            num = tsprite("dispx", 110, fn(p), rgba(WHITE))
            comp(c, fade(num, q), x - cw / 2 + 50, y - num.height / 2 - 6)
            un = tsprite("dispx", 52, unit, rgba(RED_HI))
            comp(c, fade(un, q), x - cw / 2 + 60 + num.width - 8, y - 10)
            lb_s = tsprite("inter", 26, lab, rgba(GREY), track=0.2)
            comp(c, fade(lb_s, q), x + cw / 2 - lb_s.width - 40, y - lb_s.height / 2)
            if unit == "mAh":  # battery icon filling
                d = ImageDraw.Draw(c)
                bx, by = x + cw / 2 - 150, y - 60
                d.rounded_rectangle((bx, by, bx + 100, by + 44), 8, outline=dim(WHITE, int(220 * q)), width=4)
                d.rectangle((bx + 101, by + 14, bx + 108, by + 30), fill=dim(WHITE, int(220 * q)))
                d.rectangle((bx + 8, by + 8, bx + 8 + 84 * p, by + 36), fill=dim(RED_HI, int(255 * q)))
        else:
            tx = tsprite("dispx", 56, lab, rgba(WHITE))
            comp(c, fade(tx, q), x - tx.width / 2, y - tx.height / 2 - 22)
            s2 = tsprite("interm", 26, "CONNECT UP TO 3 DEVICES", rgba(GREY), track=0.2)
            comp(c, fade(s2, q), x - s2.width / 2, y + 30)
    if lb >= 4.2:
        put(c, chip("75% LAYOUT", 24), 860, 1262, eo_back((lb - 4.2) / 0.3))
    return {}


def sc_display(c, lb, k, t):
    background(c, t, (540, 820), 0.4)
    if lb < 2:
        title_block(c, lb, "07 · DISPLAY", ["LED DISPLAY", "+ KNOB"], "OWN YOUR IDENTITY", y=300, size=112)
        sp = A["display"]
        z = 1.0 + 0.18 * eio(lb / 2)
        cw, ch = 1000, 640
        sc_ = cw / sp.width * z
        big = scaled(sp, sc_)
        fx, fy = 0.62, 0.45  # zoom toward the right-hand display
        x0 = int((big.width - cw) * fx)
        y0 = int((big.height - ch) * fy)
        card = big.crop((x0, y0, x0 + cw, y0 + ch))
        card.putalpha(round_mask(cw, ch, 34))
        q = eo_expo(lb / 0.4)
        put(c, card, W / 2, 930 + 100 * (1 - q), 1, 0, clamp(q * 1.4))
    else:
        l2 = lb - 2
        title_block(c, l2, "08 · RGB", ["LIGHT IT", "YOUR WAY"], "EVERY COLOR, SET HOW YOU WANT", y=300, size=118)
        fr = clip("rgb", 20 + l2 * BEAT * 30 * 1.4).convert("RGBA")
        fr.putalpha(RGB_MATTE)
        q = eo_expo(l2 / 0.4)
        put(c, GLOW_RED, 540, 1000, 0.6, 0, 0.3)
        put3d(c, fr, 540, 960, rx=18, ry=0, rz=0, s=0.86 * (0.9 + 0.1 * q), a=clamp(q * 1.5))
    return {}


def sc_gaming(c, lb, k, t):
    background(c, t, (540, 820), 0.45)
    title_block(c, lb, "09 · ESPORTS READY", ["BUILT FOR", "COMPETITIVE", "GAMING"], None, y=270, size=96)
    fr = clip("game", min(37, lb * BEAT * 30 * 0.5))
    cw = 1000
    chh = int(fr.height * cw / fr.width)
    card = fr.resize((cw, chh), Image.BILINEAR).convert("RGBA")
    # scanlines
    sl = Image.new("RGBA", card.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sl)
    for y in range(0, chh, 4):
        d.line((0, y, cw, y), fill=(0, 0, 0, 40))
    card.alpha_composite(sl)
    card.putalpha(round_mask(cw, chh, 24))
    q = eo_expo(lb / 0.35)
    cy = 900
    put(c, card, W / 2, cy, 0.9 + 0.1 * q, 0, clamp(q * 1.4))
    d = ImageDraw.Draw(c)
    x0, y0, x1, y1 = W / 2 - cw / 2 - 14, cy - chh / 2 - 14, W / 2 + cw / 2 + 14, cy + chh / 2 + 14
    L = 50
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=rgba(RED_HI), width=6)
        d.line((x, y, x, y + sy * L), fill=rgba(RED_HI), width=6)
    if int(t * 2) % 2 == 0:
        d.ellipse((x0 + 34, y0 + 34, x0 + 52, y0 + 52), fill=rgba(RED_HI))
    rec = tsprite("inter", 22, "LIVE · 1000Hz", rgba(WHITE), track=0.2)
    comp(c, rec, x0 + 62, y0 + 30)
    if lb >= 0.6:
        qq = eo_expo((lb - 0.6) / 0.4)
        lt = tsprite("dispx", 88, "LETHAL TAP", rgba(WHITE))
        put(c, lt, W / 2, 1180 + 30 * (1 - qq), 1, 0, qq)
        s2 = tsprite("inter", 26, "LAST-INPUT PRIORITY · COUNTER-STRAFE ON AUTO", rgba(RED_HI), track=0.12)
        put(c, s2, W / 2, 1255, min(1.0, 980 / s2.width), 0, clamp((lb - 0.9) / 0.3))
    return {}


def sc_reviews(c, lb, k, t):
    background(c, t, (540, 700), 0.4)
    q = eo_back(lb / 0.35)
    num = tsprite("dispx", 210, "4.68", rgba(WHITE))
    put(c, num, W / 2, 430, 0.6 + 0.4 * q, 0, clamp(lb / 0.15))
    nfill = clamp((lb - 0.5) / 1.6) * 5 * 0.936 if lb < 2.1 else 5 * 0.936
    stars(c, W / 2, 590, nfill)
    if lb >= 0.4:
        rv = tsprite("inter", 30, "FROM 325 REVIEWS", rgba(GREY), track=0.18)
        put(c, rv, W / 2, 670, 1, 0, clamp((lb - 0.4) / 0.3))
    xs = [190, 405, 675, 890]
    rots = [9, 3, -3, -9]
    for i in range(4):
        at = 1.0 + i * 0.35
        if lb < at:
            continue
        qq = eo_back((lb - at) / 0.4, 1.4)
        sp = A[f"review{i}"]
        put3d(c, sp, xs[i], 1030 + 160 * (1 - qq) + abs(i - 1.5) * 26, rx=0, ry=lerp(70, 0, qq), rz=rots[i],
              s=0.74, a=clamp(qq * 1.6))
    return {}


PERKS = ["18-MONTH WARRANTY", "FREE DELIVERY · INDIA", "7-DAY REPLACEMENT", "EMI FROM ₹227/MO"]


def perk_badge(text):
    ts = tsprite("inter", 26, text, rgba(WHITE), track=0.06)
    w, h = 470, 74
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 37, fill=(28, 28, 34, 240), outline=(255, 255, 255, 40), width=2)
    d.ellipse((16, 16, 58, 58), fill=rgba(RED))
    d.line((27, 37, 35, 46), fill=(255, 255, 255, 255), width=5)
    d.line((35, 46, 49, 29), fill=(255, 255, 255, 255), width=5)
    sc_ = min(1.0, (w - 90) / ts.width)
    ts2 = scaled(ts, sc_)
    im.alpha_composite(ts2, (72, (h - ts2.height) // 2))
    return im


def sc_price(c, lb, k, t):
    background(c, t, (540, 620), 0.55, 1.1)
    q = eo_expo(lb / 0.5)
    put(c, GLOW_RED, 540, 640, 0.7, 0, 0.5)
    hero = A["kb_hero"]
    put(c, hero, 540, 600 - 14 * math.sin(lb * 2), 0.98 * (0.9 + 0.1 * q), 0, clamp(q * 1.5))
    qp = eo_back((lb - 0.05) / 0.35, 2.4)
    if lb >= 0.05:
        pr = tsprite("anton", 230, "₹6,449", rgba(WHITE))
        put(c, glow_of(pr, RED, 30, 70, 0.9), W / 2, 1000, 1.4 - 0.4 * qp, 0, clamp(qp))
        put(c, pr, W / 2, 1000, 1.4 - 0.4 * qp, 0, clamp(qp * 1.4))
        d = ImageDraw.Draw(c)
        u = eo_expo((lb - 0.4) / 0.5)
        d.rectangle((W / 2 - 300 * u, 1150, W / 2 + 300 * u, 1158), fill=rgba(RED_HI))
    for i, txt in enumerate(PERKS):
        at = 1.0 + i
        if lb < at:
            continue
        qq = eo_back((lb - at) / 0.3)
        x = 290 if i % 2 == 0 else 790
        y = 1232 if i < 2 else 1312
        put(c, perk_badge(txt), x, y, 0.55 + 0.45 * qq)
    return {}


@lru_cache(maxsize=1)
def shop_button():
    w, h = 760, 150
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 75, fill=rgba(RED))
    ts = tsprite("dispx", 72, "SHOP NOW", rgba(WHITE), track=0.04)
    im.alpha_composite(ts, ((w - ts.width) // 2 - 30, (h - ts.height) // 2 + 2))
    ax = (w + ts.width) // 2 + 4
    d.line((ax, h / 2, ax + 52, h / 2), fill=(255, 255, 255, 255), width=10)
    d.polygon([(ax + 62, h / 2), (ax + 38, h / 2 - 22), (ax + 38, h / 2 + 22)], fill=(255, 255, 255, 255))
    return im


def sc_cta(c, lb, k, t):
    background(c, t, (540, 900), 0.5)
    title_block(c, lb, "AVAILABLE NOW", ["GRAB", "YOURS"], None, y=280, size=130)
    put(c, GLOW_RED, 540, 900, 0.5, 0, 0.35)
    put3d(c, A["kb_tilt"], 540, 850 - 14 * math.sin(lb * 2), rx=10, ry=-12 + 8 * lb, rz=0, s=0.6)
    btn = shop_button()
    tap = 1.5
    press = 1 - 0.06 * math.exp(-max(0.0, (lb - tap) * BEAT) / 0.08) * (lb >= tap)
    pulse = 1 + 0.03 * math.sin(lb * math.pi * 2)
    put(c, glow_of(btn, RED, 34, 80, 0.9), W / 2, 1150, pulse, 0, 0.8)
    put(c, btn, W / 2, 1150, press * pulse * eo_back(lb / 0.4))
    if lb >= tap:
        age = (lb - tap) * BEAT
        r = 20 + 380 * eo_expo(age / 0.6)
        al = int(200 * clamp(1 - age / 0.6))
        layer_draw(c, lambda d: d.ellipse((W / 2 + 120 - r, 1150 - r, W / 2 + 120 + r, 1150 + r),
                                          outline=(255, 255, 255, al), width=6))
    if lb < tap + 0.3:  # finger/tap target
        qq = clamp((lb - 0.6) / 0.6)
        fx, fy = lerp(800, W / 2 + 120, eio(qq)), lerp(1330, 1165, eio(qq))
        layer_draw(c, lambda d: d.ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150),
                                          outline=(255, 255, 255, 255), width=4))
    url = tsprite("interm", 34, "lethalblack.com", rgba(GREY), track=0.06)
    put(c, url, W / 2, 1272, 1, 0, clamp((lb - 0.5) / 0.3))
    return {}


def sc_end(c, lb, k, t):
    background(c, t, (540, 900), 0.45 + 0.25 * math.exp(-lb / 0.6), 1.0, 0.5)
    q = eo_expo(lb / 0.5)
    lg = scaled(A["logo"], 640 / A["logo"].width)
    put(c, glow_of(lg, RED, 30, 70, 0.8), W / 2, 760, 1.2 - 0.2 * q, 0, 0.7 * q)
    put(c, light_sweep(lg, clamp((lb - 0.5) / 1.4)), W / 2, 760, 1.2 - 0.2 * q, 0, clamp(q * 1.4))
    if lb >= 0.4:
        qq = eo_expo((lb - 0.4) / 0.5)
        hv = scaled(A["havoc"], 620 / A["havoc"].width)
        put(c, hv, W / 2, 1010 + 40 * (1 - qq), 1, 0, qq)
        sub = tsprite("interm", 26, "75% WIRELESS MECHANICAL KEYBOARD", rgba(GREY), track=0.25)
        put(c, sub, W / 2, 1100, 1, 0, clamp((lb - 0.8) / 0.3))
        d = ImageDraw.Draw(c)
        u = eo_expo((lb - 0.7) / 0.6)
        d.rectangle((W / 2 - 160 * u, 1150, W / 2 + 160 * u, 1155), fill=rgba(RED))
    return {}


SCENES = [
    (0, 6, sc_hook), (6, 10, sc_reveal), (10, 14, sc_venom), (14, 18, sc_layers), (18, 20, sc_gasket),
    (20, 22, sc_swap), (22, 26, sc_pbt), (26, 32, sc_specs), (32, 36, sc_display), (36, 42, sc_gaming),
    (42, 46, sc_reviews), (46, 52, sc_price), (52, 56, sc_cta), (56, 99, sc_end),
]

# ---------------------------------------------------------------- post FX


def affine(arr, z, dx, dy, rot, focus=(W / 2, H / 2)):
    if abs(z - 1) < 1e-4 and abs(dx) < 0.5 and abs(dy) < 0.5 and abs(rot) < 1e-4:
        return arr
    fx, fy = focus
    th = math.radians(rot)
    cs, sn = math.cos(th), math.sin(th)
    a, b, d, e = cs / z, sn / z, -sn / z, cs / z
    cx, cy = fx + dx, fy + dy
    im = Image.fromarray(arr).transform((W, H), Image.AFFINE,
                                        (a, b, fx - (a * cx + b * cy), d, e, fy - (d * cx + e * cy)), Image.BILINEAR)
    return np.asarray(im)


def zoom_blur(arr, amount, center=(W / 2, H / 2), n=9):
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


def rgb_split(arr, d):
    d = int(d)
    if d == 0:
        return arr
    out = arr.copy()
    out[..., 0] = np.roll(arr[..., 0], d, axis=1)
    out[..., 2] = np.roll(arr[..., 2], -d, axis=1)
    return out


def block_glitch(arr, rng, p):
    out = arr.copy()
    for _ in range(int(160 * p)):
        bw, bh = int(rng.choice([40, 80, 160])), int(rng.choice([16, 32, 64]))
        x, y = int(rng.integers(0, W - bw)), int(rng.integers(0, H - bh))
        sx = int(np.clip(x + rng.normal(0, 120), 0, W - bw))
        sy = int(np.clip(y + rng.normal(0, 40), 0, H - bh))
        blk = arr[sy:sy + bh, sx:sx + bw]
        r = rng.random()
        if r < 0.25:
            blk = (blk * 0.35 + np.array(RED) * 0.65).astype(np.uint8)
        elif r < 0.35:
            blk = blk[..., ::-1]
        out[y:y + bh, x:x + bw] = blk
    return out


def scene_at(k):
    for s, e, fn in SCENES:
        if s <= k < e:
            return s, e, fn
    return SCENES[-1]


def render(fi):
    t = fi / FPS + 0.015
    k = t / BEAT
    rng = np.random.default_rng(fi * 7919 + 5)
    s, e, fn = scene_at(k)
    c = Image.new("RGBA", (W, H), rgba(INK))
    info = fn(c, k - s, k, t) or {}
    frame_detail(c, k)
    arr = np.asarray(c.convert("RGB"))

    z = info.get("zoom", 1.0)
    dx = dy = rot = 0.0
    flash = 0.0
    rgb = 0.0
    for hk in IMPACTS:
        dt = t - tb(hk)
        if 0 <= dt < 0.6:
            z *= 1 + 0.07 * math.exp(-dt / 0.12)
            amp = 26 * math.exp(-dt / 0.1)
            dx += rng.normal(0, amp)
            dy += rng.normal(0, amp)
            rot += rng.normal(0, amp * 0.02)
            flash = max(flash, 0.75 * math.exp(-dt / 0.05))
            rgb = max(rgb, 14 * math.exp(-dt / 0.08))
    for hb in HOOK_KEYS:
        dt = t - tb(hb) - 0.02
        if 0 <= dt < 0.25:
            z *= 1 + (0.035 if hb in (0, 2, 4) else 0.015) * math.exp(-dt / 0.07)
            dx += rng.normal(0, 5 * math.exp(-dt / 0.06))
    if k >= 6:
        z *= 1 + 0.01 * math.exp(-((k % 1) * BEAT) / 0.08)
    zoom_extra = 1 + (abs(dx) + abs(dy)) / W * 2.2
    arr = affine(arr, z * zoom_extra, dx, dy, rot)

    zb = info.get("zb", 0.0)
    for cb in CUTS + [6]:
        dt = t - tb(cb)
        if -0.11 <= dt < 0.11:
            zb = max(zb, 0.26 * (1 - abs(dt) / 0.11) ** 1.4)
            rgb = max(rgb, 8 * (1 - abs(dt) / 0.11))
    arr = zoom_blur(arr, zb)
    for gb in (36, 52):
        dt = t - tb(gb)
        if -0.08 <= dt < 0.1:
            arr = block_glitch(arr, rng, 1 - abs(dt) / 0.1)
            rgb = max(rgb, 18)
    arr = rgb_split(arr, rgb)
    if flash > 0.01:
        arr = (arr.astype(np.float32) + (255 - arr.astype(np.float32)) * flash).astype(np.uint8)

    # captions (stable, after camera moves)
    hc = Image.fromarray(arr).convert("RGBA")
    captions(hc, t)
    arr = np.asarray(hc.convert("RGB"))
    if t > DUR - 0.35:
        arr = (arr.astype(np.float32) * clamp((DUR - t) / 0.35)).astype(np.uint8)
    g = GRAIN[fi % len(GRAIN)]
    out = arr.astype(np.float32) * VIG + g[..., None] * 4.5
    return np.clip(out, 0, 255).astype(np.uint8).tobytes()


def main():
    out = sys.argv[1]
    frames = sys.argv[2] if len(sys.argv) > 2 else None
    if frames:
        os.makedirs(out, exist_ok=True)
        for fi in [int(x) for x in frames.split(",")]:
            Image.frombytes("RGB", (W, H), render(fi)).save(f"{out}/f{fi:04d}.jpg", quality=90)
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(int(os.environ.get("AD_PROCS", "4"))) as pool:
        for i, buf in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(buf)
            if i % 75 == 0:
                print(f"frame {i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
