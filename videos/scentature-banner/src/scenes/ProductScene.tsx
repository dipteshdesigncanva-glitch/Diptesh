import type React from "react";
import {
  Easing,
  Img,
  Interactive,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Arrow } from "../elements/Arrow";
import { Particles } from "../elements/Particles";
import { bodyFont, displayFont } from "../fonts";

type ProductSceneProps = {
  readonly plate: string;
  readonly line1: string;
  readonly line2: string;
  readonly tagline: string;
  readonly accent: string;
  readonly index: number;
  readonly total: number;
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Where the bottle sits in every plate (see scripts/prep_images.py)
const BOTTLE = {
  left: 1155,
  top: 405,
  width: 380,
  height: 495,
  cx: 1345,
  cy: 560,
};

const ProductSceneInner: React.FC<ProductSceneProps> = ({
  plate,
  line1,
  line2,
  tagline,
  accent,
  index,
  total,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const out = durationInFrames - 8;
  // The music is 120 BPM, so a beat lands every 15 frames from the first cut
  const beat = Math.exp(-(frame % 15) / 5);

  return (
    <>
      {/* Product photo with a punch-in on the cut, then a slow push */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: `${BOTTLE.cx}px ${BOTTLE.cy}px`,
          scale: interpolate(frame, [0, 14, durationInFrames], [1.3, 1, 1.07], {
            ...clamp,
            easing: ease,
          }),
          filter: `blur(${interpolate(frame, [0, 10], [14, 0], clamp)}px) brightness(${interpolate(
            frame,
            [0, 4, 14],
            [2.2, 1.35, 1],
            clamp,
          )})`,
        }}
      >
        <Img
          src={staticFile(plate)}
          style={{ position: "absolute", width: 1920, height: 1080 }}
        />

        {/* Glass shine that sweeps across the bottle */}
        <div
          style={{
            position: "absolute",
            left: BOTTLE.left,
            top: BOTTLE.top,
            width: BOTTLE.width,
            height: BOTTLE.height,
            borderRadius: 44,
            overflow: "hidden",
            mixBlendMode: "screen",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: -100,
              width: 140,
              height: BOTTLE.height + 200,
              rotate: "18deg",
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)",
              left: interpolate(frame, [16, 42], [-220, BOTTLE.width + 120], {
                ...clamp,
                easing: Easing.inOut(Easing.quad),
              }),
            }}
          />
        </div>
      </div>

      {/* Coloured glow that pulses on every beat */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          mixBlendMode: "screen",
          background: `radial-gradient(ellipse 520px 460px at ${BOTTLE.cx}px ${BOTTLE.cy + 60}px, ${accent} 0%, transparent 70%)`,
          opacity: 0.18 + 0.22 * beat,
        }}
      />

      {/* Darken the left side so the type reads clearly */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(90deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.55) 38%, rgba(0,0,0,0) 56%)",
        }}
      />

      <Particles name="Bokeh" color={accent} count={34} seed={line1} />

      {/* Copy block */}
      <div
        style={{
          position: "absolute",
          left: 130,
          top: 200,
          width: 860,
          translate: `${interpolate(frame, [out, durationInFrames], [0, -120], {
            ...clamp,
            easing: Easing.in(Easing.cubic),
          })}px 0`,
          opacity: interpolate(frame, [out, durationInFrames], [1, 0], clamp),
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 26,
            letterSpacing: 8,
            color: accent,
            opacity: interpolate(frame, [6, 18], [0, 1], clamp),
            translate: `${interpolate(frame, [6, 20], [-40, 0], { ...clamp, easing: ease })}px 0`,
          }}
        >
          <span>{String(index).padStart(2, "0")}</span>
          <span
            style={{
              height: 2,
              background: accent,
              width: interpolate(frame, [8, 26], [0, 90], {
                ...clamp,
                easing: ease,
              }),
            }}
          />
          <span style={{ color: "rgba(255,255,255,0.7)" }}>
            {String(total).padStart(2, "0")}
          </span>
        </div>

        {[line1, line2].map((line, i) => (
          <div key={line} style={{ overflow: "hidden", paddingTop: 6 }}>
            <div
              style={{
                fontFamily: displayFont,
                fontSize: 200,
                lineHeight: 0.98,
                textTransform: "uppercase",
                color: i === 0 ? "#ffffff" : accent,
                textShadow:
                  i === 1
                    ? `0 0 40px ${accent}88`
                    : "0 6px 30px rgba(0,0,0,0.5)",
                translate: `0 ${interpolate(
                  frame,
                  [8 + i * 5, 24 + i * 5],
                  [110, 0],
                  {
                    ...clamp,
                    easing: ease,
                  },
                )}%`,
                letterSpacing: interpolate(
                  frame,
                  [8 + i * 5, 34 + i * 5],
                  [24, 3],
                  {
                    ...clamp,
                    easing: ease,
                  },
                ),
              }}
            >
              {line}
            </div>
          </div>
        ))}

        <div
          style={{
            marginTop: 26,
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 30,
            letterSpacing: 9,
            color: "rgba(255,255,255,0.88)",
            opacity: interpolate(frame, [20, 32], [0, 1], clamp),
            translate: `0 ${interpolate(frame, [20, 34], [24, 0], { ...clamp, easing: ease })}px`,
          }}
        >
          {tagline}
        </div>

        <div
          style={{
            marginTop: 40,
            display: "flex",
            alignItems: "center",
            gap: 24,
            opacity: interpolate(frame, [26, 36], [0, 1], clamp),
            translate: `0 ${interpolate(frame, [26, 40], [24, 0], { ...clamp, easing: ease })}px`,
          }}
        >
          <div
            style={{
              fontFamily: bodyFont,
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: 4,
              color: "#111",
              background: accent,
              padding: "18px 36px",
              display: "flex",
              alignItems: "center",
              gap: 14,
              borderRadius: 999,
              boxShadow: `0 0 ${20 + 24 * beat}px ${accent}`,
              scale: interpolate(frame, [30, 40], [0.8, 1], {
                ...clamp,
                easing: Easing.out(Easing.back(2.2)),
              }),
            }}
          >
            {cta}
            <Arrow size={26} />
          </div>
          <div
            style={{
              fontFamily: bodyFont,
              fontWeight: 600,
              fontSize: 24,
              letterSpacing: 6,
              color: "rgba(255,255,255,0.75)",
              border: "1.5px solid rgba(255,255,255,0.35)",
              padding: "16px 28px",
              borderRadius: 999,
            }}
          >
            EAU DE PARFUM · 50ML
          </div>
        </div>
      </div>
    </>
  );
};

export const ProductScene = Interactive.create({
  Component: ProductSceneInner,
  layout: "absolute-fill",
  schema: {
    ...Interactive.backgroundSchema,
    line1: { type: "string", default: "BAD", description: "Name, first line" },
    line2: {
      type: "string",
      default: "GIRL",
      description: "Name, second line",
    },
    tagline: { type: "string", default: "", description: "Tagline" },
    accent: { type: "color", default: "#E08A3C", description: "Accent colour" },
    cta: { type: "string", default: "SHOP NOW", description: "Button text" },
  },
});
