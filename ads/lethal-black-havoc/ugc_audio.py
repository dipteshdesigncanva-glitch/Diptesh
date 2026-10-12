"""HAVOC ad soundtrack: synthesized 144 BPM phonk/trap beat + keyboard thocks + SFX + Kokoro VO.

Everything is generated here (no samples), so the ad carries no third-party music.
Timing is in beats (144 BPM -> 60 beats = exactly 25 s).
"""
import json
import math
import subprocess
import sys

import numpy as np

VO_DIR, OUT = sys.argv[1], sys.argv[2]
SR = 44100
BPM = 144
B = 60 / BPM
DUR = 25.0
N = int(DUR * SR)
rng = np.random.default_rng(11)

VO_AT = {"hook": 0.10, "meet": 2.60, "venom": 4.30, "layers": 5.92, "gasket": 7.56, "swap": 8.45, "pbt": 9.30,
         "specs": 10.97, "gaming": 15.10, "rating": 17.62, "price": 19.40, "cta": 21.85}

music = np.zeros((N, 2), np.float32)
sfx = np.zeros((N, 2), np.float32)
vo = np.zeros((N, 2), np.float32)


def tb(b):
    return b * B


def put(buf, t0, sig, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if sig.ndim == 1:
        lg, rg = math.cos((pan + 1) * math.pi / 4) * 1.414, math.sin((pan + 1) * math.pi / 4) * 1.414
        sig = np.stack([sig * lg, sig * rg], 1)
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    m = min(len(sig), N - i0)
    if m > 0:
        buf[i0:i0 + m] += sig[:m] * gain


def lp(sig, fc):
    fc = np.broadcast_to(np.asarray(fc, np.float64), sig.shape[:1])
    a = np.exp(-2 * np.pi * fc / SR)
    out = np.empty_like(sig)
    y = np.zeros(sig.shape[1:]) if sig.ndim > 1 else 0.0
    for i in range(len(sig)):
        y = a[i] * y + (1 - a[i]) * sig[i]
        out[i] = y
    return out


def hp(sig, fc):
    return sig - lp(sig, fc)


def T(dur):
    return np.arange(int(dur * SR)) / SR


def damp(f, tau, dur=None, amp=1.0, ph=0.0):
    t = T(dur or tau * 6)
    return (np.sin(2 * np.pi * f * t + ph) * np.exp(-t / tau) * amp).astype(np.float32)


# ---------------------------------------------------------------- instruments (pre-rendered)
def mk_kick():
    t = T(0.5)
    f = 46 + 130 * np.exp(-t / 0.028)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3)
    s += rng.normal(0, 1, len(t)) * np.exp(-t / 0.0018) * 0.25
    return np.tanh(1.8 * s).astype(np.float32) * 0.85


def mk_clap():
    t = T(0.4)
    nz = rng.normal(0, 1, len(t))
    nz = hp(lp(nz, 5200), 900)
    env = np.zeros(len(t))
    for d in (0, 0.009, 0.019):
        env += np.where(t >= d, np.exp(-(t - d) / 0.0045), 0)
    env += np.where(t >= 0.025, np.exp(-(t - 0.025) / 0.13), 0) * 0.55
    s = nz * env * 0.55 + damp(190, 0.045, 0.4, 0.35)
    return s.astype(np.float32)


def mk_hat(open_=False):
    t = T(0.35 if open_ else 0.08)
    nz = hp(rng.normal(0, 1, len(t)), 7200)
    return (nz * np.exp(-t / (0.16 if open_ else 0.022)) * 0.32).astype(np.float32)


KICK, CLAP, HAT, OHAT = mk_kick(), mk_clap(), mk_hat(), mk_hat(True)


def mk_808(freq, dur):
    t = T(dur)
    f = freq * (1 + 0.5 * np.exp(-t / 0.012))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.clip(t / 0.004, 0, 1) * np.exp(-t / 1.2) * np.clip((dur - t) / 0.02, 0, 1)
    return (np.tanh(2.6 * s * env) * 0.62).astype(np.float32)


_cow = {}


