"""HAVOC ad v2 soundtrack: smooth premium-tech track + refined SFX + Kokoro VO (all generated here).

124.8 BPM -> 52 beats = exactly 25 s. Downbeats (bar starts) fall on beats 1, 5, 9, ... so the
drop lands on beat 5 (2.40 s) with the brand reveal, and the breakdown resolves on beat 37 (17.79 s).
"""
import json
import math
import subprocess
import sys

import numpy as np

VO_DIR, OUT = sys.argv[1], sys.argv[2]
SR = 44100
BPM = 124.8
B = 60 / BPM
DUR = 25.0
N = int(DUR * SR)
rng = np.random.default_rng(21)

VO_AT = {"hook": 0.10, "meet": 2.62, "venom": 4.45, "layers": 6.38, "gasket": 8.28, "swap": 9.22, "pbt": 10.22,
         "specs": 12.15, "gaming": 17.92, "price": 19.85, "cta": 22.72}


def tb(b):
    return b * B


def bar_t(n):
    return tb(1 + 4 * n)


music = np.zeros((N, 2), np.float32)
send = np.zeros((N, 2), np.float32)  # reverb send
sfx = np.zeros((N, 2), np.float32)
vo = np.zeros((N, 2), np.float32)
pump = np.ones(N, np.float32)  # sidechain gain for pads/bass


def put(buf, t0, sig, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if sig.ndim == 1:
        lg, rg = math.cos((pan + 1) * math.pi / 4) * 1.414, math.sin((pan + 1) * math.pi / 4) * 1.414
        sig = np.stack([sig * lg, sig * rg], 1)
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    m = min(len(sig), N - i0)
    if m > 0:
        buf[i0:i0 + m] += (sig[:m] * gain).astype(np.float32)


def T(d):
    return np.arange(int(d * SR)) / SR


def fft_filter(x, lo=None, hi=None, slope=4):
    """Zero-phase smooth band filter via FFT (x: (n,) or (n,2))."""
    n = len(x)
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / (1 + (f / hi) ** (2 * slope))
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 * slope))
    if X.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n, axis=0).astype(np.float32)


def lp_loop(sig, fc):
    fc = np.broadcast_to(np.asarray(fc, np.float64), sig.shape[:1])
    a = np.exp(-2 * np.pi * fc / SR)
    out = np.empty_like(sig)
    y = np.zeros(sig.shape[1:]) if sig.ndim > 1 else 0.0
    for i in range(len(sig)):
        y = a[i] * y + (1 - a[i]) * sig[i]
        out[i] = y
    return out


def note(n):
    return 440 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- one-shots
def mk_kick():
    t = T(0.42)
    f = 47 + 95 * np.exp(-t / 0.032)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17) * np.clip(t / 0.002, 0, 1)
    click = fft_filter(rng.normal(0, 1, len(t)), lo=2000, hi=7000) * np.exp(-t / 0.0015) * 0.18
    return np.tanh(1.3 * (s + click)).astype(np.float32) * 0.85


def mk_clap():
    t = T(0.45)
    nz = fft_filter(rng.normal(0, 1, len(t)), lo=900, hi=5200)
    env = np.zeros(len(t))
    for d in (0, 0.008, 0.017, 0.024):
        env += np.where(t >= d, np.exp(-(t - d) / 0.004), 0) * 0.8
    env += np.where(t >= 0.024, np.exp(-(t - 0.024) / 0.075), 0) * 0.55
    return (nz / np.abs(nz).max() * env * 0.55).astype(np.float32)


def mk_hat(tau, amp):
    t = T(tau * 7)
    nz = fft_filter(rng.normal(0, 1, len(t)), lo=7500, hi=15000)
    return (nz / np.abs(nz).max() * np.exp(-t / tau) * amp).astype(np.float32)


KICK, CLAP = mk_kick(), mk_clap()
HAT_C, HAT_O = mk_hat(0.016, 0.22), mk_hat(0.10, 0.16)


