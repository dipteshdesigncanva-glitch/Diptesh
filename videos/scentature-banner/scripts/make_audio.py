"""Synthesize the music bed and sound effects into public/audio/.

Everything is generated from scratch with numpy, so there are no licensing issues.
Usage: python3 scripts/make_audio.py

Music: 15 s, 120 BPM (one beat = 15 frames at 30 fps), A minor.
  0-2 s   intro pad + no drums (logo reveal)
  2-12 s  drop: four-on-the-floor kick, claps, hats, sub bass, pluck arp
  12-15 s outro: drums thin out, chord rings and fades for a clean loop
"""

from pathlib import Path

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = 15.0
OUT = Path(__file__).resolve().parent.parent / "public" / "audio"
rng = np.random.default_rng(7)


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
        bw = c / q
        gain = np.exp(-0.5 * ((f - c) / bw) ** 2)
        out[start : start + win] += np.fft.irfft(np.fft.rfft(seg) * gain, win) * window
        norm[start : start + win] += window**2
    out = out / np.maximum(norm, 1e-6)
    return out[win : win + len(x)]


def reverb(x: np.ndarray, seconds: float = 1.6, mix: float = 0.25, seed: int = 1) -> np.ndarray:
    r = np.random.default_rng(seed)
    t = t_axis(seconds)
    ir = r.standard_normal(len(t)) * np.exp(-t * 6.9 / seconds)
    ir = spectral_filter(ir, low=200, high=6000)
    ir /= np.sqrt(np.sum(ir**2))
    n = len(x) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)]
    return x * (1 - mix) + wet * mix * 2.2


def saw(freq: float, t: np.ndarray, harmonics: int = 18) -> np.ndarray:
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if freq * k > 9000:
            break
        out += np.sin(2 * np.pi * freq * k * t) / k
    return out


def place(buf: np.ndarray, sound: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    end = min(len(buf), i + len(sound))
    if i < len(buf):
        buf[i:end] += sound[: end - i] * gain


# --- Instruments -----------------------------------------------------------

def kick() -> np.ndarray:
    t = t_axis(0.45)
    freq = 42 + 110 * np.exp(-t * 28)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-t * 7.5)
    click = spectral_filter(rng.standard_normal(len(t)), low=1500, high=6000) * np.exp(-t * 180) * 0.25
    return np.tanh((body + click) * 1.6)


def clap() -> np.ndarray:
    t = t_axis(0.35)
    noise = spectral_filter(rng.standard_normal(len(t)), low=900, high=5500)
    env = np.zeros_like(t)
    for d in (0.0, 0.011, 0.022):
        env += np.where(t >= d, np.exp(-(t - d) * 60), 0)
    env += np.exp(-t * 14) * 0.35
    return noise * env * 0.5


def hat(open_: bool = False) -> np.ndarray:
    t = t_axis(0.3 if open_ else 0.07)
    noise = spectral_filter(rng.standard_normal(len(t)), low=7000, high=16000)
    return noise * np.exp(-t * (14 if open_ else 70)) * 0.35


def pluck(freq: float) -> np.ndarray:
    t = t_axis(0.6)
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return tone * np.exp(-t * 9) * np.minimum(t * 400, 1)


def pad_chord(notes: list[int], seconds: float) -> np.ndarray:
    t = t_axis(seconds)
    out = np.zeros_like(t)
    for m in notes:
        f = midi_hz(m)
        for cents in (-8, 0, 8):
            out += saw(f * 2 ** (cents / 1200), t + rng.random() * 0.01)
    out = spectral_filter(out, low=90, high=1400)
    env = np.minimum(t / 0.35, 1) * np.minimum((seconds - t) / 0.35, 1)
    return out * env / (len(notes) * 3)


# --- Music -------------------------------------------------------------------