def cowbell(freq):
    if freq not in _cow:
        t = T(0.3)
        sq = np.sign(np.sin(2 * np.pi * freq * t)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
        s = hp(lp(sq, 3800), 420) * np.exp(-t / 0.085) * np.clip(t / 0.001, 0, 1)
        _cow[freq] = (s * 0.16).astype(np.float32)
    return _cow[freq]


def note(n):  # MIDI -> Hz
    return 440 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- arrangement
# F minor. Intro pad (beats 0-6), drop at beat 6.
t_int = T(tb(6.3))
pad = np.zeros(len(t_int))
cut = 300 + 2600 * (t_int / t_int[-1]) ** 2
for f0 in (note(53), note(56), note(60), note(65)):  # F3 Ab3 C4 F4
    for det in (-0.12, 0.12):
        for h in range(1, 14):
            g = (1 / h) / (1 + np.exp((h * f0 - cut) / 120))
            pad += g * np.sin(2 * np.pi * f0 * (1 + det / 100) * h * t_int + h * 1.3)
pad = pad / np.abs(pad).max() * 0.16 * np.clip(t_int / 0.25, 0, 1) * np.clip((tb(6.05) - t_int) / 0.04, 0, 1)
put(music, 0, np.stack([pad, np.roll(pad, 220)], 1).astype(np.float32))

BASS = [note(29), note(29), note(32), note(27)]  # F1 F1 Ab1 Eb1 per bar
COW_A = {0: 77, 3: 80, 6: 77, 8: 84, 10: 82, 12: 80, 14: 77}
COW_B = {0: 75, 3: 77, 6: 80, 8: 77, 11: 75, 14: 72}
step = B / 4
for bar in range(15):
    b0 = 4 * bar
    for s16 in range(16):
        bt = b0 + s16 / 4
        if bt < 6 or bt >= 60:
            continue
        brk = 32 <= bt < 36  # breakdown under the display scene
        t0 = tb(bt)
        kicks = [0, 6, 10] if bar % 2 == 0 else [0, 3, 6, 10, 14]
        if s16 in kicks and not brk:
            put(music, t0, KICK, 1.0)
            # 808 rides the kick until the next kick
            nxt = min([k for k in kicks if k > s16] + [16])
            put(music, t0, mk_808(BASS[bar % 4], (nxt - s16) * step + 0.02), 1.0)
        if s16 in (4, 12) and not brk:
            put(music, t0, CLAP, 0.9)
        if s16 % 2 == 0 or (bar % 2 == 1 and s16 >= 12):
            v = 0.9 if s16 % 4 == 0 else 0.6
            put(music, t0, HAT, v, 0.25)
            if bar % 2 == 1 and s16 >= 12 and not brk:  # trap roll: 32nds
                put(music, t0 + step / 2, HAT, 0.45, 0.25)
        if s16 == 14 and bar % 4 == 3 and not brk:
            put(music, t0, OHAT, 0.7, -0.2)
        cow = COW_A if bar % 2 == 0 else COW_B
        if s16 in cow:
            put(music, t0, cowbell(note(cow[s16])), 2.2 if brk else 1.0, -0.15)


# ---------------------------------------------------------------- SFX
def thock(t0, pitch=1.0, vel=1.0, pan=0.0):
    p = pitch
    body = damp(205 * p, 0.022, 0.12) + damp(430 * p, 0.014, 0.12, 0.6) + damp(1150 * p, 0.006, 0.12, 0.35)
    body += damp(105 * p, 0.03, 0.12, 0.5)
    t = T(0.12)
    click = hp(rng.normal(0, 1, len(t)), 2500) * np.exp(-t / 0.0015) * 0.5
    put(sfx, t0, ((body + click) * 0.55 * vel).astype(np.float32), 1.0, pan)
    up = damp(330 * p, 0.012, 0.06) + damp(1500 * p, 0.004, 0.06, 0.4)
    put(sfx, t0 + 0.055, (up * 0.16 * vel).astype(np.float32), 1.0, pan)


def whoosh(t_end, dur=0.3, amp=0.22, f0=500, f1=6000):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = rng.normal(0, 1, (m, 2))
    fc = f0 * (f1 / f0) ** u
    sig = lp(nz, fc) - lp(nz, fc * 0.3)
    env = np.sin(np.pi * u) ** 1.4 * (0.3 + 0.7 * u)
    sig = sig * env[:, None]
    put(sfx, t_end - dur, (sig / (np.abs(sig).max() + 1e-9) * amp).astype(np.float32))


def riser(t_end, dur, amp=0.2):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = rng.normal(0, 1, (m, 2))
    fc = 300 * (9000 / 300) ** u
    sig = (lp(nz, fc) - lp(nz, fc * 0.5)) * (u ** 2)[:, None]
    tone = np.sin(2 * np.pi * np.cumsum(220 * (6 ** u)) / SR) * u ** 2.5 * 0.25
    sig = sig / (np.abs(sig).max() + 1e-9) + tone[:, None]
    put(sfx, t_end - dur, (sig / np.abs(sig).max() * amp).astype(np.float32))


def impact(t0, amp=0.7):
    t = T(1.4)
    f = 32 + 40 * np.exp(-t / 0.06)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.75)
    nz = lp(rng.normal(0, 1, (len(t), 2)), 2200) * np.exp(-t / 0.28)[:, None]
    s = np.tanh(1.5 * sub)[:, None] * 0.8 + nz / np.abs(nz).max() * 0.45
    put(sfx, t0, (s * amp).astype(np.float32))