def saw_tone(f, dur, fc, voices=(0.0,), amp_env=None, harm_decay=None, phase_seed=0):
    """Band-limited saw (additive) with a smooth spectral roll-off at fc."""
    t = T(dur)
    out = np.zeros(len(t))
    r = np.random.default_rng(phase_seed)
    for det in voices:
        fv = f * 2 ** (det / 1200)
        hmax = int(min(40, 9000 / fv))
        for h in range(1, hmax + 1):
            w = (1 / h) / (1 + ((h * fv) / fc) ** 4)
            if w < 0.002:
                break
            comp = np.sin(2 * np.pi * fv * h * t + r.uniform(0, 6.28))
            if harm_decay:
                comp = comp * np.exp(-t / (harm_decay / (1 + 0.35 * (h - 1))))
            out += w * comp
    out /= max(1, len(voices))
    if amp_env is not None:
        out *= amp_env(t)
    return out.astype(np.float32)


# ---------------------------------------------------------------- harmony
CHORDS = [  # per bar: pad voicing (MIDI), bass root (MIDI), arp tones (MIDI)
    ([53, 56, 60, 63, 67], 41, [72, 75, 77, 80, 84, 80, 77, 75]),  # Fm9
    ([49, 53, 56, 60, 65], 37, [72, 73, 77, 80, 84, 80, 77, 73]),  # Dbmaj7
    ([44, 51, 55, 60, 63], 44, [72, 75, 79, 80, 84, 80, 79, 75]),  # Abmaj7
    ([51, 55, 58, 63, 67], 39, [70, 74, 75, 79, 82, 79, 75, 74]),  # Eb
]
NBARS = 13
BAR = 4 * B
GROOVE = {1, 2, 3, 4, 5, 6, 7, 9, 10, 11}  # bars with drums (0 intro, 8 breakdown, 12 ending)

# sidechain pump on every beat inside groove bars
for n in GROOVE:
    for k in range(4):
        tk = bar_t(n) + k * B
        i0 = int(tk * SR)
        m = min(int(B * SR), N - i0)
        if m <= 0:
            continue
        tt = np.arange(m) / SR
        g = 1 - 0.55 * np.exp(-tt / 0.13) * np.clip(tt / 0.006, 0, 1) - 0.55 * (tt < 0.006)
        pump[i0:i0 + m] = np.minimum(pump[i0:i0 + m], np.clip(g, 0.35, 1))

# pads (legato, crossfaded per bar), filter opens in intro and breakdown
pad = np.zeros((N, 2), np.float32)
for n in range(-1, NBARS):
    t0 = bar_t(n) if n >= 0 else 0.0
    dur = (bar_t(n + 1) - t0) + 0.35
    if n == NBARS - 1:
        dur = DUR - t0
    voic, _, _ = CHORDS[max(n, 0) % 4]
    if n <= 0:
        fc = 700
    elif n == 8:
        fc = 2600
    else:
        fc = 1500
    env = lambda tt, d=dur: np.clip(tt / 0.18, 0, 1) * np.clip((d - tt) / 0.3, 0, 1)
    sigL = sum(saw_tone(note(m_), dur, fc, (-9, 0, 7), env, phase_seed=m_ * 3 + n) for m_ in voic)
    sigR = sum(saw_tone(note(m_), dur, fc, (-6, 0, 10), env, phase_seed=m_ * 5 + n + 99) for m_ in voic)
    put(pad, t0, np.stack([sigL, sigR], 1) * 0.06 * (2.0 if n == 8 else 1.0))
# intro swell + breakdown swell
tt = np.arange(N) / SR
pad_gain = np.clip(tt / 1.2, 0, 1) * 0.7 + 0.3 * np.clip(tt / 1.2, 0, 1)
pad *= pad_gain[:, None]
pad = fft_filter(pad, lo=120)
put(music, 0, pad * pump[:, None], 1.0)
put(send, 0, pad, 0.35)

