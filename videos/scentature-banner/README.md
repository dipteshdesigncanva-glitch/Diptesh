# Scentature hero banner

A 15-second, 1920×1080 looping motion-graphics banner for the Scentature website, built with Remotion.

- **Timeline:** logo intro (0–2 s), Bad Girl, Floral Kiss, Hawas Classic and Hawas Ice (2.5 s each), then the collection line-up (12–15 s).
- **Audio:** the 120 BPM music and all sound effects are synthesized by `scripts/make_audio.py`, so there are no licensing issues. Every scene cut lands on a beat.
- **Images:** `scripts/prep_images.py` builds the wide plates, bottle cards and white logo in `public/` from the original product photos.

## Commands

```bash
npm i
npm run dev                      # Remotion Studio preview
npx remotion render ScentatureBanner out/banner.mp4
python3 scripts/make_audio.py    # regenerate music and SFX
python3 scripts/prep_images.py <folder with 1.png 2.webp 3.webp 4.webp 5.webp>
```

To change the product names, taglines, colours or button text, edit the props in `src/ScentatureBanner.tsx`, or edit them in Studio.
