import type React from "react";
import {
  Easing,
  Img,
  Interactive,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Arrow } from "../elements/Arrow";
import { FloatingShapes } from "../elements/FloatingShapes";
import { Grain } from "../elements/Grain";
import { Marquee } from "../elements/Marquee";
import { Sparkle } from "../elements/Sparkle";
import { bodyFont, displayFont } from "../fonts";

type OutroSceneProps = {
  readonly headline: string;
  readonly price: string;
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const ARCH_W = 290;
const GAP = 50;
const ROW_LEFT = (1920 - (ARCH_W * 4 + GAP * 3)) / 2;
const ARCH_TOP = 330;
const BASE = 790;
const BOTTLE_H = 400;
const BOTTLE_W = (493 / 892) * BOTTLE_H;

const lineUp = [
  { src: "bottles/bad-girl.png", accent: "#E07A2E" },
  { src: "bottles/floral-kiss.png", accent: "#FF2E7E" },
  { src: "bottles/hawas-classic.png", accent: "#22C55E" },
  { src: "bottles/hawas-ice.png", accent: "#3B6BFF" },
];

const OutroSceneInner: React.FC<OutroSceneProps> = ({
  headline,
  price,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const beat = Math.exp(-(frame % 15) / 4);

  return (
    <>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(180deg, #0A0A0A 0%, #141018 100%)",
        }}
      />
      <FloatingShapes
        name="Shapes"
        shape="mixed"
        color="#F3E6CF"
        count={14}
        seed="outro"
        depth="back"
        xMin={20}
        xMax={270}
      />
      <FloatingShapes
        name="Shapes right"
        shape="mixed"
        color="#F3E6CF"
        count={14}
        seed="outro-r"
        depth="back"
        xMin={1650}
        xMax={1900}
      />

      <Img
        src={staticFile("logo-white.png")}
        style={{
          position: "absolute",
          left: (1920 - 380) / 2,
          top: 46,
          width: 380,
          clipPath: `inset(0 ${interpolate(frame, [0, 16], [100, 0], { ...clamp, easing: Easing.inOut(Easing.cubic) })}% 0 0)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 196,
          width: "100%",
          textAlign: "center",
          fontFamily: displayFont,
          fontStyle: "italic",
          fontWeight: 500,
          fontSize: 58,
          color: "#ffffff",
          opacity: interpolate(frame, [6, 16], [0, 1], clamp),
          translate: `0 ${interpolate(frame, [6, 20], [24, 0], { ...clamp, easing: ease })}px`,
        }}
      >
        {headline}{" "}
        <span
          style={{
            fontFamily: bodyFont,
            fontStyle: "normal",
            fontWeight: 700,
            color: "#F3C96B",
          }}
        >
          {price}
        </span>
      </div>

      {lineUp.map((item, i) => {
        const left = ROW_LEFT + i * (ARCH_W + GAP);
        const drop = spring({
          frame: frame - 8 - i * 4,
          fps,
          config: { damping: 11, stiffness: 150 },
        });
        return (
          <div key={item.src}>
            <div
              style={{
                position: "absolute",
                left,
                top: ARCH_TOP,
                width: ARCH_W,
                height: BASE - ARCH_TOP + 40,
                borderRadius: `${ARCH_W / 2}px ${ARCH_W / 2}px 0 0`,
                background: item.accent,
                translate: `0 ${interpolate(frame, [2 + i * 3, 18 + i * 3], [700, 0], { ...clamp, easing: ease })}px`,
              }}
            />
            <Img
              src={staticFile(item.src)}
              style={{
                position: "absolute",
                left: left + (ARCH_W - BOTTLE_W) / 2,
                top: BASE - BOTTLE_H,
                width: BOTTLE_W,
                height: BOTTLE_H,
                transformOrigin: "50% 100%",
                translate: `0 ${Math.min(0, interpolate(drop, [0, 1], [-1000, 0])) - Math.abs(Math.sin((frame + i * 7) / 10)) * 8}px`,
                scale: `${1 + Math.max(0, drop - 1) * 0.3} ${1 - Math.max(0, drop - 1) * 0.6}`,
                rotate: `${interpolate(drop, [0, 1], [i % 2 ? 16 : -16, 0])}deg`,
              }}
            />
          </div>
        );
      })}

      {/* Strip of scent names rolling along the base */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: BASE + 40,
          width: 1920,
          height: 60,
          background: "#F3E6CF",
        }}
      />
      <Marquee
        name="Names strip"
        text="BAD GIRL  •  FLORAL KISS  •  HAWAS CLASSIC  •  HAWAS ICE  •  ₹299 EACH  •  "
        fontFamily={bodyFont}
        fontSize={24}
        color="#151515"
        outline={false}
        speed={6}
        style={{ top: BASE + 58, fontWeight: 600, letterSpacing: 3 }}
      />

      <Sparkle
        name="Sparkle 1"
        size={60}
        color="#ffffff"
        delay={24}
        style={{ left: ROW_LEFT - 80, top: 330 }}
      />
      <Sparkle
        name="Sparkle 2"
        size={36}
        color="#F3C96B"
        delay={30}
        style={{ left: 1920 - ROW_LEFT + 30, top: 420 }}
      />

      <div
        style={{
          position: "absolute",
          top: 930,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 26,
            letterSpacing: 3,
            color: "#111111",
            background: "#ffffff",
            padding: "20px 46px",
            borderRadius: 999,
            scale: interpolate(frame, [30, 42], [0, 1], {
              ...clamp,
              easing: Easing.out(Easing.back(2)),
            }),
          }}
        >
          {cta}
          <span style={{ display: "flex", translate: `${beat * 8}px 0` }}>
            <Arrow size={28} />
          </span>
        </div>
      </div>

      <Grain opacity={0.2} />

      {/* Fade to black so the banner loops cleanly back into the intro */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "#000",
          opacity: interpolate(
            frame,
            [durationInFrames - 14, durationInFrames - 1],
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
    headline: {
      type: "string",
      default: "Four signature scents, each",
      description: "Headline",
    },
    price: { type: "string", default: "₹299", description: "Price" },
    cta: {
      type: "string",
      default: "SHOP THE COLLECTION",
      description: "Button text",
    },
  },
});
