"""ICEMAN // JANICE STFU — 25s 16:9 poster-style kinetic edit.

Every frame is a pure function of its time, so frames render in parallel and
pipe straight into ffmpeg. Timing is expressed in beats of the song
(125.82 BPM), so every cut, slam and flash lands on the music.
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

W, H, FPS, DUR = 1920, 1080, 30, 25.0
NF = int(DUR * FPS)
BEAT = 3.8151 / 8  # seconds per beat (125.82 BPM)
LEAD = 0.02  # pictures lead the audio by a hair so hits land on the frame the 808 starts

INK = (10, 11, 15)
PAPER = (236, 238, 241)
ICE = (38, 104, 255)
DEEP = (9, 26, 78)
FROST = (178, 226, 255)
GREY = (128, 132, 140)

HITS = [8, 11, 16, 19, 24, 27, 32, 35, 40, 43, 48, 51]
BARS = {8, 16, 24, 32, 40, 48}
BUILD = [4, 5, 6, 7]

# ---------------------------------------------------------------- utilities


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


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


FONT_FILES = {
    "anton": f"{FONTS}/Anton-Regular.ttf",
    "wide": f"{FONTS}/Unbounded%5Bwght%5D.ttf",
    "inter": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "interm": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
}


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
    sx1, sy1 = min(sp.width, W - x), min(sp.height, H - y)
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
    c.paste(rgba(col), (0, 0, W, H))


def draw_word(c, key, size, word, x, base, fill_col, *, track=0.0, appear=None, lb=0.0,
              stroke=0, slam=0.3, grey_flash=True, align="left", tilt_scale=None):
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
        if grey_flash and age < 0.12 and appear is not None:
            col = GREY if not stroke else fill_col
        sp, dx, dy = glyph(key, size, ch, rgba(col), stroke)
        s = 1 + slam * (1 - eo_expo(age / 0.3)) if appear is not None else 1.0
        gx, gy = x + xs[i] + dx, base + dy
        if s != 1.0:
            sp2 = scaled(sp, s)
            gx -= (sp2.width - sp.width) / 2
            gy -= (sp2.height - sp.height) / 2
            sp = sp2
        comp(c, sp, gx, gy)
    return total


def word_sprite(key, size, word, col, track=0.0, stroke=0, pad=10):
    xs, total = layout(key, size, word, track)
    f = F(key, size)
    asc = cap(key, size)
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
    bw_, bh = ws.width + 2 * px, ch + 2 * py
    im = Image.new("RGBA", (bw_, bh), rgba(box_col))
    # glyph sprite origin: top of ws corresponds to t (relative to baseline); cap top is -ch
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


# ---------------------------------------------------------------- assets

def load(name):
    return Image.open(f"{ASSETS}/{name}.png").convert("RGBA")


A = {n: load(n) for n in [
    "glove_bw", "glove_ht", "grin_bw", "grin_ht", "stage_bw", "stage_ht", "coat_bw", "coat_ht",
    "seat_bw", "seat_ht", "grin_plate", "stage_plate", "coat_plate", "glove_plate", "logo"]}

# swirl texture (white Archimedean spirals) for the swirl scene
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

# radial end-card background
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.75)) ** 2)
_t = np.clip(_r, 0, 1)[..., None]
END_BG = Image.fromarray((np.array(DEEP) * (1 - _t) + np.array(INK) * _t).astype(np.uint8), "RGB").convert("RGBA")
VIG = (1 - 0.32 * np.clip(_r - 0.45, 0, 1) ** 1.5)[..., None].astype(np.float32)
del _yy, _xx, _r, _t

LOGO = scaled(A["logo"], 1320 / A["logo"].width)
_glow = Image.new("RGBA", (LOGO.width + 200, LOGO.height + 200), (0, 0, 0, 0))
_tint = Image.new("RGBA", LOGO.size, rgba(ICE))
_tint.putalpha(LOGO.getchannel("A"))
_glow.alpha_composite(_tint, (100, 100))
LOGO_GLOW = _glow.filter(ImageFilter.GaussianBlur(28))
del _glow, _tint

_rng = np.random.default_rng(7)
SNOW = [(float(_rng.uniform(0, W)), float(_rng.uniform(0, H)), float(_rng.uniform(1.5, 5.5)),
         float(_rng.uniform(25, 90)), float(_rng.uniform(0, 6.28))) for _ in range(150)]
# coarse film grain (half-res, upsampled) -> filmic and encoder friendly
GRAIN = []
for i in range(6):
    g = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR))
    GRAIN.append(g)

# ---------------------------------------------------------------- HUD

HUD_ITEMS = [
    ("tl", "ARTIST", "DRAKE"), ("tc", "ICEMAN", "TRACK 04 / 18"), ("tr", "OVO", "2026"),
    ("bl", "NOW PLAYING", "JANICE STFU"), ("bc", "126 BPM", "16:9 CUT"), ("br", "TC", None),
]


@lru_cache(maxsize=64)
def hud_text(s, size, key, col):
    f = F(key, size)
    l, t, r, b = f.getbbox(s)
    # manual tracking
    xs, total = layout(key, size, s, 0.12)
    im = Image.new("RGBA", (int(total + 6), b + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(s):
        d.text((xs[i] + 2, 0), ch, font=f, fill=col)
    return im


def hud(c, t, dark=False, a=1.0):
    main = rgba(INK if dark else PAPER, int(235 * a))
    sub = rgba(INK if dark else PAPER, int(140 * a))
    fr = int(round(t * FPS))
    tc = f"00:{int(t):02d}:{fr % FPS:02d}"
    for pos, l1, l2 in HUD_ITEMS:
        if l2 is None:
            l2 = tc
        s1 = hud_text(l1, 15, "interm", sub)
        s2 = hud_text(l2, 19, "inter", main)
        if pos[0] == "t":
            y = 40
        else:
            y = H - 40 - s1.height - s2.height - 2
        for k, sp in enumerate((s1, s2)):
            if pos[1] == "l":
                x = 56
            elif pos[1] == "r":
                x = W - 56 - sp.width
            else:
                x = W / 2 - sp.width / 2
            comp(c, sp, x, y + (0 if k == 0 else s1.height + 2))
    # little ice dot that blinks on the beat (record light)
    on = (t / BEAT) % 1 < 0.5
    if on:
        ImageDraw.Draw(c).ellipse((W - 56 - 150, H - 40 - 28, W - 56 - 138, H - 40 - 16), fill=rgba(ICE))


# ---------------------------------------------------------------- scenes
# each scene: fn(c, lb, d, t) -> dict(hud='light'|'dark', zoom=, focus=, invert=, rgb=)


def sc_intro(c, lb, d, t):
    fill(c, INK)
    PW = PH = 700
    cx, cy = W / 2 - 60, H / 2 + 10
    p = eo_expo(lb / 0.5)
    panel = Image.new("RGBA", (PW, PH), rgba(DEEP))
    pd = ImageDraw.Draw(panel)
    rays(pd, PW / 2, PH * 0.62, 18, lb * 0.12, rgba(ICE, 150), r=1200, width=0.45)
    gl = A["glove_ht"]
    put_bottom(panel, gl, PW / 2 + 10, PH + 90 - 30 * lb / 4, 880 * (1 + 0.04 * lb / 4))
    # dark-to-bright reveal of the photo
    if lb < 0.6:
        dk = Image.new("RGBA", (PW, PH), rgba(INK, int(255 * (1 - lb / 0.6))))
        panel.alpha_composite(dk)
    panel.putalpha(round_mask(PW, PH, 64))
    s = 0.9 + 0.1 * p + 0.03 * lb / 4
    put(c, panel, cx, cy, s, 0, clamp(lb / 0.25))
    x0, y0 = cx - PW * s / 2, cy - PH * s / 2
    x1, y1 = cx + PW * s / 2, cy + PH * s / 2
    # name tag
    if lb >= 0.5:
        tag = box_text("anton", 96, "DRAKE", PAPER, ICE)
        q = eo_back((lb - 0.5) / 0.35)
        put(c, tag, x0 + 40, y0 + 90, 0.6 + 0.4 * q, 6)
    # JANICE typed on a growing chip
    word = "JANICE"
    n = sum(1 for i in range(len(word)) if lb >= 1.0 + i * 0.42)
    if n:
        chip = box_text("anton", 190, word[:n], PAPER, ICE)
        put(c, chip, x1 - 80 + chip.width / 2 - 150, y1 - 90, 1.0, -4)
    # small label
    lab = hud_text("TRACK 04  —  ICEMAN", 20, "inter", rgba(PAPER, 220))
    if lb > 0.8:
        comp(c, lab, x0 + 30, y1 + 24)
    return {"hud": "light"}


def sc_build(c, lb, d, t):
    i = int(lb)
    if lb >= 3.55:  # drop gap: CRT switch-off line
        fill(c, (0, 0, 0))
        q = clamp((lb - 3.55) / 0.35)
        w = int(W * (1 - q) ** 2)
        if w > 4:
            ImageDraw.Draw(c).rectangle((W / 2 - w / 2, H / 2 - 3, W / 2 + w / 2, H / 2 + 3), fill=rgba(PAPER))
        return {"hud": None}
    fill(c, [INK, DEEP, INK, DEEP][i])
    size = 1060
    word = "STFU"
    xs, total = layout("anton", size, word, 0.02)
    base = H / 2 + cap("anton", size) / 2
    for j, ch in enumerate(word):
        if lb < j:
            continue
        col = ICE if j == i else PAPER
        sp, dx, dy = glyph("anton", size, ch, rgba(col))
        age = lb - j
        s = 1 + 0.25 * (1 - eo_expo(age / 0.35))
        sp2 = scaled(sp, s)
        gx = W / 2 - total / 2 + xs[j] + dx - (sp2.width - sp.width) / 2
        gy = base + dy - (sp2.height - sp.height) / 2
        comp(c, sp2, gx, gy)
    gl = A["glove_bw"]
    hh = 900 * (1 + 0.1 * i + 0.05 * (lb - i))
    put_bottom(c, gl, W / 2 + 20, H + 160, hh, rot=[3, -3, 4, -4][i])
    return {"hud": "light", "zoom": 1 + 0.06 * eio(clamp((lb - 2.8) / 0.75))}


def sc_ice(c, lb, d, t):
    fill(c, DEEP)
    dr = ImageDraw.Draw(c)
    for k in range(5):
        dr.rectangle((70, 640 + k * 38, 300 - k * 30, 660 + k * 38), fill=rgba(ICE))
    size = 1420
    word = "ICE"
    xs, total = layout("anton", size, word, 0.03)
    base = H / 2 + cap("anton", size) / 2 + 30
    draw_word(c, "anton", size, word, W / 2, base, PAPER, track=0.03, appear=[0, 1, 2], lb=lb,
              align="center", slam=0.25)
    put_bottom(c, A["stage_ht"], W / 2 + 40, H + 140 - 20 * lb / 3, 1250 * (1 + 0.035 * lb / 3))
    if lb >= 1.5:
        q = eo_expo((lb - 1.5) / 0.35)
        b1 = box_text("anton", 120, "ICEMAN", PAPER, ICE)
        put(c, b1, W - 330 + (1 - q) * 500, 790, 1, -3)
    if lb >= 2.0:
        q = eo_expo((lb - 2.0) / 0.35)
        b2 = box_text("anton", 92, "ERA", INK, PAPER)
        put(c, b2, W - 250 + (1 - q) * 500, 925, 1, -3)
    return {"hud": "light"}


def sc_badge(c, lb, d, t):
    fill(c, INK)
    dr = ImageDraw.Draw(c)
    dr.polygon([(860, 0), (1600, 0), (1500, H), (760, H)], fill=rgba(ICE))
    # partial second photo at the left edge (collage feel)
    plate = cover(A["grin_plate"], 330, H, 0.15, 0.3, 1.25)
    comp(c, fade(plate, 0.55), 0, 0)
    put_bottom(c, A["grin_ht"], 1190 + 25 * lb / 2, H + 20, 1010)
    q = eo_back(lb / 0.4)
    bx, by, R = 600, 560, 270 * q
    if R > 2:
        burst(dr, bx, by, R, R * 0.85, 30, lb * 0.25, rgba(ICE))
        if lb > 0.2:
            app1 = [0.25, 0.38, 0.51]
            app2 = [0.75, 0.88, 1.01]
            draw_word(c, "anton", 165, "SIX", bx, by - 8, PAPER, appear=app1, lb=lb, align="center")
            draw_word(c, "anton", 165, "GOD", bx, by + cap("anton", 165) + 14, PAPER, appear=app2, lb=lb,
                      align="center")
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
        (45, ICE, "O", PAPER, "stage_ht", 960, 0, -1.5, 0.5),
        (662, PAPER, "V", ICE, "grin_ht", 900, 0, 1.2, 0.62),
        (1279, DEEP, "O", PAPER, "coat_ht", 930, 10, -1.0, 0.5),
    ]
    zoom = 1 + 0.05 * eio(clamp((lb - 2.3) / 0.7))
    for i, (x, bg, L, lc, subj, sh, stroke, rot, fx) in enumerate(specs):
        if lb < i:
            continue
        q = eo_expo((lb - i) / 0.38)
        pw, ph = 596, 1000
        p = panel_img(pw, ph, bg, L, lc, subj, sh, lb - i, stroke, fx)
        p.putalpha(round_mask(pw, ph, 18))
        off = (1 - q) * (H if i % 2 == 0 else -H)
        put(c, p, x + pw / 2, H / 2 + off, 1.0, rot * q)
    return {"hud": "light", "zoom": zoom}


def sc_stack(c, lb, d, t):
    fill(c, INK)
    plate = cover(A["coat_plate"], W, H, 0.5, 0.5, 1.05 + 0.02 * lb / 3)
    comp(c, fade(plate, 0.22), 0, 0)
    put_bottom(c, A["coat_ht"], 1380, H + 20, 1040 * (1 + 0.03 * lb / 3))
    lines = [("TOO", PAPER, 210, 0, 0.0), ("COLD", ICE, 330, 0, 0.75), ("FOR", PAPER, 210, 0, 1.5),
             ("YOU", PAPER, 230, 6, 2.25)]
    gap = 34
    total_h = sum(cap("anton", s) for _, _, s, _, _ in lines) + gap * (len(lines) - 1)
    y = (H - total_h) / 2
    for word, col, size, stroke, at in lines:
        ch = cap("anton", size)
        y += ch
        if lb >= at:
            app = [at + k * 0.09 for k in range(len(word))]
            if stroke:
                xs, _ = layout("anton", size, word)
                for k, L in enumerate(word):
                    if lb >= app[k]:
                        sp, dx, dy = glyph("anton", size, L, rgba(col), stroke)
                        comp(c, sp, 150 + 12 * lb + xs[k] + dx, y + dy)
            else:
                draw_word(c, "anton", size, word, 150 + 12 * lb, y, col, appear=app, lb=lb)
        y += gap
    return {"hud": "light"}


def bezier(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        u = i / n
        a = (1 - u) ** 3
        b = 3 * (1 - u) ** 2 * u
        cc = 3 * (1 - u) * u ** 2
        e = u ** 3
        pts.append((a * p0[0] + b * p1[0] + cc * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + cc * p2[1] + e * p3[1]))
    return pts


SWOOSH = bezier((-80, 980), (500, -150), (1250, 1250), (2000, 260), 260)


def sc_wide(c, lb, d, t):
    fill(c, INK)
    q1 = eo_expo(lb / 0.35)
    drift = -30 * lb
    xs, tot = layout("wide", 300, "SUB")
    draw_word(c, "wide", 300, "SUB", 110 + (1 - q1) * W + drift, 430, ICE)
    if lb >= 0.9:
        q2 = eo_expo((lb - 0.9) / 0.35)
        sp = word_sprite("wide", 300, "ZERO", ICE, stroke=7)
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
    return word_sprite("anton", 860, "STFU", PAPER, track=0.02, pad=20)


def sc_tilt(c, lb, d, t):
    fill(c, INK)
    pan = Image.new("RGBA", (2600, 760), rgba(ICE))
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
        b1 = box_text("anton", 170, "JANICE", PAPER, ICE)
        put(c, b1, 470, 420, eo_back((lb - 0.15) / 0.3), -5)
    if lb >= 0.65:
        b2 = box_text("anton", 170, "STFU", INK, PAPER)
        put(c, b2, 560, 640, eo_back((lb - 0.65) / 0.3), -5)
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
    if bg is None:  # full-bleed plate
        comp(c, cover(A[subj], W, H, 0.5, 0.25, 1.1 * z), 0, 0)
        b = box_text("anton", 210, word, PAPER, ICE)
        put(c, b, 520, H - 300, 1 + 0.15 * (1 - eo_expo(ll * 3)), -4)
        return {"hud": "light", "cut": st}
    fill(c, bg)
    size = 900
    xs, tot = layout("anton", size, word, 0.02)
    if tot > W - 160:
        size = int(size * (W - 160) / tot)
    base = H / 2 + cap("anton", size) / 2
    if stroke:
        xs, tot = layout("anton", size, word, 0.02)
        for k, L in enumerate(word):
            sp, dx, dy = glyph("anton", size, L, rgba(wc), stroke)
            sp = scaled(sp, z)
            comp(c, sp, W / 2 - tot * z / 2 + xs[k] * z + dx, base + dy * z)
    else:
        sp = word_sprite("anton", size, word, wc, 0.02)
        put(c, sp, W / 2, H / 2 + 10, z)
    hh = (1000 if subj != "seat_bw" else 760) * (1 + 0.05 * ll)
    put_bottom(c, A[subj], W * fx, H + (120 if subj in ("stage_ht", "glove_ht") else 10), hh)
    return {"hud": "dark" if bg == PAPER else "light", "cut": st}


def sc_white(c, lb, d, t):
    fill(c, PAPER)
    dr = ImageDraw.Draw(c)
    rays(dr, W * 0.86, -80, 26, 1.75 + 0.05 * lb, rgba(ICE), r=2600, width=0.42)
    dr.rectangle((0, 0, W, H), outline=None)
    size = 600
    word = "DRAKE"
    xs, tot = layout("anton", size, word, 0.02)
    base = 610
    app = [0.0, 0.18, 0.36, 0.54, 0.72]
    draw_word(c, "anton", size, word, W / 2, base, INK, track=0.02, appear=app, lb=lb, align="center")
    if lb >= 0.9:
        ws = word_sprite("anton", size, word, INK, 0.02, pad=0)
        ref = ws.transpose(Image.FLIP_TOP_BOTTOM).resize((ws.width, int(ws.height * 0.62)), Image.BILINEAR)
        grad = np.linspace(0.55, 0.0, ref.height)[:, None] * np.ones((1, ref.width))
        al = (np.asarray(ref.getchannel("A")).astype(np.float32) * grad * clamp((lb - 0.9) / 0.3)).astype(np.uint8)
        ref.putalpha(Image.fromarray(al, "L"))
        comp(c, ref, W / 2 - ws.width / 2, base + 16)
    put_bottom(c, A["stage_ht"], W / 2 + 10, H + 130, 1120 * (1 + 0.03 * lb / 3))
    # ink poster frame with rounded inner window
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
    for k, (wd, tc_, bc, size, y) in enumerate(rows):
        if lb >= k:
            q = eo_expo((lb - k) / 0.32)
            b = box_text("wide", size, wd, tc_, bc)
            put(c, b, 120 + b.width / 2 - (1 - q) * 900, y, 1 + 0.12 * (1 - q), -5)
    z, inv, rgb = 1.0, False, 0
    if lb >= 3:
        z = 1 + 0.2 * eo_expo((lb - 3) / 0.5)
    if lb >= 4:
        inv = (lb - 4) % 0.5 < 0.18
        rgb = 10 if inv else 4
    return {"hud": "light", "zoom": z, "focus": (W - 560, 420), "invert": inv, "rgb": rgb}


def sc_end(c, lb, d, t):
    c.paste(END_BG, (0, 0))
    dr = ImageDraw.Draw(c)
    for (x, y, r, sp, ph) in SNOW:
        yy = (y + sp * t * 1.0) % H
        xx = x + 18 * math.sin(t * 0.9 + ph)
        dr.ellipse((xx - r, yy - r, xx + r, yy + r), fill=rgba(FROST, 120))
    q = eo_expo(lb / 0.35)
    s = 1.25 - 0.25 * q + 0.02 * lb / 4
    hit = lb >= 3
    if hit:
        g = 1 - clamp((lb - 3) / 1.2) * 0.5
        put(c, LOGO_GLOW, W / 2, H / 2 - 40, s, 0, g)
    elif lb > 0.2:
        put(c, LOGO_GLOW, W / 2, H / 2 - 40, s, 0, 0.45)
    put(c, LOGO, W / 2, H / 2 - 40, s, 0, clamp(lb / 0.1))
    if lb >= 0.6:
        a = clamp((lb - 0.6) / 0.4)
        sub = hud_text("DRAKE   —   JANICE STFU", 34, "inter", rgba(PAPER))
        put(c, sub, W / 2, H / 2 + 150 + 20 * (1 - a), 1, 0, a)
    if lb >= 1.1:
        a = clamp((lb - 1.1) / 0.4)
        sub2 = hud_text("ICEMAN  ·  TRACK 04  ·  2026", 20, "interm", rgba(FROST))
        put(c, sub2, W / 2, H / 2 + 205, 1, 0, a)
        dr.rectangle((W / 2 - 60 * a, H / 2 + 240, W / 2 + 60 * a, H / 2 + 243), fill=rgba(ICE))
    return {"hud": "light", "zoom": 1.0}


SCENES = [
    (0, 4, sc_intro), (4, 8, sc_build), (8, 11, sc_ice), (11, 13, sc_badge), (13, 16, sc_collage),
    (16, 19, sc_stack), (19, 21.5, sc_wide), (21.5, 24, sc_seats), (24, 25.5, sc_tilt),
    (25.5, 27, sc_tiltcoat), (27, 32, sc_swirl), (32, 40, sc_rapid), (40, 43, sc_white),
    (43, 48, sc_words), (48, 99, sc_end),
]
TRANS = {4: "flash", 11: "whip", 13: "slice", 16: "flash", 19: "whip", 21.5: "slice", 24: "flash",
         25.5: "whip", 27: "flash", 32: "slice", 40: "invert", 43: "whip", 48: "flash"}

# ---------------------------------------------------------------- post FX


def affine(arr, z, dx, dy, rot, focus):
    if abs(z - 1) < 1e-4 and abs(dx) < 0.5 and abs(dy) < 0.5 and abs(rot) < 1e-4:
        return arr
    fx, fy = focus
    th = math.radians(rot)
    cs, sn = math.cos(th), math.sin(th)
    a, b, d, e = cs / z, sn / z, -sn / z, cs / z
    # p_in = M (p_out - f - T) + f
    cx, cy = fx + dx, fy + dy
    c0 = fx - (a * cx + b * cy)
    f0 = fy - (d * cx + e * cy)
    im = Image.fromarray(arr).transform((W, H), Image.AFFINE, (a, b, c0, d, e, f0), Image.BILINEAR)
    return np.asarray(im)


def smear(arr, strength, shift):
    k = max(1, int(strength))
    im = Image.fromarray(arr)
    im = im.resize((max(16, W // k), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    out = np.asarray(im)
    if shift:
        out = np.roll(out, int(shift), axis=1)
    return out


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


def scene_at(k):
    for s, e, fn in SCENES:
        if s <= k < e:
            return s, e, fn
    return SCENES[-1]


def render(fi):
    t = fi / FPS + LEAD
    k = t / BEAT
    rng = np.random.default_rng(fi * 7919 + 13)
    s, e, fn = scene_at(k)
    c = Image.new("RGBA", (W, H), rgba(INK))
    info = fn(c, k - s, e - s, t) or {}
    arr = np.asarray(c.convert("RGB"))

    # ---- camera: hit punches, beat pulse, shake
    z = info.get("zoom", 1.0)
    dx = dy = rot = 0.0
    flash = 0.0
    rgb = info.get("rgb", 0)
    for hk in HITS:
        dt = t - hk * BEAT
        if 0 <= dt < 0.6:
            big = hk in BARS
            z *= 1 + (0.075 if big else 0.05) * math.exp(-dt / 0.12)
            amp = (30 if big else 18) * math.exp(-dt / 0.1)
            dx += rng.normal(0, amp)
            dy += rng.normal(0, amp * 0.7)
            rot += rng.normal(0, amp * 0.02)
            flash = max(flash, (0.9 if big else 0.55) * math.exp(-dt / 0.045))
            rgb = max(rgb, 16 * math.exp(-dt / 0.07))
    for bk in BUILD:
        dt = t - bk * BEAT
        if 0 <= dt < 0.3:
            flash = max(flash, 0.35 * math.exp(-dt / 0.04))
            z *= 1 + 0.03 * math.exp(-dt / 0.1)
            dx += rng.normal(0, 8 * math.exp(-dt / 0.1))
    if k >= 8:
        dtb = (k % 1) * BEAT
        z *= 1 + 0.012 * math.exp(-dtb / 0.08)
    if s == 32 and "cut" in info:  # rapid montage: tiny flash + jolt on each cut
        dt = t - (32 + info["cut"]) * BEAT
        if 0 <= dt < 0.2 and info["cut"] not in (0.0, 3.0):
            flash = max(flash, 0.3 * math.exp(-dt / 0.04))
            dx += rng.normal(0, 12 * math.exp(-dt / 0.08))
    zoom_extra = 1 + (abs(dx) + abs(dy)) / W * 2.2
    arr = affine(arr, z * zoom_extra, dx, dy, rot, info.get("focus", (W / 2, H / 2)))

    # ---- transitions
    for tk, kind in TRANS.items():
        dt = t - tk * BEAT
        if kind == "whip" and -0.14 <= dt < 0.12:
            if dt < 0:
                p = 1 + dt / 0.14
                arr = smear(arr, 4 + 70 * p ** 2, -260 * p ** 2)
            else:
                p = 1 - dt / 0.12
                arr = smear(arr, 4 + 70 * p ** 2, 260 * p ** 2)
        elif kind == "slice" and -0.1 <= dt < 0.08:
            p = 1 - abs(dt) / 0.1
            arr = slice_glitch(arr, rng, 160 * p)
            rgb = max(rgb, 10 * p)
        elif kind == "invert" and 0 <= dt < 0.07:
            arr = negative(arr)
    if info.get("invert"):
        arr = negative(arr)
    # end glitch-out
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
        hud(hc, t, dark=info["hud"] == "dark" and not info.get("invert"), a=clamp(t / 0.4))
        arr = np.asarray(hc.convert("RGB"))

    # ---- grain + vignette
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
            if i % 75 == 0:
                print(f"frame {i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
