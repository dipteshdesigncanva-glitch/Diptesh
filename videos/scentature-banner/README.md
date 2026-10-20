# Scentature hero banner

A 15-second, 1920×1080 looping motion-graphics banner for the Scentature website, built with Remotion.

- **Timeline:** logo intro (0–2 s), Bad Girl, Floral Kiss, Hawas Classic and Hawas Ice (2.5 s each) with the bottle dropping in on a spring, then the collection line-up (12–15 s).
- **Audio:** the 120 BPM music and all sound effects are synthesized by `scripts/make_audio.py`, so there are no licensing issues. Every scene cut lands on a beat.
- **Images:** `scripts/prep_images.py` cuts each bottle out of its product photo (`public/bottles/`) and makes the white logo.
- **Look:** flat colour arches, outlined marquee type, spinning badges, sparkles, film grain and slanted colour-panel wipes. No glows. Fonts: Syne, Instrument Serif italic and Space Mono, bundled in `public/fonts/`.

## Commands

```bash
npm i
npm run dev                      # Remotion Studio preview
npx remotion render ScentatureBanner out/banner.mp4
python3 scripts/make_audio.py    # regenerate music and SFX
python3 scripts/prep_images.py <folder with 1.png 2.webp 3.webp 4.webp 5.webp>
```

To change the product names, taglines, colours or button text, edit the props in `src/ScentatureBanner.tsx`, or edit them in Studio.