# sub bass (sustained root per groove bar, sidechained)
for n in range(NBARS):
    if n not in GROOVE and n != 12:
        continue
    _, root, _ = CHORDS[n % 4]
    t0 = bar_t(n)
    dur = BAR + 0.02 if n != 12 else 1.4
    t_ = T(dur)
    f0 = note(root)
    s = np.sin(2 * np.pi * f0 * t_) + 0.25 * np.sin(4 * np.pi * f0 * t_)
    env = np.clip(t_ / 0.01, 0, 1) * np.clip((dur - t_) / 0.03, 0, 1)
    if n == 12:
        env *= np.exp(-t_ / 0.6)
    put(music, t0, (np.tanh(1.4 * s * env) * 0.42).astype(np.float32))
i_b = int(bar_t(1) * SR)
music[i_b:] *= np.stack([pump[i_b:], pump[i_b:]], 1) ** 0.5  # gentle pump on everything after the drop

# pluck arp (16ths), ping-pong delay + reverb send
arp = np.zeros((N, 2), np.float32)
for n in range(NBARS):
    _, _, tones = CHORDS[n % 4]
    for s16 in range(16):
        t0 = bar_t(n) + s16 * B / 4
        if t0 >= DUR - 0.05:
            continue
        if n == 0 and s16 < 4:
            continue
        if n == 12 and s16 > 0:
            continue
        mn = tones[s16 % 8] + (12 if (n >= 4 and s16 % 4 == 2 and n != 8) else 0)
        vel = 0.75 if s16 % 4 == 0 else 0.5
        if n == 0:
            vel *= 0.45 + 0.4 * s16 / 16
        if n == 8:
            vel *= 1.6
        p = saw_tone(note(mn), 0.42, 2600 if n != 0 else 1200, (0.0, 6), harm_decay=0.16,
                     amp_env=lambda tt: np.exp(-tt / 0.15) * np.clip(tt / 0.002, 0, 1), phase_seed=mn + s16)
        put(arp, t0, p * vel * 0.10, 1.0, pan=0.25 if s16 % 2 else -0.25)
dly = int(3 * B / 4 * SR)
wet = np.zeros_like(arp)
for k, g in enumerate((0.42, 0.25, 0.14, 0.08), 1):
    sh = np.roll(arp, dly * k, axis=0)
    sh[:dly * k] = 0
    wet += sh[:, ::-1] * g if k % 2 else sh * g
put(music, 0, (arp + wet * 0.8) * pump[:, None] ** 0.6, 1.0)
put(send, 0, arp + wet, 0.45)

# drums
for n in range(NBARS):
    for s16 in range(16):
        t0 = bar_t(n) + s16 * B / 4
        if t0 >= DUR:
            continue
        if n in GROOVE:
            if s16 % 4 == 0:
                put(music, t0, KICK, 0.9)
            if s16 in (4, 12):
                put(music, t0, CLAP, 0.55, 0.05)
                put(send, t0, CLAP, 0.5)
            if s16 % 2 == 1 or n >= 4:
                put(music, t0, HAT_C, (0.55 if s16 % 2 else 0.3), 0.3)
            if s16 % 4 == 2:
                put(music, t0, HAT_O, 0.5, -0.2)
        if n == 8:  # build: claps 8ths -> 16ths, rising
            if (s16 >= 4 and s16 % 2 == 0) or s16 >= 12:
                v = 0.3 + 0.9 * s16 / 16
                put(music, t0, CLAP, v, 0.0)
                put(send, t0, CLAP, v * 0.6)
put(music, bar_t(12), KICK, 1.0)


# ---------------------------------------------------------------- SFX (smooth)
def whoosh(t_mid, dur=0.5, amp=0.16, f0=350, f1=4500, pan=(-0.5, 0.5), sub=False):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = rng.normal(0, 1, (m, 2))
    fc = f0 * (f1 / f0) ** np.sin(u * np.pi / 2)
    sig = lp_loop(nz, fc) - lp_loop(nz, fc * 0.35)
    env = np.sin(np.pi * u) ** 2
    pp = pan[0] + (pan[1] - pan[0]) * u
    lg, rg = np.cos((pp + 1) * np.pi / 4), np.sin((pp + 1) * np.pi / 4)
    sig = sig * env[:, None] * np.stack([lg, rg], 1) * 1.414
    sig = sig / (np.abs(sig).max() + 1e-9) * amp
    if sub:
        st = np.arange(m) / SR
        boom = np.sin(2 * np.pi * np.cumsum(70 * (0.6 ** u)) / SR) * env * 0.5 * amp / 0.16
        sig += np.stack([boom, boom], 1)
    put(sfx, t_mid - dur / 2, sig.astype(np.float32))


