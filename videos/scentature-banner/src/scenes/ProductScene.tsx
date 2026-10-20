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
import { Backdrop } from "../elements/Backdrop";
import { FloatingShapes, type ShapeKind } from "../elements/FloatingShapes";
import { Grain } from "../elements/Grain";
import { KineticLine, TypeOn } from "../elements/KineticText";
import { Marquee } from "../elements/Marquee";
import { Mist } from "../elements/Mist";
import { PriceTag } from "../elements/PriceTag";
import { Sparkle } from "../elements/Sparkle";
import { bodyFont, displayFont } from "../fonts";

type ProductSceneProps = {
  readonly bottle: string;
  readonly line1: string;
  readonly line2: string;
  readonly tagline: string;
  readonly accent: string;
  readonly base: string;
  readonly shape: ShapeKind;
  readonly price: string;
  readonly index: number;
  readonly total: number;
  readonly cta: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Rough width of an uppercase Playfair Display ExtraBold word, in ems
const emWidth = (word: string) =>
  word
    .split("")
    .reduce(
      (sum, ch) =>
        sum + (ch === "W" || ch === "M" ? 1.1 : ch === "I" ? 0.45 : 0.78),
      0,
    );

// Bottle cut-outs are 493x892; shown 700px tall, standing in the arch
const BOTTLE_H = 700;
const BOTTLE_W = (493 / 892) * BOTTLE_H;
const CX = 1390;
const BOTTLE_BOTTOM = 975;
const BOTTLE_TOP = BOTTLE_BOTTOM - BOTTLE_H;

const ProductSceneInner: React.FC<ProductSceneProps> = ({
  bottle,
  line1,
  line2,
  tagline,
  accent,
  base,
  shape,
  price,
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
  const sway = Math.sin(frame / 17) * 1.6;
  const nameSize = Math.min(160, 800 / emWidth(line2));

  return (
    <>
      <Backdrop
        name="Backdrop"
        accent={accent}
        base={base}
        ringsX={CX}
        ringsY={560}
      />
      <FloatingShapes
        name="Shapes – back"
        shape={shape}
        color={accent}
        count={16}
        seed={line2}
        depth="back"
        xMin={960}
        xMax={1880}
      />

      {/* Elegant outlined name scrolling along the bottom */}
      <Marquee
        name="Marquee"
        text={`${line1} ${line2} · `}
        fontFamily={displayFont}
        fontSize={200}
        color={`${accent}66`}
        outline
        speed={-7}
        style={{
          top: 870,
          fontStyle: "italic",
          fontWeight: 700,
          textTransform: "none",
        }}
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
          background: `linear-gradient(180deg, ${accent} 0%, ${accent}CC 100%)`,
          translate: `0 ${interpolate(frame, [0, 16], [920, 0], { ...clamp, easing: ease })}px`,
        }}
      />
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

      {/* Bottle, price tag and spray all move together: drop in, squash, float, sway */}
      <div
        style={{
          position: "absolute",
          left: CX - BOTTLE_W / 2,
          top: BOTTLE_TOP,
          width: BOTTLE_W,
          height: BOTTLE_H,
          transformOrigin: "50% 100%",
          translate: `0 ${Math.min(0, interpolate(drop, [0, 1], [-1200, 0])) - 10 - float}px`,
          rotate: `${interpolate(drop, [0, 1], [-18, 0]) + sway}deg`,
          scale: `${1 + beat * 0.015 + squash * 0.5} ${1 + beat * 0.015 - squash}`,
        }}
      >
        <Img
          src={staticFile(bottle)}
          style={{ width: BOTTLE_W, height: BOTTLE_H }}
        />
        <Mist
          name="Spray"
          delay={16}
          style={{ left: BOTTLE_W / 2 - 70, top: 40 }}
        />
      </div>

      {/* Price tag hangs from the arch, just clear of the bottle */}
      <PriceTag
        name="Price tag"
        price={price}
        accent={accent}
        delay={18}
        style={{ left: CX + 272, top: 330 }}
      />

      <FloatingShapes
        name="Shapes – front"
        shape={shape}
        color={accent}
        count={3}
        seed={line1}
        depth="front"
        xMin={1080}
        xMax={1900}
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
        style={{ left: CX + 300, top: 560 }}
      />
      <Sparkle
        name="Sparkle 3"
        size={46}
        color="#ffffff"
        delay={26}
        style={{ left: CX - 300, top: 760 }}
      />

      {/* Copy block */}
      <div style={{ position: "absolute", left: 130, top: 200, width: 900 }}>
        <TypeOn
          text={`${String(index).padStart(2, "0")} / ${String(total).padStart(2, "0")}   ·   SCENTATURE`}
          start={4}
          charsPerFrame={2.2}
          style={{
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 22,
            letterSpacing: 5,
            color: accent,
          }}
        />

        <div style={{ marginTop: 14 }}>
          <KineticLine
            text={line1}
            start={6}
            stagger={1.4}
            style={{
              fontFamily: displayFont,
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: nameSize * 0.72,
              lineHeight: 1.05,
              color: "#ffffff",
            }}
          />
          <KineticLine
            text={line2.toUpperCase()}
            start={11}
            stagger={1.6}
            style={{
              fontFamily: displayFont,
              fontWeight: 800,
              fontSize: nameSize,
              lineHeight: 0.95,
              letterSpacing: 2,
              color: accent,
            }}
          />
        </div>

        <div
          style={{
            marginTop: 18,
            fontFamily: displayFont,
            fontStyle: "italic",
            fontSize: 44,
            lineHeight: 1.1,
            color: "rgba(255,255,255,0.88)",
          }}
        >
          {tagline.split(" ").map((word, i) => (
            <span
              key={`${word}-${i}`}
              style={{
                display: "inline-block",
                marginRight: 12,
                opacity: interpolate(
                  frame,
                  [20 + i * 2, 28 + i * 2],
                  [0, 1],
                  clamp,
                ),
                translate: `0 ${interpolate(frame, [20 + i * 2, 30 + i * 2], [26, 0], { ...clamp, easing: ease })}px`,
              }}
            >
              {word}
            </span>
          ))}
        </div>

        {/* Price */}
        <div
          style={{
            marginTop: 30,
            display: "flex",
            alignItems: "baseline",
            gap: 18,
            fontFamily: bodyFont,
            color: "#ffffff",
            opacity: interpolate(frame, [26, 34], [0, 1], clamp),
            translate: `${interpolate(frame, [26, 38], [-40, 0], { ...clamp, easing: ease })}px 0`,
          }}
        >
          <span style={{ fontSize: 76, fontWeight: 700, lineHeight: 1 }}>
            {price}
          </span>
          <span
            style={{
              fontSize: 20,
              fontWeight: 500,
              letterSpacing: 3,
              color: "rgba(255,255,255,0.7)",
            }}
          >
            50 ML · EAU DE PARFUM
          </span>
        </div>

        <div
          style={{
            marginTop: 30,
            display: "inline-flex",
            alignItems: "center",
            gap: 14,
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 24,
            letterSpacing: 3,
            color: "#111111",
            background: "#ffffff",
            padding: "18px 34px",
            borderRadius: 999,
            clipPath: `inset(0 ${interpolate(frame, [32, 44], [100, 0], { ...clamp, easing: ease })}% 0 0 round 999px)`,
          }}
        >
          {cta}
          <span
            style={{
              display: "flex",
              color: accent,
              translate: `${beat * 8}px 0`,
            }}
          >
            <Arrow size={26} />
          </span>
        </div>
      </div>

      <Grain opacity={0.2} />
    </>
  );
};

export const ProductScene = Interactive.create({
  Component: ProductSceneInner,
  layout: "absolute-fill",
  schema: {
    ...Interactive.backgroundSchema,
    line1: { type: "string", default: "Bad", description: "Name, first line" },
    line2: {
      type: "string",
      default: "Girl",
      description: "Name, second line",
    },
    tagline: { type: "string", default: "", description: "Tagline" },
    price: { type: "string", default: "₹299", description: "Price" },
    accent: { type: "color", default: "#E07A2E", description: "Accent colour" },
    base: {
      type: "color",
      default: "#120A06",
      description: "Background colour",
    },
    cta: { type: "string", default: "SHOP NOW", description: "Button text" },
  },
});
