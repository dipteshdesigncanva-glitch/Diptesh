"""Generate the creator voiceover line by line with Kokoro (offline) and report durations."""
import json
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

TTS = sys.argv[1]  # dir with kokoro-v1.0.onnx + voices-v1.0.bin
OUT = sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
SPEED = float(sys.argv[4]) if len(sys.argv) > 4 else 1.12

LINES = [
    ("hook", "This keyboard has no business sounding this good."),
    ("meet", "Meet the Havoc, by Lethal Black."),
    ("venom", "Pre-lubed Venom switches."),
    ("layers", "Five layers of sound dampening."),
    ("gasket", "Gasket mounted."),
    ("swap", "Hot-swappable."),
    ("pbt", "Doubleshot PBT keycaps."),
    ("specs", "Tri-mode wireless, with thousand hertz polling."),
    ("gaming", "Built for competitive gaming."),
    ("rating", "Rated four point six eight stars."),
    ("price", "All this, for just sixty-four forty-nine."),
    ("cta", "Hit the link, and grab yours."),
]

k = Kokoro(f"{TTS}/kokoro-v1.0.onnx", f"{TTS}/voices-v1.0.bin")
meta = {}
for key, text in LINES:
    audio, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
    a = np.asarray(audio, np.float32)
    # trim leading/trailing silence
    env = np.abs(a)
    idx = np.where(env > 0.01)[0]
    a = a[max(0, idx[0] - int(0.01 * sr)): idx[-1] + int(0.04 * sr)]
    sf.write(f"{OUT}/{key}.wav", a, sr)
    meta[key] = dict(text=text, dur=round(len(a) / sr, 3), sr=sr)
    print(f"{key:8s} {len(a) / sr:5.2f}s  {text}")
json.dump(meta, open(f"{OUT}/vo.json", "w"), indent=1)
print("total", round(sum(m["dur"] for m in meta.values()), 2))