def boom(t0, amp=0.4):
    t = T(1.6)
    f = 34 + 30 * np.exp(-t / 0.09)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7) * np.clip(t / 0.006, 0, 1)
    put(sfx, t0, (np.tanh(1.2 * s) * amp).astype(np.float32))
    put(send, t0, (s * amp * 0.2).astype(np.float32))


def thock(t0, pitch=1.0, vel=1.0, pan=0.0):
    t = T(0.14)
    body = (np.sin(2 * np.pi * 190 * pitch * t) * np.exp(-t / 0.024) + 0.55 * np.sin(2 * np.pi * 390 * pitch * t) *
            np.exp(-t / 0.014) + 0.25 * np.sin(2 * np.pi * 1050 * pitch * t) * np.exp(-t / 0.006) +
            0.5 * np.sin(2 * np.pi * 98 * pitch * t) * np.exp(-t / 0.032))
    click = fft_filter(rng.normal(0, 1, len(t)), lo=1800, hi=6000) * np.exp(-t / 0.0014) * 0.35
    put(sfx, t0, ((body + click) * 0.5 * vel).astype(np.float32), 1.0, pan)
    up = np.sin(2 * np.pi * 300 * pitch * t) * np.exp(-t / 0.010) * 0.12
    put(sfx, t0 + 0.06, (up * vel).astype(np.float32), 1.0, pan)


def tick(t0, amp=0.07, f=1500):
    t = T(0.08)
    s = np.sin(2 * np.pi * (f * (1 + 0.25 * np.exp(-t / 0.01))) * t) * np.exp(-t / 0.018) * np.clip(t / 0.0015, 0, 1)
    put(sfx, t0, (s * amp).astype(np.float32), 1.0, rng.uniform(-0.25, 0.25))
    put(send, t0, (s * amp * 0.5).astype(np.float32))


def chime(t0, freqs, amp=0.07, gap=0.07):
    for i, f in enumerate(freqs):
        t = T(1.2)
        s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5) + 0.3 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.2) +
             0.12 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / 0.08)) * np.clip(t / 0.003, 0, 1)
        put(sfx, t0 + i * gap, (s * amp).astype(np.float32), 1.0, -0.3 + 0.6 * i / max(1, len(freqs) - 1))
        put(send, t0 + i * gap, (s * amp * 0.6).astype(np.float32))


def shimmer(t0, dur=0.6, amp=0.05):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = fft_filter(rng.normal(0, 1, (m, 2)), lo=7000, hi=14000)
    sig = nz / np.abs(nz).max() * (np.sin(np.pi * u) ** 2)[:, None] * amp
    put(sfx, t0, sig.astype(np.float32))
    put(send, t0, sig.astype(np.float32), 0.8)


def riser(t_end, dur, amp=0.1):
    m = int(dur * SR)
    u = np.linspace(0, 1, m)
    nz = rng.normal(0, 1, (m, 2))
    fc = 300 * (8000 / 300) ** u
    sig = (lp_loop(nz, fc) - lp_loop(nz, fc * 0.5)) * (u ** 2.4)[:, None]
    sig = sig / (np.abs(sig).max() + 1e-9) * amp
    put(sfx, t_end - dur, sig.astype(np.float32))
    put(send, t_end - dur, sig.astype(np.float32), 0.5)


# hook keystrokes (sync with the visual key glows)
HOOK_KEYS = [0.0, 0.5, 1.0, 1.25, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5, 3.75, 4.0, 4.25, 4.5]
for b in HOOK_KEYS:
    thock(tb(b) + 0.03, rng.uniform(0.94, 1.06), 1.0 if b in (0.0, 2.0, 4.0) else 0.72, rng.uniform(-0.35, 0.35))
