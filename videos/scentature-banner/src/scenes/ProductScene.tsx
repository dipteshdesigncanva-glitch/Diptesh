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
import { KineticLine, TypeOn } from "../elements/KineticText";
import { Marquee } from "../elements/Marquee";
import { Sparkle } from "../elements/Sparkle";
import { SpinBadge } from "../elements/SpinBadge";
import { displayFont, monoFont, serifFont } from "../fonts";

type ProductSceneProps = {
  readonly bottle: string;
  readonly line1: string;
  readonly line2: string;
  readonly tagline: string;
  readonly accent: string;
  readonly index: number;
  readonly total: number;
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);

// Rough width of an uppercase Syne ExtraBold word, in ems
const emWidth = (word: string) =>
  word
    .split("")
    .reduce(
      (sum, ch) =>
        sum + (ch === "W" ? 1.5 : ch === "M" ? 1.3 : ch === "I" ? 0.5 : 1.1),
      0,
    );
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Bottle cut-outs are 493x892; shown 700px tall, standing in the arch
const BOTTLE_H = 700;
const BOTTLE_W = (493 / 892) * BOTTLE_H;
const CX = 1390;
const BOTTLE_BOTTOM = 975;

const ProductSceneInner: React.FC<ProductSceneProps> = ({
  bottle,
  line1,
  line2,
  tagline,
  accent,
  index,
  total,
  cta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // The music is 120 BPM: a beat lands every 15 frames from the scene start
  const beat = Math.exp(-(frame % 15) / 4);
  const drop = spring({
    frame: frame - 4,
    fps,
    config: { damping: 11, stiffness: 140, mass: 0.9 },
  });
  const float = Math.sin(frame / 11) * 9;
  // Instead of sinking past its spot when the spring overshoots, the bottle squashes on landing
  const squash = Math.max(0, drop - 1) * 0.6;
  // Syne is wide: size the name so the longer line fits left of the arch (~820px)
  const nameSize = Math.min(
    150,
    820 / Math.max(emWidth(line1), emWidth(line2)),
  );

  return (
    <>
      {/* Giant outlined names scrolling behind everything */}
      <Marquee
        name="Marquee top"
        text={`${line1} ${line2} — `}
        fontFamily={displayFont}
        fontSize={250}
        color={`${accent}55`}
        outline
        speed={9}
        style={{ top: -40 }}
      />
      <Marquee
        name="Marquee bottom"
        text={`${line1} ${line2} — `}
        fontFamily={displayFont}
        fontSize={250}
        color={`${accent}55`}
        outline
        speed={-9}
        style={{ top: 860 }}
      />

      {/* Solid arch the bottle stands in */}
      <div
        style={{
          position: "absolute",
          left: CX - 290,
          top: 190,
          width: 580,
          height: 1000,
          borderRadius: "290px 290px 0 0",
          background: accent,
          translate: `0 ${interpolate(frame, [0, 16], [920, 0], { ...clamp, easing: ease })}px`,
        }}
      />
      {/* Outline arch drawn slightly bigger, lagging behind */}
      <div
        style={{
          position: "absolute",
          left: CX - 320,
          top: 160,
          width: 640,
          height: 1000,
          borderRadius: "320px 320px 0 0",
          border: "2px solid rgba(255,255,255,0.55)",
          translate: `0 ${interpolate(frame, [4, 22], [920, 0], { ...clamp, easing: ease })}px`,
          rotate: `${interpolate(frame, [4, 22], [-6, 0], { ...clamp, easing: ease })}deg`,
        }}
      />

      {/* Flat contact shadow that shrinks as the bottle floats up */}
      <div
        style={{
          position: "absolute",
          left: CX - 210,
          top: BOTTLE_BOTTOM - 22,
          width: 420,
          height: 44,
          borderRadius: "50%",
          background: "rgba(0,0,0,0.35)",
          filter: "blur(6px)",
          scale: `${(0.85 - float / 90) * drop}`,
        }}
      />

      {/* The bottle drops in on a spring, then floats and sways */}
      <Img
        src={staticFile(bottle)}
        style={{
          position: "absolute",
          left: CX - BOTTLE_W / 2,
          top: BOTTLE_BOTTOM - BOTTLE_H,
          width: BOTTLE_W,
          height: BOTTLE_H,
          transformOrigin: "50% 100%",
          translate: `0 ${Math.min(0, interpolate(drop, [0, 1], [-1200, 0])) - 10 - float}px`,
          rotate: `${interpolate(drop, [0, 1], [-18, 0]) + Math.sin(frame / 17) * 1.6}deg`,
          scale: `${1 + beat * 0.015 + squash * 0.5} ${1 + beat * 0.015 - squash}`,
        }}
      />

      <SpinBadge
        name="Badge"
        text="EAU DE PARFUM • 50 ML • SCENTATURE • "
        size={210}
        color="#111111"
        fill="#ffffff"
        delay={16}
        style={{ left: CX + 170, top: 230 }}
      />

      <Sparkle
        name="Sparkle 1"
        size={64}
        color="#ffffff"
        delay={14}
        style={{ left: CX - 330, top: 300 }}
      />
      <Sparkle
        name="Sparkle 2"
        size={34}
        color="#ffffff"
        delay={20}
        style={{ left: CX + 290, top: 560 }}
      />
      <Sparkle
        name="Sparkle 3"
        size={46}
        color="#ffffff"
        delay={26}
        style={{ left: CX - 300, top: 760 }}
      />
      <Sparkle
        name="Sparkle 4"
        size={26}
        color={accent}
        delay={30}
        style={{ left: CX - 420, top: 520 }}
      />

      {/* Copy block */}
      <div style={{ position: "absolute", left: 130, top: 236, width: 900 }}>
        <TypeOn
          text={`[${String(index).padStart(2, "0")}/${String(total).padStart(2, "0")}]  SCENTATURE PARFUMS`}
          start={4}
          charsPerFrame={2.2}
          style={{
            fontFamily: monoFont,
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: 3,
            color: accent,
          }}
        />

        <div style={{ marginTop: 18 }}>
          <KineticLine
            text={line1}
            start={6}
            stagger={1.5}
            style={{
              fontFamily: displayFont,
              fontWeight: 800,
              fontSize: nameSize,
              lineHeight: 0.95,
              letterSpacing: -3,
              color: "#ffffff",
            }}
          />
          <KineticLine
            text={line2}
            start={11}
            stagger={1.5}
            style={{
              fontFamily: displayFont,
              fontWeight: 800,
              fontSize: nameSize,
              lineHeight: 0.95,
              letterSpacing: -3,
              color: accent,
            }}
          />
        </div>

        <div
          style={{
            marginTop: 22,
            fontFamily: serifFont,
            fontStyle: "italic",
            fontSize: 64,
            lineHeight: 1.05,
            color: "rgba(255,255,255,0.92)",
          }}
        >
          {tagline.split(" ").map((word, i) => (
            <span
              key={`${word}-${i}`}
              style={{
                display: "inline-block",
                marginRight: 16,
                opacity: interpolate(
                  frame,
                  [20 + i * 2, 28 + i * 2],
                  [0, 1],
                  clamp,
                ),
                translate: `0 ${interpolate(frame, [20 + i * 2, 30 + i * 2], [30, 0], { ...clamp, easing: ease })}px`,
              }}
            >
              {word}
            </span>
          ))}
        </div>

        <div
          style={{
            marginTop: 40,
            display: "flex",
            alignItems: "center",
            gap: 28,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              fontFamily: displayFont,
              fontWeight: 800,
              fontSize: 28,
              letterSpacing: 2,
              color: "#111111",
              background: accent,
              padding: "20px 36px",
              borderRadius: 999,
              clipPath: `inset(0 ${interpolate(frame, [30, 42], [100, 0], { ...clamp, easing: ease })}% 0 0 round 999px)`,
            }}
          >
            {cta}
            <span style={{ display: "flex", translate: `${beat * 8}px 0` }}>
              <Arrow size={28} />
            </span>
          </div>
          <div
            style={{
              fontFamily: monoFont,
              fontSize: 22,
              letterSpacing: 2,
              color: "rgba(255,255,255,0.75)",
              opacity: interpolate(frame, [36, 44], [0, 1], clamp),
            }}
          >
            EAU DE PARFUM — 50 ML
          </div>
        </div>
      </div>

      <Grain opacity={0.22} />
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
    accent: { type: "color", default: "#E07A2E", description: "Accent colour" },
    cta: { type: "string", default: "SHOP NOW", description: "Button text" },
  },
});
