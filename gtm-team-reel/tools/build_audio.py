"""Build the music bed and the pre-mixed SFX track for index.html.

SFX cues are read from the composition itself (every data-sfx attribute plus the
WIPES array), so sound always lands on the frame it belongs to.

    python3 tools/build_audio.py
"""
import re
import wave
from pathlib import Path

import numpy as np

SR = 44100
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "audio"
DUR = 46.5
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack, release):
    a = min(n, max(1, int(attack * SR)))
    r = min(n, max(1, int(release * SR)))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def onepole(x, cutoff):
    """Simple low-pass; cutoff may be a scalar or a per-sample array."""
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    k = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += k[i] * (x[i] - acc)
        y[i] = acc
    return y


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


# ---------------------------------------------------------------- SFX library
def whoosh(length=0.55, lo=300, hi=5200):
    n = int(length * SR)
    x = rng.standard_normal(n)
    sweep = np.concatenate([np.geomspace(lo, hi, n // 2), np.geomspace(hi, lo, n - n // 2)])
    y = onepole(x, sweep) - onepole(x, sweep * 0.25)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    return norm(y * shape, 0.8)


def pop():
    tt = t(0.13)
    f = 280 + 650 * np.exp(-tt * 38)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-tt * 30)
    y[:60] += rng.standard_normal(60) * 0.3
    return norm(y, 0.7)


def tick():
    tt = t(0.05)
    return norm(np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 90), 0.35)


def click():
    tt = t(0.06)
    n = rng.standard_normal(len(tt))
    hp = n - onepole(n, 1500)
    return norm(hp * np.exp(-tt * 120) + 0.4 * np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 80), 0.55)


def key():
    tt = t(0.035)
    n = rng.standard_normal(len(tt))
    hp = n - onepole(n, 2500)
    return hp * np.exp(-tt * 160)


def ding():
    tt = t(1.0)
    y = np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt) + 0.25 * np.sin(2 * np.pi * 2637 * tt)
    return norm(y * np.exp(-tt * 5.5) * env(len(tt), 0.004, 0.05), 0.42)


def impact():
    tt = t(1.3)
    f = 38 + 110 * np.exp(-tt * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    n = rng.standard_normal(len(tt))
    body = onepole(n, 900) * np.exp(-tt * 9) * 2.5
    return norm((sub + body) * env(len(tt), 0.002, 0.2), 0.95)


def shimmer():
    tt = t(1.8)
    y = np.zeros_like(tt)
    for i, f in enumerate([1046.5, 1318.5, 1568, 2093, 2637, 3136]):
        start = int(i * 0.07 * SR)
        seg = tt[: len(tt) - start]
        y[start:] += np.sin(2 * np.pi * f * seg) * np.exp(-seg * 3.2) * (0.9 - i * 0.1)
    sparkle = rng.standard_normal(len(tt))
    sparkle = (sparkle - onepole(sparkle, 6000)) * np.exp(-tt * 4) * 0.15
    return norm((y + sparkle) * env(len(tt), 0.01, 0.3), 0.55)


def riser(length=1.4):
    tt = t(length)
    n = rng.standard_normal(len(tt))
    cut = np.geomspace(300, 9000, len(tt))
    noise = onepole(n, cut)
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(180, 900, len(tt))) / SR) * 0.35
    shape = np.linspace(0, 1, len(tt)) ** 2.2
    return norm((noise + tone) * shape * env(len(tt), 0.01, 0.03), 0.7)


LIB = {"whoosh": whoosh(), "swoosh": whoosh(0.35, 800, 7000) * 0.55, "pop": pop(), "tick": tick(),
       "click": click(), "ding": ding(), "impact": impact(), "shimmer": shimmer(), "riser": riser()}
GAIN = {"whoosh": 0.5, "swoosh": 0.45, "pop": 0.42, "tick": 0.5, "click": 0.6, "ding": 0.5,
        "impact": 0.75, "shimmer": 0.6, "riser": 0.45}


# ---------------------------------------------------------------- cues from the HTML
def read_cues():
    html = (ROOT / "index.html").read_text()
    cues = []
    for tag in re.findall(r"<[^>]*data-sfx=\"\w+\"[^>]*>", html):
        name = re.search(r'data-sfx="(\w+)"', tag).group(1)
        if name == "type":
            continue
        at = re.search(r'data-t="([\d.]+)"', tag)
        cues.append((float(at.group(1)), name))
    typing = re.findall(r'<span data-type="([\d.]+)" data-dur="([\d.]+)" data-sfx="type">(.*?)</span>', html)
    wipes = [float(v) for v in re.search(r"const WIPES = \[([^\]]*)\]", html).group(1).split(",")]
    for b in wipes:
        cues.append((b - 0.27, "whoosh"))
    cues.append((wipes[-2] - 1.4, "riser"))
    return cues, typing


