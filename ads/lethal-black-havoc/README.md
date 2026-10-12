# LETHAL BLACK HAVOC — 25s ad (9:16)

A spec ad for the **LETHAL BLACK HAVOC** 75% wireless mechanical keyboard (₹6,449). It is built entirely from a screen recording of the brand's product page, plus a synthesized soundtrack and an AI creator voiceover. All claims and numbers come from the product page.

| Version | File | Notes |
|---|---|---|
| **v2 (current)** | `HAVOC_ad_v2_9x16_25s_60fps.mp4` | On-brand redesign: 1080×1920 @ 60fps, H.264 14 Mbps, AAC 256k, −14 LUFS, exactly 25.0s |
| v1 | `HAVOC_UGC_ad_9x16_25s.mp4` | First cut: 30fps phonk/trap edit (kept for comparison) |

## v2: brand system

v1 was generic, so v2 is rebuilt around LETHAL BLACK's own site design:

- **Colour:** brand crimson `#BC002E` (sampled from the site) on a charcoal gradient. The panther emblem appears as a faint watermark.
- **Type:** Montserrat 900 for headlines and Montserrat 300 for the light "experience" lines. Eyebrows are crimson and letter-spaced with side rules. Small copy is set in Inter.
- **UI elements:**
  - black cards with crimson borders
  - crimson leader lines with square nodes, matching the product page's switch diagram
  - crimson pills and buttons
- **Grid:** everything is centred on x = 540, with fixed rows:

  | Element | Position |
  |---|---|
  | Eyebrow | y = 290 |
  | Headline | from y = 412 |
  | Product zone | y ≈ 600–1320 |
  | Captions | y = 1450 |

  Nothing important sits in the top 250 px or bottom 400 px, which platform UI covers.

## v2: motion

Everything renders at 60fps. Every frame is a pure function of time, so motion is sub-pixel smooth.

- **Text:** eased line-mask reveals. Lines rise into their box and leave through the top. In-scene swaps use a "text roll": gasket → hot-swap, LED → RGB, CTA → end lockup.
- **Scene changes:** velocity-matched slide handoffs. The old scene accelerates up and out, and the new one arrives already moving at the same speed. Fast layers get vertical motion blur, so text never double-exposes.
- **Other transitions:**
  - a zoom-through into the display section
  - a crimson brand sweep on the drop and on the gaming section, which glides in, holds on the logo, then glides out
- **No** shakes, flashes or glitch effects.
- **Captions:** word-by-word in Montserrat 800, with a crimson pill that glides from word to word. Upcoming words wait at 50% opacity. Word groups never stack.
- **Timing:** every UI pop sits on the 16th-note grid shared with the soundtrack (`EV` in `ugc_ad2.py`). This covers callouts, chips, stat cards, the star rating, perks and the CTA tap.

| Time | Scene | Voiceover |
|---|---|---|
| 0.0–2.4s | **Hook:** SOUND ON pill. The RGB board lights up under a slow dolly-out, with a key glow on every thock. | "This keyboard has no business sounding this good." |
| 2.0–2.7s | Crimson brand sweep with the LETHAL BLACK logo, on the drop | — |
| 2.4–4.3s | **Reveal:** logo, HAVOC wordmark wipe with light sweep, 3D board | "Meet the Havoc, by Lethal Black." |
| 4.3–6.3s | **VENOM linear switch:** exploded parts with callouts (lets the RGB through, 2.0mm pre-travel, 45gf, 5-pin · 50M keystrokes) | "Pre-lubed Venom switches." |
| 6.3–8.2s | **5-layer dampening:** exploded-layer footage settles while a crimson waveform flattens; FOAM, SWITCH FILMS and SILICONE chips | "Five layers of sound dampening." |
| 8.2–10.1s | **Gasket mounted** (pulsing gasket points), then rolls to **hot-swap**, 3 & 5-pin | "Gasket mounted." / "Hot-swappable." |
| 10.1–12.0s | **Doubleshot PBT:** "Legends that never wear off", with molded-in legend and thicker-walls callouts | "Doubleshot PBT keycaps." |
| 12.0–14.9s | **Built without compromise:** counting cards for 4000 mAh, 1000 Hz, BT 5.0 (2.4G · wired · 3 devices) and 75% | "Tri-mode wireless, with thousand hertz polling." |
| 14.9–17.8s | Zoom-through to the LED display ("Own your identity"), then RGB "Light it your way". The music breaks down here. | — |
| 17.8–19.7s | Second sweep; **built for competitive gaming:** gameplay card, LETHAL TAP · last-input priority | "Built for competitive gaming." |
| 19.7–22.6s | **₹6,449** with light sweep; 4.68★ (with a partial fifth star) · 325 reviews; 18-month warranty, free delivery (India), 7-day replacement, EMI from ₹227/mo | "All this, for just sixty-four forty-nine." |
| 22.6–25.0s | **GRAB YOURS:** SHOP NOW button with a tap ripple clipped to the pill, lethalblack.com. Then the end lockup: logo, HAVOC, "Built without compromise". | "Hit the link, and grab yours." |

## v2: sound

`ugc_audio2.py` generates everything. There are no third-party samples.

- **Track:** a premium-tech track at 124.8 BPM, so 52 beats make exactly 25s.
  - Fm9 – D♭maj7 – A♭maj7 – E♭ pads, sub bass, and a pluck arp with ping-pong delay.
  - Sidechain pump throughout. Bar 8 is a breakdown with a clap build into the gaming section, and bar 12 is the final hit.
- **SFX:**
  - keyboard thocks synced to the hook glows
  - soft whooshes on every transition, and boom + shimmer on the brand sweeps
  - UI ticks on each callout, chip and card
  - counter ticks that thin out as the numbers settle
  - a star chime, and a CTA tap click with a confirm chime
- **Voice:** Kokoro TTS (offline, voice `af_heart`), generated by `vo.py`. Music ducks under the voice.
- **Master:** −14 LUFS integrated (BS.1770 meter), true peak ≤ −1.5 dBTP. This comes from a 4× oversampled look-ahead limiter.

## Re-render

```bash
./extract_clips.sh path/to/recording.mp4        # frames + clips, with the mouse cursor painted out
python3 ugc_audio2.py vo out_audio2.f32          # v2 soundtrack + VO, mastered
python3 ugc_ad2.py video2.mp4                    # 1500 frames @ 60fps, ~4 min on 4 cores
ffmpeg -i video2.mp4 -f f32le -ar 44100 -ac 2 -i out_audio2.f32 -map 0:v -map 1:a \
  -c:v libx264 -preset slow -b:v 14M -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart ad_v2.mp4
```

The delivered file used a two-pass 14 Mbps encode.

- **Preview stills:** `python3 ugc_ad2.py stills/ 0,144,336` writes those frame numbers (at 60fps) as JPGs.
- **v1:** re-render with `ugc_audio.py` and `ugc_ad.py` the same way, at 30fps and 12 Mbps.

`assets/` already holds the cutouts and mattes. To rebuild them, run `prep_ugc.py` (rembg isnet) and then `prep_ugc2.py` (luminance mattes with hole-fill). The voiceover lines live in `vo.py`. Their placements are `VO_AT` in the ad and audio scripts, which must match.

Requirements:
- Python 3 with `numpy`, `Pillow` and `scipy` (v2 mastering), plus `ffmpeg`.
- Re-cutting assets also needs `rembg`, and regenerating the voiceover needs `kokoro-onnx`.
- Fonts: Montserrat and Anton are SIL OFL and are in `fonts/`. The Inter system font is also used, and v1 additionally uses Noto Color Emoji.