def pop(t0, amp=0.18, f0=700, f1=1500):
    t = T(0.09)
    f = f0 + (f1 - f0) * np.clip(t / 0.04, 0, 1)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035)
    put(sfx, t0, (s * amp).astype(np.float32), 1.0, rng.uniform(-0.3, 0.3))


def tick(t0, amp=0.08):
    put(sfx, t0, damp(2600, 0.004, 0.03, amp), 1.0, rng.uniform(-0.2, 0.2))


def ding(t0, amp=0.12, f=1760):
    s = damp(f, 0.35, 1.0) + damp(f * 2.76, 0.12, 1.0, 0.3) + damp(f * 5.4, 0.05, 1.0, 0.12)
    put(sfx, t0, (s * amp).astype(np.float32), 1.0, rng.uniform(-0.3, 0.3))


def ching(t0, amp=0.22):
    s = damp(2637, 0.45, 1.2) + damp(3951, 0.32, 1.2, 0.7) + damp(5274, 0.2, 1.2, 0.4)
    t = T(1.2)
    s += hp(rng.normal(0, 1, len(t)), 6000) * np.exp(-t / 0.25) * 0.35
    put(sfx, t0, (s / np.abs(s).max() * amp).astype(np.float32))


def click(t0, amp=0.25):
    for d, a in ((0, 1.0), (0.07, 0.6)):
        t = T(0.02)
        s = hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t / 0.0012) + np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.002)
        put(sfx, t0 + d, (s * amp * a).astype(np.float32))


def glitch(t0, dur=0.18, amp=0.12):
    m = int(dur * SR)
    s = np.zeros(m)
    i = 0
    while i < m:
        seg = int(rng.integers(300, 1800))
        f = rng.choice([180, 360, 720, 1440, 2880])
        tt = np.arange(min(seg, m - i)) / SR
        s[i:i + len(tt)] = np.sign(np.sin(2 * np.pi * f * tt)) * rng.uniform(0.3, 1)
        i += seg
    s = np.round(s * 4) / 4
    put(sfx, t0, (s * amp).astype(np.float32))


# hook: typing on the beat (lights snap on with the first big thock)
HOOK_KEYS = [0, 0.5, 1, 1.25, 1.5, 2, 2.5, 2.75, 3, 3.5, 3.75, 4, 4.5, 5, 5.25, 5.5]
for i, b in enumerate(HOOK_KEYS):
    thock(tb(b) + 0.02, rng.uniform(0.92, 1.08), 1.15 if b in (0, 2, 4) else 0.85, rng.uniform(-0.4, 0.4))
