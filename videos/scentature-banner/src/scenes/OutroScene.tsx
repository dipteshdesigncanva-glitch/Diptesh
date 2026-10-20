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
import { Grain } from "../elements/Grain";
import { Marquee } from "../elements/Marquee";
import { Sparkle } from "../elements/Sparkle";
import { displayFont, monoFont } from "../fonts";

type OutroSceneProps = {
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const ARCH_W = 300;
const GAP = 56;
const ROW_LEFT = (1920 - (ARCH_W * 4 + GAP * 3)) / 2;
const BOTTLE_H = 430;
const BOTTLE_W = (493 / 892) * BOTTLE_H;

const lineUp = [
  { src: "bottles/bad-girl.png", accent: "#E07A2E" },
  { src: "bottles/floral-kiss.png", accent: "#FF2E7E" },
  { src: "bottles/hawas-classic.png", accent: "#22C55E" },
  { src: "bottles/hawas-ice.png", accent: "#3B6BFF" },
];

const OutroSceneInner: React.FC<OutroSceneProps> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const beat = Math.exp(-(frame % 15) / 4);

  return (
    <>
      <Img
        src={staticFile("logo-white.png")}
        style={{
          position: "absolute",
          left: (1920 - 440) / 2,
          top: 56,
          width: 440,
          clipPath: `inset(0 ${interpolate(frame, [0, 16], [100, 0], { ...clamp, easing: Easing.inOut(Easing.cubic) })}% 0 0)`,
        }}
      />

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
                top: 300,
                width: ARCH_W,
                height: 520,
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
                top: 800 - BOTTLE_H,
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
          top: 820,
          width: 1920,
          height: 64,
          background: "#ffffff",
        }}
      />
      <Marquee
        name="Names strip"
        text="BAD GIRL • FLORAL KISS • HAWAS CLASSIC • HAWAS ICE • "
        fontFamily={monoFont}
        fontSize={30}
        color="#111111"
        outline={false}
        speed={6}
        style={{ top: 837 }}
      />

      <Sparkle
        name="Sparkle 1"
        size={60}
        color="#ffffff"
        delay={24}
        style={{ left: ROW_LEFT - 70, top: 280 }}
      />
      <Sparkle
        name="Sparkle 2"
        size={36}
        color="#ffffff"
        delay={30}
        style={{ left: 1920 - ROW_LEFT + 20, top: 360 }}
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
            fontFamily: displayFont,
            fontWeight: 800,
            fontSize: 30,
            letterSpacing: 2,
            color: "#111111",
            background: "#ffffff",
            padding: "22px 48px",
            borderRadius: 999,
            scale: interpolate(frame, [30, 42], [0, 1], {
              ...clamp,
              easing: Easing.out(Easing.back(2)),
            }),
          }}
        >
          {cta}
          <span style={{ display: "flex", translate: `${beat * 8}px 0` }}>
            <Arrow size={30} />
          </span>
        </div>
      </div>

      <Grain opacity={0.22} />

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
    cta: {
      type: "string",
      default: "SHOP THE COLLECTION",
      description: "Button text",
    },
  },
});
