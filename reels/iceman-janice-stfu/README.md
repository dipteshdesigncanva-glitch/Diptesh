# ICEMAN // Janice STFU — 16:9 edit

25-second, 1920×1080 @ 30fps fan edit of Drake, *Janice STFU* (ICEMAN, 2026), in a poster-collage kinetic-type style: B&W halftone cutouts, one accent colour (ice blue), huge condensed type behind the subject, letter-by-letter captions, and a fixed HUD.

**Deliverable:** `ICEMAN_Janice-STFU_edit_16x9.mp4` (H.264 12 Mbps, AAC 256k).

## Beat map

The song runs at 125.8 BPM (1 beat = 0.477s). The edit uses the song from 41.945s, so the first big 808 drop lands on beat 8. Every cut, letter slam, flash and shake is placed in beats.

| Beats | Time | Scene |
|---|---|---|
| 0–4 | 0.0–1.9s | Rounded poster frame, crystal glove, `DRAKE` tag, `JANICE` typed on |
| 4–8 | 1.9–3.8s | Build: `S`·`T`·`F`·`U` per beat, noise riser, CRT-off drop gap |
| 8–11 | 3.8s | **Drop**: giant `ICE` behind the stage pose |
| 11–16 | | `SIX GOD` starburst badge, then the `O`·`V`·`O` 3-panel collage |
| 16–24 | | `TOO COLD FOR YOU` stack, `SUB ZERO` wide type with swoosh, `THE BOY` stadium seats |
| 24–32 | | Tilted `STFU`, `JANICE / STFU` chips, swirl `ICEMAN` (inverts on beat 30) |
| 32–40 | | Rapid montage: one poster per beat, half-beats at the end spelling `I·C·E·MAN` |
| 40–48 | | White `DRAKE` poster with mirrored type, then `ICE IN MY VEINS` with punch-in and strobe |
| 48–52.4 | 22.9–25s | ICEMAN logo end card, glitch out |

## Re-render

Requirements: Python 3 with `numpy` and `Pillow`, plus `ffmpeg`.

```bash
cd reels/iceman-janice-stfu
python3 scripts/audio.py "<path to Janice STFU audio>" audio.f32   # 25s cut + riser + drop gap
python3 scripts/reel.py video.mp4                                  # ~1.5 min on 4 cores
ffmpeg -i video.mp4 -f f32le -ar 44100 -ac 2 -i audio.f32 -map 0:v -map 1:a \
  -c:v libx264 -b:v 12M -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart out.mp4
```

Preview stills: `python3 scripts/reel.py stills/ 115,300,600` writes those frame numbers as JPGs.

The look is controlled by constants near the top of `scripts/reel.py`. `ICE` and `DEEP` set the accent colours (try `(200, 32, 90)` and `(100, 16, 50)` for the crimson look of the reference). Caption words live in each scene function and in the `RAPID` table.

The `assets/` folder holds treated cutouts made from the source photos. `scripts/cut.py` (rembg, BiRefNet-portrait) and `scripts/prep.py` regenerate them, and `scripts/analyze.py` is the beat and energy analysis used to choose the section.

Fonts: Anton and Unbounded (SIL Open Font License, see `fonts/`). The HUD uses Inter.