riser(tb(6), tb(3), 0.16)
for b in (6, 26, 36, 46, 56):
    impact(tb(b), 0.75 if b in (6, 36, 46, 56) else 0.5)
for b in (10, 14, 18, 20, 22, 26, 32, 34, 42, 52):
    whoosh(tb(b) + 0.03, 0.28, 0.17)
whoosh(tb(6) + 0.02, 0.45, 0.22, 300, 8000)
riser(tb(36), tb(3), 0.14)
riser(tb(46), tb(2), 0.14)
# detailing pops / ticks
for b in (10.6, 11.2, 11.8, 12.4):
    pop(tb(b), 0.14)
for b in (14.5, 14.75, 15.0, 15.25, 15.5):
    tick(tb(b), 0.1)
for b in (18.25, 18.5, 18.75, 19.0):
    pop(tb(b), 0.12, 900, 1700)
pop(tb(20.4), 0.14)
pop(tb(22.6), 0.14)
pop(tb(23.3), 0.12)
for i in range(46):  # counters ticking
    tick(tb(26.4) + i * 0.035, 0.05)
for b in (26.2, 27.7, 29.2):
    pop(tb(b), 0.16, 500, 1100)
for i, b in enumerate((42.5, 42.85, 43.2, 43.55, 43.9)):
    ding(tb(b), 0.1, 1760 * 2 ** (i * 2 / 12))
ching(tb(46) + 0.02, 0.24)
for b in (47, 48, 49, 50):
    pop(tb(b), 0.13, 800, 1600)
glitch(tb(36) - 0.02, 0.16, 0.1)
glitch(tb(52) - 0.05, 0.12, 0.08)
click(tb(53.5), 0.28)
pop(tb(53.6), 0.16, 600, 1300)

# ---------------------------------------------------------------- VO
meta = json.load(open(f"{VO_DIR}/vo.json"))
for key, t0 in VO_AT.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{VO_DIR}/{key}.wav", "-ar", str(SR), "-ac", "1",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    # gentle presence lift: add a little high-passed copy
    a = a + hp(a, 2500) * 0.35
    put(vo, t0, np.stack([a, a], 1).astype(np.float32), 0.95)

# sidechain-style duck: music sits under the voice
env = np.abs(vo[:, 0])
win = int(0.03 * SR)
env = np.convolve(env, np.ones(win) / win, mode="same")
att = env > 0.02
duck = np.where(att, 1.0, 0.0).astype(np.float32)
# release smoothing
k = int(0.18 * SR)
duck = np.convolve(duck, np.ones(k) / k, mode="same")
music *= (1 - 0.45 * np.clip(duck, 0, 1))[:, None]

def rms_db(x, m=None):
    x = x if m is None else x[m]
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


speech = duck > 0.5
print(f"bus rms  music {rms_db(music):.1f}  sfx {rms_db(sfx):.1f}  vo(speech) {rms_db(vo, speech):.1f}  "
      f"music(speech) {rms_db(music, speech):.1f}")
# gain staging: voice on top, music ~9 dB under it while talking
g_music = 10 ** ((rms_db(vo, speech) - 9 - rms_db(music, speech)) / 20)
music *= g_music
mix = music + sfx * 0.85 + vo
fade = np.clip((DUR - np.arange(N) / SR) / 0.35, 0, 1)[:, None]
mix *= fade
mix *= 10 ** ((-13.5 - rms_db(mix)) / 20)  # loudness target before limiting
th = 0.9
a = np.abs(mix)
o = a > th
mix[o] = np.sign(mix[o]) * (th + (1 - th) * np.tanh((a[o] - th) / (1 - th)))
over = (np.abs(mix) > 0.97).mean()
mix = np.clip(mix, -0.98, 0.98)
mix.astype(np.float32).tofile(OUT)
print(f"music gain {g_music:.2f}  limited samples {100 * (a > th).mean():.2f}%")
rms = np.sqrt((mix ** 2).mean())
print(f"done  rms {20 * np.log10(rms):.1f} dBFS  peak {np.abs(mix).max():.2f}")
json.dump({"vo_at": VO_AT, "bpm": BPM}, open(OUT + ".json", "w"))
