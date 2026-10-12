"""Cut the 25s section of the song and add edit sound design.

- starts one bar before the first big 808 drop (song 45.76s)
- white-noise riser over the build bar (beats 4-8)
- ~0.2s drop gap (silence) right before the drop, so the 808 slams
- short fade in, fade out on the last half second
"""
import subprocess
import sys

import numpy as np

src, out = sys.argv[1], sys.argv[2]
SR = 44100
BEAT = 3.8151 / 8
START = 45.76 - 8 * BEAT  # the drop lands exactly on beat 8 of the edit
DUR = 25.0

raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{START:.4f}", "-t", f"{DUR}", "-i", src,
                      "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
n = len(x)
t = np.arange(n) / SR
drop = 8 * BEAT

g = np.ones(n, np.float32)
g *= np.clip(t / 0.06, 0, 1)  # fade in
gap0, gap1 = drop - 0.215, drop - 0.012
g *= np.where(t < gap0, 1, np.where(t < gap0 + 0.06, 1 - (t - gap0) / 0.06, 0))
g = np.where(t >= gap1, np.clip((t - gap1) / 0.008, 0, 1), g)  # back in just before the hit
g *= np.clip((DUR - t) / 0.5, 0, 1)  # fade out
x *= g[:, None]

# riser: band-passed noise sweeping up, beats 4 -> gap
rng = np.random.default_rng(3)
r0, r1 = 4 * BEAT, gap0 + 0.06
m = (t >= r0) & (t < r1)
k = np.where(m)[0]
p = (t[k] - r0) / (r1 - r0)
noise = rng.normal(0, 1, (len(k), 2)).astype(np.float32)
fc = 400 * (9000 / 400) ** p  # cutoff sweep
alpha = np.exp(-2 * np.pi * fc / SR)
hp = np.zeros_like(noise)
lp_prev = np.zeros(2, np.float32)
for i in range(len(k)):  # one-pole lowpass, then subtract -> highpass
    lp_prev = alpha[i] * lp_prev + (1 - alpha[i]) * noise[i]
    hp[i] = noise[i] - lp_prev
env = (p ** 2.2) * 0.16
x[k] += hp * env[:, None]

peak = np.abs(x).max()
if peak > 0.99:
    x *= 0.99 / peak
x.astype(np.float32).tofile(out)
print(f"start {START:.3f}s  drop at {drop:.3f}s  peak {peak:.3f}")
