"""Find the screen-recording mouse cursor (white arrow, dark outline) and inpaint it, in place."""
import glob
import sys

import numpy as np
from PIL import Image

# template from a frame where the cursor sits on a mid-grey area
ref = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(np.float32)[392:416, 979:999]
WM = (ref > 200).astype(np.float32)
KM = ((ref < 70) & ~(ref > 200)).astype(np.float32)
# keep only outline pixels that touch the white body
from numpy.lib.stride_tricks import sliding_window_view as swv

pad = np.pad(WM, 1)
near = swv(pad, (3, 3)).max(axis=(2, 3)) > 0
KM = KM * near
th, tw = WM.shape


def corr(img, k):
    H, W = img.shape
    F = np.fft.rfft2(img, (H + th, W + tw))
    G = np.fft.rfft2(k[::-1, ::-1], (H + th, W + tw))
    return np.fft.irfft2(F * G, (H + th, W + tw))[th - 1:H, tw - 1:W]


def find(gray):
    s = corr(gray, WM) / WM.sum() - corr(gray, KM) / KM.sum()
    w = corr(gray, WM) / WM.sum()
    s = np.where(w > 185, s, -1e9)
    y, x = np.unravel_index(np.argmax(s), s.shape)
    return (x, y, s[y, x])


def inpaint(arr, mask, iters=80):
    out = arr.astype(np.float32).copy()
    m = mask.astype(bool)
    out[m] = 0
    known = (~m).astype(np.float32)
    for _ in range(iters):
        p = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode="edge")
        kp = np.pad(known, 1, mode="edge")
        nb = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        kn = kp[:-2, 1:-1] + kp[2:, 1:-1] + kp[1:-1, :-2] + kp[1:-1, 2:]
        upd = m & (kn > 0)
        out[upd] = (nb[upd] / np.maximum(kn[upd], 1)[:, None])
        known = np.where(upd, 1.0, known)
    return out


def clean(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    g = a.astype(np.float32).mean(2)
    x, y, sc = find(g)
    if sc < 110:
        return False
    mask = np.zeros(g.shape, bool)
    body = (WM + KM) > 0
    mask[y:y + th, x:x + tw] |= body
    # dilate 2px
    for _ in range(2):
        mp = np.pad(mask, 1)
        mask = mp[1:-1, 1:-1] | mp[:-2, 1:-1] | mp[2:, 1:-1] | mp[1:-1, :-2] | mp[1:-1, 2:]
    y0, y1, x0, x1 = max(0, y - 6), y + th + 6, max(0, x - 6), x + tw + 6
    sub = inpaint(a[y0:y1, x0:x1], mask[y0:y1, x0:x1])
    out = a.copy()
    out[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(path, quality=95) if path.endswith(".jpg") else Image.fromarray(out).save(path)
    return (x, y, round(float(sc)))


files = []
for pat in sys.argv[2:]:
    files += sorted(glob.glob(pat))
hits = 0
for f in files:
    r = clean(f)
    if r:
        hits += 1
    if f.endswith("001.jpg") or "/t" in f:
        print(f.split("/")[-2] + "/" + f.split("/")[-1], r)
print("cleaned", hits, "of", len(files))
