# Scentature hero banner

A 15-second looping motion-graphics video for Scentature, built with Remotion, in two formats from one timeline:

- `ScentatureBanner`: 1920×1080 (16:9) website hero banner
- `ScentatureReel`: 1080×1920 (9:16) for Reels, Shorts and Stories. Each scene reads the frame size and switches to a stacked layout.

- **Timeline:** logo intro (0–2 s), Bad Girl, Floral Kiss, Hawas Classic and Hawas Ice (2.5 s each) with the bottle dropping in on a spring, then the collection line-up (12–15 s).
- **Audio:** smooth R&B-style music (electric piano, sub bass, half-time drums, bells) plus whoosh, glass-clink, perfume-spray, shimmer and swell sound effects, all synthesized by `scripts/make_audio.py`, so there are no licensing issues. Every scene cut lands on a beat.
- **Images:** `scripts/prep_images.py` cuts each bottle out of its product photo (`public/bottles/`) and makes the white logo.
- **Look:** flat colour arches, themed floating shapes (drops, petals, leaves, ice), dashed rings, a dot grid, spray mist, a swinging ₹549 price tag, outlined marquee type, sparkles, film grain and slanted colour-panel wipes. No glows.
- **Fonts:** Playfair Display (names, taglines) and Poppins (prices, labels, buttons; its Devanagari file supplies the ₹ sign), bundled in `public/fonts/`.

## Commands

```bash
npm i
npm run dev                      # Remotion Studio preview
npx remotion render ScentatureBanner out/banner.mp4
npx remotion render ScentatureReel out/reel.mp4
python3 scripts/make_audio.py    # regenerate music and SFX
python3 scripts/prep_images.py <folder with 1.png 2.webp 3.webp 4.webp 5.webp>
```

To change the product names, taglines, colours or button text, edit the props in `src/ScentatureBanner.tsx`, or edit them in Studio.
