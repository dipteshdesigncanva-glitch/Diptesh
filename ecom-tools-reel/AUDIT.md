# Audit: "3 Free E-com Tools" reel (v4 draft)

Source: `growthx_3-ecom-tools_reels_16x9_v4_draft.mp4`, 1920×1080, 30 fps, 39.0 s, Hinglish voiceover.
Rebuild: `index.html` (HyperFrames) → `renders/growthx_3-ecom-tools_16x9_replica.mp4`, using the original voiceover track.

## Concept and script

| Beat | Time | VO / on-screen copy |
| --- | --- | --- |
| Hook | 0.0–1.8 | "kya hi E-COMMERCE brand banaoge?" + tag "3 FREE E-COM TOOLS" |
| Stakes | 1.8–4.1 | "Agar yeh 3 EXTENSIONS hi use nahi ki?" + three icons |
| Promise | 4.1–7.3 | "kyunki yeh tools tumhe BEGINNER se PRO bana denge" + progress bar |
| Promise 2 | 7.3–10.8 | "aur tumhare COMPETITORS ka saara DATA tumhare saamne rakh denge" + bar chart |
| Tool 1 | 10.8–19.3 | "Pehla hai" Free Trendtrack Chrome Extension → best sellers, traffic source, theme |
| Tool 2 | 19.3–26.2 | "Doosra hai" E-Commerce Profit Calculator → profit margin before listing a product |
| Tool 3 | 26.2–31.3 | "Aur 3RD hai" winning-ads spy tool → spy on competitor ads |
| CTA | 31.3–36.3 | "in teeno TOOLS ka LINK chahiye? Toh comment karo 'TOOLS', link seedha aapke DM mein" |
| End card | 36.3–39.0 | GX logo, COMMENT "TOOLS", email, BUILD • GROW • SCALE |

The format holds up. A listicle of three free tools with a comment-to-DM keyword CTA is a proven lead-gen pattern for Reels. The text is synced to the voice word by word, a progress bar tracks the whole reel, and the brand look (black and violet, glow type) is consistent throughout.

## What's working

- **Clear structure.** Hook, then why it matters, then tools #1, #2 and #3, then the CTA. Each tool card is numbered, so viewers always know where they are.
- **Keyword CTA.** "Comment TOOLS" plus a mock comment box that types itself is a strong, low-friction ask, and comments feed the algorithm.
- **Calculator example is correct.** ₹1,199 − ₹450 − ₹260 = ₹489 profit. The numbers check out.
- **Progress bar.** It tells viewers how much is left, which helps watch time on a 39 s piece.
- **Brand presence without clutter.** A small logo pill sits top right, and the logo appears full size only at the end.

## Issues, ranked by impact

1. **Wrong aspect ratio for Reels (critical).** The file is 16:9 but is named and scripted as a Reel. On Instagram, YouTube Shorts and TikTok a 16:9 video plays letterboxed in a 9:16 frame, with the type about a third of its intended size. Every other fix matters less than this one. Re-lay it out at 1080×1920.
2. **Only one of the three tools is named (content).** #1 is "Trendtrack". #2 is just "E-Commerce Profit Calculator" and #3 is just "Winning-ads spy tool". Viewers can't search for them, and saves and shares depend on that. Name all three on screen. Comment-gating the links still works when the names are shown.
3. **"3 EXTENSIONS" contradicts the tools that follow (credibility).** Tool #2 is a calculator, not a browser extension. Say "3 TOOLS" in both the voice and the text, which also matches the CTA keyword.
4. **Placeholder boxes show before their content (polish).** At 19.3–20.7 s the calculator panel is an empty dark rectangle. At 21.9–25 s and 4.1–5.7 s an empty grey bar sits on screen. At 29.6 s the two "ad" cards are blank rectangles. These read as rendering glitches.
5. **Lines jump sideways as words arrive (polish).** Each line is re-centred whenever a word is added: "aur" appears at the left, then jumps when "tumhare" lands, and "kyunki", "Yeh competitors" and others do the same. That constant shifting makes the text harder to read.
6. **Final words flash by too fast (retention).** "kar sakte ho", "aapke DM mein", "banega" and "help" are on screen for only about 0.2–0.4 s before the next wipe. The CTA's key phrase "DM mein" gets about 0.3 s. Hold the last word around 0.5 s, or start the wipe after the word lands.
7. **Supporting text is too small for a phone.** "FREE · CHROME EXTENSION", "COST → PRICE → PROFIT", "SEE WHAT YOUR COMPETITORS RUN" and the calculator rows are roughly 14–18 px in a 1080p frame. After the 16:9 letterbox they can't be read.
8. **Emoji icons clash with the visual style.** 🧩 🧮 🔍 💬 ✉ render as system emoji in mismatched colours (green, rainbow, blue), which looks cheap against the violet glow look. Use matching line or gradient icons.
9. **Hook.** The opener is a rhetorical question with no visual payoff. Show the result (a winning-product dashboard or a ₹ profit figure) in the first second, and tease the CTA ("comment TOOLS for the links") early as well as at the end.
10. **No product UI anywhere.** It's all text on a dark background. Even 1–2 s of real screenshots or screen recordings per tool (the Trendtrack panel, the calculator, an ad library) would add proof and visual variety.
11. **The end card asks for email, not a follow.** For Reels a "Follow @handle" pays off more than an email address.
12. **Composition is crowded at the top.** Most scenes place text in the top 40% and leave the bottom half empty, so the frame feels unbalanced.

## What the rebuild changes

The rebuild keeps the original voiceover, script, timing (taken frame by frame from the reference), palette, diagonal wipe, rings, progress bar and logo. It also fixes the polish issues that don't need a new script:

- Every line is laid out in full from the first frame, so words fade in where they belong and nothing jumps (issue 5).
- Panels, meters and ad cards appear together with their content, so there are no empty placeholders. The ad cards now show mock ad content (issue 4).
- All emoji are replaced with matching SVG icons (issue 8).
- Card subtitles and calculator rows are about twice the original size (issue 7).
- Text blocks are centred vertically in the frame (issue 12).
- The original layout had no room for the full phrases, so the rebuild shows them: "bana denge", "ki?", "is tool ki help", "kar sakte ho", "chahiye?" and "aapke DM mein".

These are left for you to decide, because they change the content or the voiceover: issue 1 (9:16 layout), issues 2 and 3 (naming tools #2 and #3, "extensions" vs "tools"), issue 6 (it needs voiceover pauses), and issues 9–11.

## Rebuild files

- `index.html`: the whole composition. Each `[data-t]` attribute is the second at which that word or element appears, so retiming means editing one number.
- `audio.m4a`: the original voiceover, taken from the draft.
- `assets/img/`: the GX logo, cut from the draft's end card.
- `assets/fonts/`, `assets/vendor/`: Inter and GSAP, bundled locally so rendering needs no network.
- Re-render with `npx hyperframes render --quality delivery --output renders/out.mp4`.
