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

const BOTTLE_H = 400;
const BOTTLE_W = (493 / 892) * BOTTLE_H;

// 16:9 puts the four arches in a row; 9:16 stacks them in a 2x2 grid
const LANDSCAPE = {
  archW: 290,
  gap: 50,
  columns: 4,
  rowLeft: (1920 - (290 * 4 + 50 * 3)) / 2,
  archTop: 330,
  rowStep: 0,
  logo: { width: 380, top: 46 },
  headline: { top: 196, size: 58 },
  ctaTop: 930,
  ctaSize: 26,
  sides: [
    { xMin: 20, xMax: 270 },
    { xMin: 1650, xMax: 1900 },
  ],
};

const PORTRAIT = {
  archW: 380,
  gap: 60,
  columns: 2,
  rowLeft: (1080 - (380 * 2 + 60)) / 2,
  archTop: 600,
  rowStep: 540,
  logo: { width: 520, top: 130 },
  headline: { top: 350, size: 66 },
  ctaTop: 1760,
  ctaSize: 30,
  sides: [
    { xMin: 0, xMax: 90 },
    { xMin: 990, xMax: 1060 },
  ],
};

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
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const L = height > width ? PORTRAIT : LANDSCAPE;
  const ARCH_W = L.archW;
  const ROW_LEFT = L.rowLeft;
  // Bottles stand 460px below the top of their arch
  const lastBase = L.archTop + L.rowStep * (4 / L.columns - 1) + 460;
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
        {...L.sides[0]}
      />
      <FloatingShapes
        name="Shapes right"
        shape="mixed"
        color="#F3E6CF"
        count={14}
        seed="outro-r"
        depth="back"
        {...L.sides[1]}
      />

      <Img
        src={staticFile("logo-white.png")}
        style={{
          position: "absolute",
          left: (width - L.logo.width) / 2,
          top: L.logo.top,
          width: L.logo.width,
          clipPath: `inset(0 ${interpolate(frame, [0, 16], [100, 0], { ...clamp, easing: Easing.inOut(Easing.cubic) })}% 0 0)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: L.headline.top,
          left: (width - 900) / 2,
          width: 900,
          textAlign: "center",
          fontFamily: displayFont,
          fontStyle: "italic",
          fontWeight: 500,
          fontSize: L.headline.size,
          lineHeight: 1.2,
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
        const col = i % L.columns;
        const row = Math.floor(i / L.columns);
        const left = ROW_LEFT + col * (ARCH_W + L.gap);
        const ARCH_TOP = L.archTop + row * L.rowStep;
        const BASE = ARCH_TOP + 460;
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
                translate: `0 ${interpolate(frame, [2 + i * 3, 18 + i * 3], [height - ARCH_TOP, 0], { ...clamp, easing: ease })}px`,
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
                translate: `0 ${Math.min(0, interpolate(drop, [0, 1], [-(BASE + 200), 0])) - Math.abs(Math.sin((frame + i * 7) / 10)) * 8}px`,
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
          top: lastBase + 40,
          width,
          height: 60,
          background: "#F3E6CF",
        }}
      />
      <Marquee
        name="Names strip"
        text="BAD GIRL  •  FLORAL KISS  •  HAWAS CLASSIC  •  HAWAS ICE  •  ₹549 EACH  •  "
        fontFamily={bodyFont}
        fontSize={24}
        color="#151515"
        outline={false}
        speed={6}
        style={{ top: lastBase + 58, fontWeight: 600, letterSpacing: 3 }}
      />

      <Sparkle
        name="Sparkle 1"
        size={60}
        color="#ffffff"
        delay={24}
        style={{ left: ROW_LEFT - 80, top: L.archTop }}
      />
      <Sparkle
        name="Sparkle 2"
        size={36}
        color="#F3C96B"
        delay={30}
        style={{ left: width - ROW_LEFT + 30, top: L.archTop + 90 }}
      />

      <div
        style={{
          position: "absolute",
          top: L.ctaTop,
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
            fontSize: L.ctaSize,
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
    price: { type: "string", default: "₹549", description: "Price" },
    cta: {
      type: "string",
      default: "SHOP THE COLLECTION",
      description: "Button text",
    },
  },
});