def build_sfx():
    n = int(DUR * SR)
    left, right = np.zeros(n), np.zeros(n)
    cues, typing = read_cues()
    for at, name in cues:
        clip = LIB[name] * GAIN[name]
        s = int(at * SR)
        e = min(n, s + len(clip))
        seg = clip[: e - s]
        if name == "whoosh":  # sweep left to right, like the wipe
            pan = np.linspace(0.15, 0.85, len(seg))
        else:
            pan = np.full(len(seg), 0.5)
        left[s:e] += seg * np.sqrt(1 - pan)
        right[s:e] += seg * np.sqrt(pan)
    for start, dur, text in typing:
        start, dur = float(start), float(dur)
        count = len(text)
        step = dur / count
        every = max(1, int(np.ceil(0.045 / step)))  # cap at ~22 keys per second
        for i in range(0, count, every):
            k = key() * (0.18 + 0.08 * rng.random())
            s = int((start + i * step) * SR)
            left[s : s + len(k)] += k * 0.7
            right[s : s + len(k)] += k * 0.7
    print(f"sfx cues: {len(cues)} one-shots, {len(typing)} typing runs")
    return np.stack([left, right], axis=1)


# ---------------------------------------------------------------- music bed
def note(f, length, harmonics=6, detune=0.003):
    tt = t(length)
    y = np.zeros_like(tt)
    for h in range(1, harmonics + 1):
        amp = 1 / h**1.6
        y += amp * (np.sin(2 * np.pi * f * h * (1 + detune) * tt) + np.sin(2 * np.pi * f * h * (1 - detune) * tt))
    return y


def build_music():
    n = int(DUR * SR)
    out = np.zeros(n)
    bpm = 104
    beat = 60 / bpm
    bar = beat * 4
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    roots = [110.0, 87.3, 130.8, 98.0]
    pad = np.zeros(n)
    bass = np.zeros(n)
    tchord = 0.0
    i = 0
    while tchord < DUR:
        length = min(bar * 2, DUR - tchord)
        s = int(tchord * SR)
        seg = sum(note(f, length) for f in chords[i % 4]) * env(int(length * SR), 0.35, 0.5)
        pad[s : s + len(seg)] += seg
        for b in range(8):  # bass on every beat of the two bars, short and round
            bt = tchord + b * beat
            if bt >= DUR:
                break
            bl = min(beat * 0.9, DUR - bt)
            bs = int(bt * SR)
            tt = t(bl)
            bseg = (np.sin(2 * np.pi * roots[i % 4] * tt) + 0.3 * np.sin(4 * np.pi * roots[i % 4] * tt)) * np.exp(-tt * 4)
            bass[bs : bs + len(bseg)] += bseg
        tchord += bar * 2
        i += 1
    pad = onepole(pad, 1400)
    drums = np.zeros(n)
    kick_t = t(0.3)
    kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-kick_t * 30)) / SR) * np.exp(-kick_t * 9)
    hat_t = t(0.04)
    hn = rng.standard_normal(len(hat_t))
    hat = (hn - onepole(hn, 7000)) * np.exp(-hat_t * 110)
    clap_t = t(0.16)
    cn = rng.standard_normal(len(clap_t))
    clap = (onepole(cn, 3000) - onepole(cn, 900)) * np.exp(-clap_t * 22)
    k = 0
    bt = 3.55  # drums enter after the hook
    while bt < DUR - 0.3:
        s = int(bt * SR)
        drums[s : s + len(kick)] += kick[: n - s] * 0.9
        if k % 2 == 1:
            drums[s : s + len(clap)] += clap[: n - s] * 0.5
        hs = int((bt + beat / 2) * SR)
        if hs < n:
            drums[hs : hs + len(hat)] += hat[: n - hs] * 0.35
        bt += beat
        k += 1
    mix = norm(pad) * 0.55 + norm(bass) * 0.45 + norm(drums) * 0.5
    # sit under the voice, open up on the end card, fade out
    level = np.full(n, 0.12)
    ramp = int(1.0 * SR)
    level[:ramp] = np.linspace(0, 0.12, ramp)
    end = int(43.3 * SR)
    level[end : end + ramp] = np.linspace(0.12, 0.42, ramp)
    level[end + ramp :] = 0.42
    fade = int(1.4 * SR)
    level[-fade:] *= np.linspace(1, 0, fade)
    music = norm(mix, 0.9) * level
    return np.stack([music, music], axis=1)


def write(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "sfx.wav", build_sfx())
    write(OUT / "music.wav", build_music())
