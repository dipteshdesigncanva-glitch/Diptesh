"""Synthesize the music bed and sound effects into public/audio/.

Everything is generated from scratch with numpy, so there are no licensing issues.
Usage: python3 scripts/make_audio.py

Music: 15 s, smooth R&B / lo-fi luxury feel. The grid is 120 BPM (one beat =
15 frames at 30 fps) so cuts land on beats, but the drums play half-time.
  0-2 s   electric-piano chord and an airy swell (logo reveal)
  2-14 s  soft kick, finger snaps, swung shaker, round sub bass, e-piano comping,
          a sparse bell melody and a little vinyl crackle
  14-15 s drums drop out, the last chord rings and fades for a clean loop
"""

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = 15.0
OUT = Path(__file__).resolve().parent.parent / "public" / "audio"
rng = np.random.default_rng(11)


def t_axis(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SR)) / SR


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def spectral_filter(x: np.ndarray, low: float = 0.0, high: float = SR / 2, order: int = 2) -> np.ndarray:
    """Static band filter done in the frequency domain (smooth Butterworth-like rolloff)."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    gain = np.ones_like(f)
    if high < SR / 2:
        gain *= 1 / np.sqrt(1 + (f / high) ** (2 * order))
    if low > 0:
        gain *= 1 / np.sqrt(1 + (low / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(spec * gain, n)


def sweep_filter(x: np.ndarray, centers: np.ndarray, q: float = 1.5) -> np.ndarray:
    """Time-varying band-pass via overlap-add STFT. `centers` gives Hz per sample."""
    win, hop = 2048, 512
    window = np.hanning(win)
    pad = np.concatenate([np.zeros(win), x, np.zeros(win)])
    cpad = np.concatenate([np.full(win, centers[0]), centers, np.full(win, centers[-1])])
    out = np.zeros_like(pad)
    norm = np.zeros_like(pad)
    f = np.fft.rfftfreq(win, 1 / SR)
    for start in range(0, len(pad) - win, hop):
        seg = pad[start : start + win] * window
        c = cpad[start + win // 2]
        gain = np.exp(-0.5 * ((f - c) / (c / q)) ** 2)
        out[start : start + win] += np.fft.irfft(np.fft.rfft(seg) * gain, win) * window
        norm[start : start + win] += window**2
    out = out / np.maximum(norm, 1e-6)
    return out[win : win + len(x)]


def reverb(x: np.ndarray, seconds: float = 1.6, mix: float = 0.25, seed: int = 1) -> np.ndarray:
    r = np.random.default_rng(seed)
    t = t_axis(seconds)
    ir = r.standard_normal(len(t)) * np.exp(-t * 6.9 / seconds)
    ir = spectral_filter(ir, low=250, high=5000)
    ir /= np.sqrt(np.sum(ir**2))
    n = len(x) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)]
    return x * (1 - mix) + wet * mix * 2.2


def place(buf: np.ndarray, sound: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    end = min(len(buf), i + len(sound))
    if 0 <= i < len(buf):
        buf[i:end] += sound[: end - i] * gain


# --- Instruments -----------------------------------------------------------------

def epiano(freq: float, seconds: float, velocity: float = 1.0) -> np.ndarray:
    """Rhodes-style FM electric piano: soft bell attack that mellows into a sine."""
    t = t_axis(seconds)
    index = 1.6 * velocity * np.exp(-t * 5) + 0.25
    mod = np.sin(2 * np.pi * freq * t)
    tone = np.sin(2 * np.pi * freq * t + index * mod)
    tine = np.sin(2 * np.pi * freq * 7.1 * t) * np.exp(-t * 28) * 0.12 * velocity
    env = np.minimum(t / 0.004, 1) * np.exp(-t * 1.1) * np.clip((seconds - t) / 0.08, 0, 1)
    return (tone + tine) * env * velocity


def chord(notes: list[int], seconds: float, velocity: float = 1.0) -> np.ndarray:
    out = np.zeros(int(seconds * SR))
    for j, m in enumerate(notes):
        # A tiny strum between notes makes it feel played
        note = epiano(midi_hz(m), seconds - j * 0.012, velocity)
        out[int(j * 0.012 * SR) : int(j * 0.012 * SR) + len(note)] += note
    return out / len(notes)


def bell(freq: float) -> np.ndarray:
    t = t_axis(1.6)
    tone = np.sin(2 * np.pi * freq * t + 0.8 * np.exp(-t * 3) * np.sin(2 * np.pi * freq * 3.5 * t))
    return tone * np.exp(-t * 2.4) * np.minimum(t / 0.003, 1)


def sub(freq: float, seconds: float) -> np.ndarray:
    t = t_axis(seconds)
    tone = np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(4 * np.pi * freq * t)
    env = np.minimum(t / 0.02, 1) * np.clip((seconds - t) / 0.06, 0, 1) * np.exp(-t * 0.8)
    return tone * env


def kick() -> np.ndarray:
    t = t_axis(0.5)
    freq = 46 + 70 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 6.5)
    return np.tanh(body * 1.3)


def snap() -> np.ndarray:
    t = t_axis(0.4)
    noise = spectral_filter(rng.standard_normal(len(t)), low=1400, high=6500)
    env = np.exp(-t * 45) + 0.25 * np.exp(-t * 10)
    tone = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 80) * 0.3
    return reverb((noise + tone) * env * 0.5, 1.2, 0.4, 21)


def shaker() -> np.ndarray:
    t = t_axis(0.09)
    noise = spectral_filter(rng.standard_normal(len(t)), low=6000, high=14000)
    return noise * np.sin(np.pi * t / 0.09) ** 2 * 0.25


# --- Music -----------------------------------------------------------------------

def make_music() -> np.ndarray:
    n = int(DUR * SR)
    keys = np.zeros(n)
    bass = np.zeros(n)
    drums = np.zeros(n)
    bells = np.zeros(n)

    # Bars are 2 s: Am9, Fmaj9, Cmaj9, Gadd9 (smooth, jazzy voicings)
    voicings = {
        "Am9": ([60, 64, 67, 71], 45),
        "Fmaj9": ([57, 64, 67, 72], 41),
        "Cmaj9": ([59, 64, 67, 74], 48),
        "Gadd9": ([59, 62, 69, 74], 43),
    }
    progression = ["Am9", "Am9", "Fmaj9", "Cmaj9", "Gadd9", "Am9", "Fmaj9", "Am9"]

    for bar, name in enumerate(progression):
        start = bar * 2.0
        notes, root = voicings[name]
        if bar == 0:
            place(keys, chord(notes, 2.2, 0.8), 0.0)
            continue
        if bar == 7:
            place(keys, chord(notes, 1.0, 0.8), start)
            place(bass, sub(midi_hz(root - 12), 0.9), start, 0.8)
            continue
        # E-piano comping: beat 1 long, the "and" of 2 short, beat 4 short
        place(keys, chord(notes, 1.2, 0.9), start)
        place(keys, chord(notes, 0.45, 0.55), start + 1.5 * BEAT)
        place(keys, chord(notes, 0.6, 0.6), start + 3 * BEAT)
        # Round sub bass: root, root, fifth
        place(bass, sub(midi_hz(root - 12), 0.9), start, 0.8)
        place(bass, sub(midi_hz(root - 12), 0.4), start + 1.5 * BEAT, 0.6)
        place(bass, sub(midi_hz(root - 5), 0.45), start + 3 * BEAT, 0.6)

    # Half-time drums from the drop (2 s) to 14 s
    k, s, sh = kick(), snap(), shaker()
    for bar in range(1, 7):
        start = bar * 2.0
        place(drums, k, start, 0.85)
        place(drums, k, start + 2.5 * BEAT, 0.6)
        place(drums, s, start + 2 * BEAT, 0.7)
        for step in range(8):
            swing = 0.035 if step % 2 else 0.0
            place(drums, sh, start + step * BEAT / 2 + swing, 0.5 if step % 2 else 0.8)

    # Sparse bell melody in A minor pentatonic
    melody = [(2.0, 76), (2.75, 79), (3.5, 81), (6.0, 79), (6.5, 76), (7.25, 74), (10.0, 76), (10.75, 79), (11.5, 84), (12.0, 81)]
    for at, m in melody:
        place(bells, bell(midi_hz(m)), at, 0.22)

    # Vinyl crackle
    crackle = np.zeros(n)
    pops = rng.integers(0, n, 140)
    crackle[pops] = rng.uniform(-1, 1, len(pops))
    crackle = spectral_filter(crackle, low=900, high=7000) * 0.6 + spectral_filter(rng.standard_normal(n), low=3000, high=9000) * 0.004

    # Gentle sidechain on the kicks keeps the low end clean
    duck = np.ones(n)
    for bar in range(1, 7):
        for off in (0, 2.5 * BEAT):
            i = int((bar * 2.0 + off) * SR)
            td = t_axis(0.35)
            duck[i : i + len(td)] = np.minimum(duck[i : i + len(td)], 1 - 0.35 * np.exp(-td * 12))

    keys_wet = reverb(keys, 2.4, 0.3, 2)
    mix = keys_wet * 0.9 * duck + bass * 0.75 * duck + drums * 0.8 + reverb(bells, 2.6, 0.5, 3) * 0.8 + crackle
    mix = spectral_filter(mix, low=28, high=11000)

    # Stereo: tremolo pans the e-piano gently left and right
    t = t_axis(DUR)
    pan = 0.5 + 0.18 * np.sin(2 * np.pi * t / (4 * BEAT))
    left = mix + keys_wet * 0.25 * (pan - 0.5)
    right = mix - keys_wet * 0.25 * (pan - 0.5)
    stereo = np.stack([left, right], axis=1)

    fade = np.minimum(t / 0.03, 1) * np.clip((DUR - t) / 1.0, 0, 1)
    stereo *= fade[:, None]
    stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.1)
    return stereo / np.max(np.abs(stereo)) * 0.89


# --- Sound effects -----------------------------------------------------------------

def make_whoosh() -> np.ndarray:
    """Soft silky swoosh for the colour-panel wipes."""
    seconds = 0.7
    t = t_axis(seconds)
    centers = 250 + 2600 * np.sin(np.pi * np.clip(t / seconds, 0, 1)) ** 2
    s = sweep_filter(rng.standard_normal(len(t)), centers, q=1.0)
    s = reverb(s * np.sin(np.pi * (t / seconds) ** 1.3) ** 2, 0.8, 0.3, 4)
    return s / np.max(np.abs(s)) * 0.8


def make_tink() -> np.ndarray:
    """A glass bottle touching down: bright inharmonic partials that ring briefly."""
    t = t_axis(1.4)
    s = np.zeros_like(t)
    for ratio, amp, decay in ((1.0, 1.0, 6), (2.32, 0.6, 9), (4.25, 0.35, 13), (6.63, 0.2, 18)):
        s += np.sin(2 * np.pi * 2350 * ratio * t) * amp * np.exp(-t * decay)
    click = spectral_filter(rng.standard_normal(len(t)), low=3000) * np.exp(-t * 400) * 0.3
    s = reverb(s + click, 1.2, 0.3, 7)
    return s / np.max(np.abs(s)) * 0.7


def make_spray() -> np.ndarray:
    """Perfume atomiser 'pssht': a pump click and a short hiss of mist."""
    t = t_axis(0.8)
    hiss = spectral_filter(rng.standard_normal(len(t)), low=3500, high=11000, order=3)
    env = np.minimum(t / 0.012, 1) * np.where(t < 0.28, 1.0, np.exp(-(t - 0.28) * 14))
    click = spectral_filter(rng.standard_normal(len(t)), low=800, high=4000) * np.exp(-t * 300) * 0.5
    s = reverb(hiss * env * 0.7 + click, 0.6, 0.2, 9)
    return s / np.max(np.abs(s)) * 0.65


def make_shimmer() -> np.ndarray:
    t = t_axis(2.2)
    s = np.zeros_like(t)
    for i, m in enumerate([81, 84, 88, 93, 96, 100]):
        start = i * 0.07
        tt = np.clip(t - start, 0, None)
        f = midi_hz(m)
        ring = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 3.5)
        s += np.where(t >= start, ring, 0) * (0.6 - i * 0.05)
    s = reverb(s, 2.0, 0.55, 6)
    return s / np.max(np.abs(s)) * 0.55


def make_swell() -> np.ndarray:
    """Airy rise into the drop: filtered noise and a soft chord that grow together."""
    seconds = 2.0
    t = t_axis(seconds)
    air = sweep_filter(rng.standard_normal(len(t)), 300 * (12 ** (t / seconds)), q=1.6)
    pad = sum(np.sin(2 * np.pi * midi_hz(m) * t) for m in (69, 72, 76, 79)) / 4
    s = (air / np.max(np.abs(air)) * 0.6 + pad * 0.5) * (t / seconds) ** 2.2
    s *= np.clip((seconds - t) / 0.03, 0, 1)
    s = reverb(s, 1.4, 0.3, 5)
    return s / np.max(np.abs(s)) * 0.6


def save(name: str, data: np.ndarray) -> None:
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for old in ("impact.wav", "pop.wav", "riser.wav"):
        (OUT / old).unlink(missing_ok=True)
    save("music.wav", make_music())
    save("whoosh.wav", make_whoosh())
    save("tink.wav", make_tink())
    save("spray.wav", make_spray())
    save("shimmer.wav", make_shimmer())
    save("swell.wav", make_swell())
    print("done")
