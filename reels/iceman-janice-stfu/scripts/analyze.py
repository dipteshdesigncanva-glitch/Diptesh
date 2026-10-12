"""Beat / energy analysis of the song (numpy only)."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw

SR = 22050
HOP = 512
NFFT = 2048
y = np.fromfile(sys.argv[1], dtype=np.float32)
out_dir = sys.argv[2]

# STFT
win = np.hanning(NFFT).astype(np.float32)
n = 1 + (len(y) - NFFT) // HOP
idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
frames = y[idx] * win
mag = np.abs(np.fft.rfft(frames, axis=1)).astype(np.float32)
freqs = np.fft.rfftfreq(NFFT, 1 / SR)
fps = SR / HOP
times = np.arange(n) / fps

logm = np.log1p(10 * mag)
flux = np.maximum(0, np.diff(logm, axis=0, prepend=logm[:1])).sum(1)
low = (freqs >= 30) & (freqs <= 150)
kick = np.maximum(0, np.diff(logm[:, low], axis=0, prepend=logm[:1, low])).sum(1)
snare_band = (freqs >= 1500) & (freqs <= 6000)
snare = np.maximum(0, np.diff(logm[:, snare_band], axis=0, prepend=logm[:1, snare_band])).sum(1)
rms = np.sqrt((frames ** 2).mean(1))


def norm(x):
    x = x - np.median(x)
    return np.maximum(0, x) / (np.percentile(x, 99) + 1e-9)


onset = norm(flux)

# tempo via autocorrelation of onset envelope
oe = onset - onset.mean()
ac = np.correlate(oe[: int(60 * fps)], oe[: int(60 * fps)], mode="full")[int(60 * fps) - 1:]
best = None
for bpm in np.arange(60, 181, 0.25):
    lag = 60 * fps / bpm
    score = np.interp(lag, np.arange(len(ac)), ac) + 0.5 * np.interp(2 * lag, np.arange(len(ac)), ac)
    # mild preference for 80-160
    score *= np.exp(-0.5 * (np.log2(bpm / 120) / 1.0) ** 2)
    if best is None or score > best[0]:
        best = (score, bpm)
bpm = best[1]
period = 60 * fps / bpm

# DP beat tracking (Ellis)
alpha = 100.0
score = onset.copy()
back = np.full(n, -1)
for i in range(n):
    lo, hi = int(i - 2 * period), int(i - period / 2)
    if hi <= 0:
        continue
    lo = max(lo, 0)
    prev = np.arange(lo, hi)
    pen = -alpha * (np.log((i - prev) / period)) ** 2
    cand = score[prev] + pen
    j = np.argmax(cand)
    score[i] = onset[i] + cand[j]
    back[i] = prev[j]
i = int(np.argmax(score[-int(2 * period):])) + n - int(2 * period)
beats = []
while i >= 0:
    beats.append(i)
    i = back[i]
beats = np.array(beats[::-1])
beat_t = times[beats]

# energy profile per second
sec = int(times[-1])
prof = []
for s in range(sec):
    m = (times >= s) & (times < s + 1)
    prof.append((s, float(rms[m].mean()), float(norm(kick)[m].sum()), float(norm(snare)[m].sum())))

# best 25s window: high mean rms + high kick density, prefer window starting on beat
rms_s = np.array([p[1] for p in prof])
kick_s = np.array([p[2] for p in prof])
L = 25
cands = []
for s in range(0, sec - L):
    e = rms_s[s:s + L].mean() / rms_s.max() + 0.5 * kick_s[s:s + L].mean() / kick_s.max()
    cands.append((e, s))
cands.sort(reverse=True)

json.dump({
    "bpm": bpm,
    "beats": beat_t.round(4).tolist(),
    "profile": prof,
    "top_windows": cands[:12],
}, open(f"{out_dir}/analysis.json", "w"))

# picture: rms + kick + beat ticks
W, H = 2400, 600
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
T = times[-1]
for k, (arr, col) in enumerate([(rms / rms.max(), (30, 30, 200)), (norm(kick), (200, 30, 30))]):
    sm = np.convolve(arr, np.ones(20) / 20, mode="same")
    pts = [(t / T * W, H - 40 - (k * 0) - v * 250) for t, v in zip(times[::4], sm[::4])]
    d.line(pts, fill=col, width=2)
for s in range(0, int(T), 10):
    x = s / T * W
    d.line([(x, H - 40), (x, H - 30)], fill="black")
    d.text((x + 2, H - 28), f"{s}s", fill="black")
img.save(f"{out_dir}/energy.png")
print("bpm", round(bpm, 2), "beats", len(beat_t))
print("first beats", beat_t[:8].round(3))
print("top windows", cands[:12])
print("profile (sec, rms, kick, snare):")
for p in prof:
    print(f"{p[0]:4d} {p[1]:.3f} {p[2]:6.1f} {p[3]:6.1f}")