riser(bar_t(1), 1.4, 0.09)
# brand red sweeps (reveal + gaming)
for tm in (bar_t(1), bar_t(9)):
    whoosh(tm, 0.8, 0.2, 250, 5000, (-0.2, 0.2), sub=True)
    boom(tm + 0.02, 0.5)
    shimmer(tm + 0.25, 0.7, 0.04)
riser(bar_t(9), 1.9, 0.1)
# slide transitions (soft, rising air)
for tm in (tb(9), tb(13), tb(17), tb(21), tb(25), tb(41), tb(47)):
    whoosh(tm + 0.02, 0.5, 0.11, 400, 4200, (0.3, -0.3))
whoosh(9.18 + 0.02, 0.36, 0.08, 500, 5000, (-0.4, 0.4))  # gasket -> hot-swap
whoosh(tb(31), 0.6, 0.12, 250, 3000, (0, 0))  # zoom-through
whoosh(16.35, 0.4, 0.08, 500, 5000, (0.4, -0.4))
whoosh(24.05, 0.5, 0.09, 300, 4000, (0, 0))
# reveal details
shimmer(3.25, 0.7, 0.05)  # HAVOC light sweep
S16 = B / 4  # event grid shared with ugc_ad2.py (EV)
for i in range(4):  # venom callouts
    tick(tb(10) + i * S16, 0.06, 1700)
for i in range(3):  # layer chips
    tick(tb(14.5) + i * S16, 0.06, 1500)
for i in range(9):  # gasket pulses
    tick(tb(17.75) + i * S16 / 2, 0.03, 2000 + 60 * i)
for t0 in (tb(22), tb(22.5)):  # keycap callouts
    tick(t0, 0.06, 1600)
for i in range(4):  # stat cards
    tick(tb(26) + i * S16, 0.06, 1400)
for k in range(1, 18):  # counters (ease-out: ticks thin out as the numbers settle)
    tick(tb(26) + 0.12 + 1.1 * (1 - (1 - k / 18) ** (1 / 3)), 0.02, 2600)
shimmer(15.2, 0.8, 0.04)
chime(20.25, [note(84), note(87), note(89), note(91), note(96)], 0.05, 0.06)  # stars
shimmer(20.3, 0.6, 0.05)  # price light sweep
for i in range(4):  # perks
    tick(tb(43.5) + i * S16, 0.055, 1500)
# CTA tap + confirm, end logo
tt_ = T(0.03)
clk = fft_filter(rng.normal(0, 1, len(tt_)), lo=2500, hi=9000) * np.exp(-tt_ / 0.0016) * 0.3
put(sfx, 23.18, clk.astype(np.float32))
chime(23.22, [note(84), note(91)], 0.07, 0.09)
shimmer(24.25, 0.7, 0.05)
boom(bar_t(12), 0.35)

# ---------------------------------------------------------------- reverb (FFT convolution)
ir_t = T(2.2)
ir = rng.normal(0, 1, (len(ir_t), 2)) * np.exp(-ir_t / 0.55)[:, None]
ir = fft_filter(ir, lo=200, hi=6500)
ir /= np.sqrt((ir ** 2).sum(0))
L = 1 << int(np.ceil(np.log2(N + len(ir_t))))
rev = np.fft.irfft(np.fft.rfft(send, L, axis=0) * np.fft.rfft(ir, L, axis=0), L, axis=0)[:N].astype(np.float32)
music += rev * 0.55

# ---------------------------------------------------------------- VO + duck
meta = json.load(open(f"{VO_DIR}/vo.json"))
for key, t0 in VO_AT.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{VO_DIR}/{key}.wav", "-ar", str(SR), "-ac", "1",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    a = a + fft_filter(a, lo=2800) * 0.3  # presence
    put(vo, t0, np.stack([a, a], 1), 1.0)

