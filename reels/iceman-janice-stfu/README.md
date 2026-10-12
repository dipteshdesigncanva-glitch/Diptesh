# ICEMAN // Janice STFU — 16:9 edit

A 30-second, 1920×1080 @ 30fps fan edit of Drake, *Janice STFU* (ICEMAN, 2026). It mixes poster-collage kinetic type (B&W halftone cutouts, giant type behind the subject, an ice-blue accent) with phone-UI lyric-video moves (3D-tilted cards, zoom-blur tunnels, motion-blurred and arc-warped words), plus ice-cube and ice-shatter elements.

**Deliverable:** `ICEMAN_Janice-STFU_edit_v2_30s.mp4` (H.264 12 Mbps, AAC 256k). The earlier 25s v1 is in git history.

## Story / beat map

The song runs at 125.8 BPM (1 beat = 0.477s). The cut runs from 0:42.47 to 1:12.47 of the song, so the first 808 drop lands at 3.29s and the edit ends exactly on a bar line.

| Beats | Time | What happens |
|---|---|---|
| 1–8 | 0.0–3.3s | **Hook.** Caption "when janice texts you right before the drop 🙄". A 3D player card and chat swing in, Janice texts twice, the keys type `s·t·f·u` on the beat, and the sent bubble swells to fill the screen. Ice cracks spread across it in the pre-drop silence. |
| 8 | 3.3s | **Drop.** The screen shatters into flying shards, with the ice-shatter element exploding over it, and reveals ice-textured `ICE` behind the stage pose. |
| 11–16 | | `SIX GOD` starburst badge, then the `O·V·O` panels flipping in on 3D cards |
| 16–24 | | White-page kinetic captions `too cold 🥶 / for you.`, `SUB ZERO` with swoosh, `THE BOY` stadium seats |
| 24–32 | | Ice-textured tilted `STFU`, `JANICE / STFU` chips, swirl `ICEMAN` |
| 32–40 | | Rapid montage: one poster per beat, then `I·C·E·MAN` on half-beats |
| 40–48 | | White `DRAKE` poster with mirrored type, `ICE IN MY VEINS` |
| 48–52 | | Ice-cube backdrop, arc-warped `COLD AS`, giant `ICE` |
| 52–56 | | **Payoff:** Janice's contact card, *Block this Caller*, glowing `Blocked.` pill, Drake laughing |
| 56–64 | 26.7–30s | Second shatter into the Iceman logo with god rays. Janice's notification "u really blocked me?? 💀" drops in and is swiped away. Glitch out. |

Sound design is synthesized in `audio_v2.py`: message dings, key clicks, send whoosh and swell, ice crackle in the drop gap, and a glass/ice shatter on the drop and on the end card.

## Re-render

Requirements: Python 3 with `numpy` and `Pillow`, plus `ffmpeg`. The Inter and Noto Color Emoji system fonts are used for UI text.

```bash
cd reels/iceman-janice-stfu
python3 scripts/audio_v2.py "<path to Janice STFU audio>" audio.f32
python3 scripts/reel_v2.py video.mp4                     # ~3 min on 4 cores
ffmpeg -i video.mp4 -f f32le -ar 44100 -ac 2 -i audio.f32 -map 0:v -map 1:a \
  -c:v libx264 -b:v 12M -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart out.mp4
```

Preview stills: `python3 scripts/reel_v2.py stills/ 0,99,700` writes those frame numbers as JPGs.

The look is controlled by constants near the top of `scripts/reel_v2.py`. `ICE` and `DEEP` are the accent colours. Captions live in each scene function, in `RAPID`, `KIN` and `hook_caption()`. The chat lines are in `chat_panel()`.

## Files

- `scripts/reel_v2.py`, `scripts/audio_v2.py`: the v2 frame renderer and the audio cut with sound design.
- `scripts/reel.py`, `scripts/audio.py`: the v1 (25s) versions.
- `scripts/cut.py`, `scripts/prep.py`, `scripts/prep_v2.py`: rebuild the treated cutouts (rembg, BiRefNet-portrait) and the ice elements from the source photos.
- `scripts/analyze.py`: the beat and energy analysis used to choose the section.
- `assets/`: treated cutouts, the Iceman logo, the ice-cube backdrop and texture, the ice-shatter overlay, and the player-card art.
- `fonts/`: Anton and Unbounded (SIL Open Font License).
