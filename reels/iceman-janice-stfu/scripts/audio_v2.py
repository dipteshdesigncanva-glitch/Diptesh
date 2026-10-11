"""v2 audio: 30s cut of the song + synthesized sound design for the hook.

- the cut ends exactly on a bar line; the first big 808 drop lands at DROP_T
- message dings, key clicks (s-t-f-u), send whoosh + swell riser
- ~0.2s drop gap filled with ice-crack crackle, glass/ice shatter on the drop
- second shatter on the end card, soft limiter, short fades
"""
import math
import subprocess
import sys

import numpy as np

src, out = sys.argv[1], sys.argv[2]
SR = 44100
BEAT = 3.8151 / 8
DUR = 30.0
DROP_T = DUR - 56 * BEAT
K0 = 8 - DROP_T / BEAT
START = 45.76 - DROP_T  # first big 808 hit of the song is at 45.76s


def tb(k):
    return (k - K0) * BEAT


raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{START:.4f}", "-t", f"{DUR}", "-i", src,
                      "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
n = len(x)
t = np.arange(n) / SR

# ---- music gain: fade in, drop gap, fade out
g = np.clip(t / 0.04, 0, 1)
gap0, gap1 = DROP_T - 0.215, DROP_T - 0.012
g = g * np.where(t < gap0, 1, np.where(t < gap0 + 0.05, 1 - (t - gap0) / 0.05, 0))
g = np.where(t >= gap1, np.clip((t - gap1) / 0.008, 0, 1), g)
g *= np.clip((DUR - t) / 0.25, 0, 1)
x *= g[:, None].astype(np.float32)

rng = np.random.default_rng(5)
sfx = np.zeros_like(x)


def add(t0, sig, pan=0.0):
    i0 = int(t0 * SR)
    if sig.ndim == 1:
        lgain, rgain = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        sig = np.stack([sig * lgain * 1.414, sig * rgain * 1.414], 1)
    m = min(len(sig), n - i0)
    if m > 0:
        sfx[i0:i0 + m] += sig[:m]


def lowpass(sig, fc):
    """one-pole lowpass; fc scalar or per-sample array"""
    fc = np.broadcast_to(np.asarray(fc, np.float64), sig.shape[:1])
    a = np.exp(-2 * np.pi * fc / SR)
    out = np.empty_like(sig)
    y = np.zeros(sig.shape[1:]) if sig.ndim > 1 else 0.0
    for i in range(len(sig)):
        y = a[i] * y + (1 - a[i]) * sig[i]
        out[i] = y
    return out


def tone(freq, dur, decay, amp):
    tt = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * freq * tt) * np.exp(-tt / decay) * np.clip(tt / 0.003, 0, 1) * amp).astype(np.float32)


def ding(t0, amp=0.11):
    add(t0, tone(1568, 0.5, 0.11, amp) + tone(3136, 0.5, 0.05, amp * 0.25))
    add(t0 + 0.075, tone(2093, 0.5, 0.13, amp) + tone(4186, 0.5, 0.05, amp * 0.2))


def click(t0, amp=0.09):
    m = int(0.014 * SR)
    tt = np.arange(m) / SR
    nz = rng.normal(0, 1, m)
    nz = nz - lowpass(nz, 2500)  # highpass
    add(t0, (nz * np.exp(-tt / 0.0025) * amp + tone(3200, 0.014, 0.003, amp * 0.5)).astype(np.float32),
        rng.uniform(-0.2, 0.2))


def whoosh(t0, dur, amp, f0, f1, shape="bell", pan=(-0.6, 0.6)):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = rng.normal(0, 1, (m, 2))
    fc = f0 * (f1 / f0) ** u
    sig = lowpass(nz, fc) - lowpass(nz, fc * 0.25)
    env = np.sin(np.pi * u) ** 1.6 if shape == "bell" else u ** 2.2 * np.clip((1 - u) / 0.04, 0, 1)
    p = pan[0] + (pan[1] - pan[0]) * u
    lg, rg = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
    sig = sig * env[:, None] * np.stack([lg, rg], 1) * 1.414
    sig = sig / (np.abs(sig).max() + 1e-9) * amp
    add(t0, sig.astype(np.float32))


def crackle(t0, t1, amp, count=55):
    for _ in range(count):
        u = rng.uniform(0, 1) ** 0.55  # denser toward the drop
        f = rng.uniform(2200, 9500)
        a = amp * rng.uniform(0.25, 1.0) * (0.5 + 0.5 * u)
        dur = rng.uniform(0.004, 0.02)
        sig = tone(f, dur * 3, dur, a)
        m = len(sig)
        sig = sig + (rng.normal(0, 1, m) * np.exp(-np.arange(m) / SR / 0.0015) * a * 0.6).astype(np.float32)
        add(t0 + u * (t1 - t0), sig, rng.uniform(-0.8, 0.8))


def shatter(t0, amp):
    m = int(0.7 * SR)
    tt = np.arange(m) / SR
    nz = rng.normal(0, 1, (m, 2))
    body = nz - lowpass(nz, 700)
    body = lowpass(body, 9000) * (np.exp(-tt / 0.16) * np.clip(tt / 0.002, 0, 1))[:, None]
    add(t0, (body / np.abs(body).max() * amp).astype(np.float32))
    for _ in range(110):  # glassy tinkles raining out
        dt = min(rng.exponential(0.14), 0.95)
        f = rng.uniform(2500, 11000)
        a = amp * 0.55 * rng.uniform(0.15, 1.0) * math.exp(-dt / 0.35)
        add(t0 + dt, tone(f, 0.15, rng.uniform(0.012, 0.07), a), rng.uniform(-0.9, 0.9))


# ---- hook sound design
ding(tb(3))
ding(tb(4))
for k in (5, 5.5, 6, 6.5):
    click(tb(k))
click(tb(6.92), 0.07)
whoosh(tb(7.0), 0.26, 0.16, 900, 5000)  # send
whoosh(tb(7.0) + 0.08, gap0 - tb(7.0) - 0.06, 0.2, 300, 9000, shape="rise", pan=(0.5, 0.0))  # swell
crackle(gap0 + 0.015, DROP_T - 0.004, 0.2)
shatter(DROP_T, 0.42)
shatter(tb(56), 0.32)
whoosh(tb(55.75), tb(56) - tb(55.75), 0.12, 400, 7000, shape="rise", pan=(0.0, 0.0))

ding(tb(60), 0.09)
whoosh(tb(62.1), 0.3, 0.12, 700, 6000, pan=(0.0, 0.3))

y = x + sfx * np.clip((DUR - t) / 0.25, 0, 1)[:, None]
# soft limiter above 0.85
th = 0.85
a = np.abs(y)
over = a > th
y[over] = np.sign(y[over]) * (th + (1 - th) * np.tanh((a[over] - th) / (1 - th)))
y.astype(np.float32).tofile(out)
print(f"start {START:.3f}s  drop at {DROP_T:.3f}s  K0 {K0:.4f}  peak {np.abs(y).max():.3f}")