def make_music() -> np.ndarray:
    n = int(DUR * SR)
    drums = np.zeros(n)
    bass = np.zeros(n)
    pads = np.zeros(n)
    arp = np.zeros(n)

    # Bars are 2 s. Am, Am, F, C, G, Am, F, Am
    progression = [
        (0, [57, 60, 64], 45),
        (2, [57, 60, 64], 45),
        (4, [53, 57, 60], 41),
        (6, [55, 60, 64], 48),
        (8, [55, 59, 62], 43),
        (10, [57, 60, 64], 45),
        (12, [53, 57, 60], 41),
        (14, [57, 60, 64], 45),
    ]

    for start, chord, root in progression:
        length = 2.6 if start < 14 else 1.0
        place(pads, pad_chord(chord + [chord[0] + 12], length), start)

        if 2 <= start < 14:
            # Sub bass on the off-beat 8ths, ducked under the kick
            for i in range(4):
                tb = t_axis(BEAT * 0.45)
                note = np.sin(2 * np.pi * midi_hz(root - 12) * tb)
                note = np.tanh(note * 1.8) * np.minimum(tb * 300, 1) * np.exp(-tb * 3)
                place(bass, note, start + i * BEAT + BEAT / 2, 0.55)

            # 16th-note pluck arpeggio
            pattern = [0, 2, 1, 3, 2, 1, 3, 2]
            arp_notes = [m + 12 for m in chord] + [chord[0] + 24]
            for i in range(16):
                if start >= 12 and i >= 8:
                    break
                note = arp_notes[pattern[i % 8]]
                place(arp, pluck(midi_hz(note)), start + i * BEAT / 4, 0.18 if i % 4 else 0.26)

    k, c, h, oh = kick(), clap(), hat(), hat(True)
    beats = int(DUR / BEAT)
    for b in range(beats):
        at = b * BEAT
        if 2 <= at < 14:
            place(drums, k, at, 0.9)
            if b % 2 == 1:
                place(drums, c, at, 0.55)
            place(drums, h if b % 4 != 3 else oh, at + BEAT / 2, 0.5)
            if at >= 4:
                place(drums, h, at + BEAT / 4, 0.18)
                place(drums, h, at + 3 * BEAT / 4, 0.18)
        if 1.0 <= at < 2 and b % 1 == 0:
            # Clap roll building into the drop
            for s in range(4):
                place(drums, c, at + s * BEAT / 4, 0.12 + 0.08 * s)

    # Sidechain: duck pads and bass on every kick in the drop
    duck = np.ones(n)
    for b in range(beats):
        at = b * BEAT
        if 2 <= at < 14:
            i = int(at * SR)
            td = t_axis(BEAT)
            env = 1 - 0.65 * np.exp(-td * 9)
            duck[i : i + len(env)] = env[: n - i]
    pads *= duck
    bass *= duck

    # Dotted-8th echo on the arp
    delay = int(BEAT * 0.75 * SR)
    echoed = arp.copy()
    echoed[delay:] += arp[:-delay] * 0.35
    echoed[2 * delay :] += arp[: -2 * delay] * 0.15

    mix = drums * 0.95 + bass * 0.9 + reverb(pads, 2.2, 0.35, 2) * 0.55 + reverb(echoed, 1.4, 0.3, 3) * 0.6
    stereo = np.stack([mix, mix], axis=1)
    # Slight stereo width on pads and arp
    width = reverb(pads + echoed, 0.9, 1.0, 9) * 0.12
    stereo[:, 0] += width
    stereo[:, 1] -= width

    t = t_axis(DUR)
    fade = np.minimum(t / 0.05, 1) * np.clip((DUR - t) / 1.2, 0, 1)
    stereo *= fade[:, None]
    stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.2)
    return stereo / np.max(np.abs(stereo)) * 0.89


# --- Sound effects -------------------------------------------------------------

def make_whoosh() -> np.ndarray:
    seconds = 0.7
    t = t_axis(seconds)
    noise = rng.standard_normal(len(t))
    centers = 300 + 4200 * np.sin(np.pi * np.clip(t / seconds, 0, 1)) ** 2
    s = sweep_filter(noise, centers, q=1.2)
    env = np.sin(np.pi * (t / seconds) ** 1.3) ** 2
    s = reverb(s * env, 0.8, 0.3, 4)
    return s / np.max(np.abs(s)) * 0.8


def make_impact() -> np.ndarray:
    t = t_axis(1.8)
    freq = 28 + 70 * np.exp(-t * 12)
    boom = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 3.2)
    crack = spectral_filter(rng.standard_normal(len(t)), low=300, high=5000) * np.exp(-t * 25) * 0.6
    s = reverb(np.tanh((boom + crack) * 2.0), 1.6, 0.3, 5)
    return s / np.max(np.abs(s)) * 0.9


def make_shimmer() -> np.ndarray:
    t = t_axis(2.2)
    s = np.zeros_like(t)
    notes = [81, 84, 88, 93, 96, 100, 105]
    for i, m in enumerate(notes):
        start = i * 0.06
        tt = np.clip(t - start, 0, None)
        f = midi_hz(m)
        bell = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 3.5)
        s += np.where(t >= start, bell, 0) * (0.6 - i * 0.05)
    s = reverb(s, 2.0, 0.55, 6)
    return s / np.max(np.abs(s)) * 0.6


def make_riser() -> np.ndarray:
    seconds = 2.0
    t = t_axis(seconds)
    noise = rng.standard_normal(len(t))
    centers = 200 * (40 ** (t / seconds))
    s = sweep_filter(noise, centers, q=2.0) * (t / seconds) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(110 * 4 ** (t / seconds)) / SR) * (t / seconds) ** 3 * 0.25
    s = s / np.max(np.abs(s)) + tone
    s *= np.clip((seconds - t) / 0.02, 0, 1)
    return s / np.max(np.abs(s)) * 0.7


def save(name: str, data: np.ndarray) -> None:
    import wave

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
    save("music.wav", make_music())
    save("whoosh.wav", make_whoosh())
    save("impact.wav", make_impact())
    save("shimmer.wav", make_shimmer())
    save("riser.wav", make_riser())
    print("done")
