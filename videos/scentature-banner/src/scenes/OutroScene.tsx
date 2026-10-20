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
import { bodyFont } from "../fonts";

type OutroSceneProps = {
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const CARD_W = 300;
const CARD_H = 548;
const GAP = 48;
const ROW_LEFT = (1920 - (CARD_W * 4 + GAP * 3)) / 2;

const cards = [
  { src: "cards/bad-girl.jpg", accent: "#E08A3C" },
  { src: "cards/floral-kiss.jpg", accent: "#FF2E7E" },
  { src: "cards/hawas-classic.jpg", accent: "#2BD960" },
  { src: "cards/hawas-ice.jpg", accent: "#4D7CFF" },
];

const OutroSceneInner: React.FC<OutroSceneProps> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const beat = Math.exp(-(frame % 15) / 5);

  return (
    <>
      {/* A glow in each bottle's colour behind its card */}
      {cards.map((card, i) => (
        <div
          key={card.src}
          style={{
            position: "absolute",
            left: ROW_LEFT + i * (CARD_W + GAP) - 160,
            top: 300,
            width: CARD_W + 320,
            height: 520,
            background: `radial-gradient(ellipse at center, ${card.accent} 0%, transparent 65%)`,
            filter: "blur(30px)",
            opacity:
              (0.35 + 0.2 * beat) *
              interpolate(frame, [4 + i * 4, 24 + i * 4], [0, 1], clamp),
          }}
        />
      ))}
      <Particles name="Gold dust" color="#F3D9A4" count={36} seed="outro" />

      <Img
        src={staticFile("logo-white.png")}
        style={{
          position: "absolute",
          left: (1920 - 460) / 2,
          top: 64,
          width: 460,
          filter: "drop-shadow(0 0 20px rgba(255,255,255,0.35))",
          opacity: interpolate(frame, [0, 14], [0, 1], clamp),
          translate: `0 ${interpolate(frame, [0, 18], [-30, 0], { ...clamp, easing: ease })}px`,
        }}
      />

      {cards.map((card, i) => (
        <div
          key={card.src}
          style={{
            position: "absolute",
            left: ROW_LEFT + i * (CARD_W + GAP),
            top: 262,
            width: CARD_W,
            height: CARD_H,
            borderRadius: 24,
            overflow: "hidden",
            border: "1.5px solid rgba(255,255,255,0.16)",
            boxShadow: `0 30px 80px rgba(0,0,0,0.6), 0 0 40px ${card.accent}55`,
            opacity: interpolate(frame, [4 + i * 4, 16 + i * 4], [0, 1], clamp),
            translate: `0 ${
              interpolate(frame, [4 + i * 4, 26 + i * 4], [160, 0], {
                ...clamp,
                easing: ease,
              }) +
              Math.sin((frame + i * 9) / 14) * 6
            }px`,
            rotate: `${interpolate(
              frame,
              [4 + i * 4, 26 + i * 4],
              [(i - 1.5) * 6, 0],
              {
                ...clamp,
                easing: ease,
              },
            )}deg`,
          }}
        >
          <Img
            src={staticFile(card.src)}
            style={{ width: CARD_W, height: CARD_H, objectFit: "cover" }}
          />
          {/* Shine that runs across the whole line-up */}
          <div
            style={{
              position: "absolute",
              top: -80,
              width: 120,
              height: CARD_H + 160,
              rotate: "16deg",
              mixBlendMode: "screen",
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
              left: interpolate(
                frame,
                [36 + i * 3, 56 + i * 3],
                [-200, CARD_W + 120],
                clamp,
              ),
            }}
          />
        </div>
      ))}

      <div
        style={{
          position: "absolute",
          top: 868,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          opacity: interpolate(frame, [28, 38], [0, 1], clamp),
        }}
      >
        <div
          style={{
            fontFamily: bodyFont,
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: 6,
            color: "#111",
            background: "linear-gradient(90deg, #F3D9A4, #ffffff, #F3D9A4)",
            padding: "22px 54px",
            display: "flex",
            alignItems: "center",
            gap: 14,
            borderRadius: 999,
            boxShadow: `0 0 ${18 + 26 * beat}px rgba(243,217,164,0.8)`,
            scale: interpolate(frame, [28, 40], [0.7, 1], {
              ...clamp,
              easing: Easing.out(Easing.back(2)),
            }),
          }}
        >
          {cta}
          <Arrow size={30} />
        </div>
      </div>

      {/* Fade to black so the banner loops cleanly back into the intro */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "#000",
          opacity: interpolate(
            frame,
            [durationInFrames - 16, durationInFrames - 1],
            [0, 1],
            clamp,
          ),
        }}
      />
    </>
  );
};

export const OutroScene = Interactive.create({
  Component: OutroSceneInner,
  layout: "absolute-fill",
  schema: {
    ...Interactive.backgroundSchema,
    cta: {
      type: "string",
      default: "SHOP THE COLLECTION",
      description: "Button text",
    },
  },
});