env = np.convolve(np.abs(vo[:, 0]), np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same")
speech = (env > 0.015).astype(np.float32)
k = int(0.25 * SR)
duck = np.clip(np.convolve(speech, np.ones(k) / k, mode="same") * 1.6, 0, 1)


def rms_db(x, m=None):
    x = x if m is None else x[m]
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


sp = speech > 0.5
music *= (1 - 0.6 * duck)[:, None]
g_music = 10 ** ((rms_db(vo, sp) - 10 - rms_db(music, sp)) / 20)
music *= g_music
g_sfx = 1.0
mix = music + sfx + vo
t_all = np.arange(N) / SR
mix *= np.clip((DUR - t_all) / 0.3, 0, 1)[:, None] * np.clip(t_all / 0.02, 0, 1)[:, None]
mix = fft_filter(mix, lo=32, slope=2)


# ---------------------------------------------------------------- master: -14 LUFS, true peak <= -1.5 dBTP
def _biquad_shelf(fs, fc=1500.0, gain_db=4.0, q=1 / np.sqrt(2)):
    A, w0 = 10 ** (gain_db / 40), 2 * np.pi * fc / fs
    al, c = np.sin(w0) / (2 * q), np.cos(w0)
    b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
         A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
    a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
         (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
    return np.array(b) / a[0], np.array(a) / a[0]


def _biquad_hp(fs, fc=38.0, q=0.5):
    w0 = 2 * np.pi * fc / fs
    al, c = np.sin(w0) / (2 * q), np.cos(w0)
    b, a = [(1 + c) / 2, -(1 + c), (1 + c) / 2], [1 + al, -2 * c, 1 - al]
    return np.array(b) / a[0], np.array(a) / a[0]


def lufs(x):
    """ITU-R BS.1770-4 integrated loudness (K-weighted, gated)."""
    from scipy.signal import lfilter
    z = lfilter(*_biquad_shelf(SR), x, axis=0)
    z = lfilter(*_biquad_hp(SR), z, axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    ms = np.array([(z[i:i + blk] ** 2).mean(0).sum() for i in range(0, len(z) - blk, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-12)
    g = lk > -70
    rel = -0.691 + 10 * np.log10(ms[g].mean()) - 10
    g &= lk > rel
    return -0.691 + 10 * np.log10(ms[g].mean())


def true_peak_env(x, os=4):
    from scipy.signal import resample_poly
    up = np.abs(resample_poly(x, os, 1, axis=0)).max(1)
    return up[:len(x) * os].reshape(len(x), os).max(1)


def tp_limit(x, ceil_db=-1.5, look=0.0015, release=0.06):
    """Look-ahead true-peak limiter (4x oversampled detector, linked stereo)."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceil = 10 ** (ceil_db / 20)
    need = np.minimum(1.0, ceil / (true_peak_env(x) + 1e-12))
    L = max(3, int(look * SR))
    r = 1 - minimum_filter1d(need, 2 * L + 1)  # gain reduction, starting L samples ahead of each peak
    # instant attack, exponential release: env[n] = max_k r[k] * exp(-(n - k) / tau), done in log space
    tau, n = release * SR, np.arange(len(r))
    lg = np.log(np.maximum(r, 1e-12)) + n / tau
    env = np.exp(np.maximum.accumulate(lg) - n / tau)
    g = minimum_filter1d(uniform_filter1d(1 - env, L), L)  # de-click without letting peaks through
    return x * g[:, None]


gain = 10 ** ((-14.0 - lufs(mix)) / 20)
for _ in range(3):  # limiting removes a little loudness: re-aim until integrated loudness sits at -14 LUFS
    out = tp_limit(mix * gain)
    err = -14.0 - lufs(out)
    if abs(err) < 0.1:
        break
    gain *= 10 ** (err / 20)
mix = out
for _ in range(2):  # belt and braces: any residual overshoot gets one more pass
    if 20 * np.log10(true_peak_env(mix).max()) <= -1.45:
        break
    mix = tp_limit(mix)
mix.astype(np.float32).tofile(OUT)
print(f"music gain {g_music:.3f}  sfx gain {g_sfx:.2f}  loudness {lufs(mix):.1f} LUFS  "
      f"true peak {20 * np.log10(true_peak_env(mix).max()):.1f} dBTP  rms {rms_db(mix):.1f} dBFS")
json.dump({"vo_at": VO_AT, "bpm": BPM, "hook_keys": HOOK_KEYS}, open(OUT + ".json", "w"))
