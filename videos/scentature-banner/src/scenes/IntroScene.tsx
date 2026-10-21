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
import { Grain } from "../elements/Grain";
import { TypeOn } from "../elements/KineticText";
import { Sparkle } from "../elements/Sparkle";
import { SpinBadge } from "../elements/SpinBadge";
import { FloatingShapes } from "../elements/FloatingShapes";
import { bodyFont } from "../fonts";

type IntroSceneProps = {
  readonly tagline: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const COLORS = ["#E07A2E", "#FF2E7E", "#22C55E", "#3B6BFF"];

const IntroSceneInner: React.FC<IntroSceneProps> = ({ tagline }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const portrait = height > width;
  // Logo box, centred in either frame shape; the sparkles hang off it
  const logo = { left: (width - 860) / 2, top: (height - 1080) / 2 + 330 };
  const labelSize = portrait ? 24 : 20;
  // Landscape: shapes stay in side columns. Portrait: they stay below the logo.
  const bands = portrait
    ? [
        { xMin: 30, xMax: 1050, yMin: 1250 },
        { xMin: 30, xMax: 1050, yMax: 620 },
        { xMin: 30, xMax: 1050, yMin: 1250 },
      ]
    : [
        { xMin: 30, xMax: 430, yMin: -1000 },
        { xMin: 1490, xMax: 1890, yMin: -1000 },
        { xMin: 30, xMax: 430, yMin: -1000 },
      ];

  return (
    <>
      {/* Four colour bars sweep up through the frame, one per scent */}
      {COLORS.map((color, i) => (
        <div
          key={color}
          style={{
            position: "absolute",
            left: (i * width) / 4,
            top: 0,
            width: width / 4 + 1,
            height,
            background: color,
            translate: `0 ${interpolate(
              frame,
              [i * 2, i * 2 + 10, i * 2 + 12, i * 2 + 22],
              [height, 0, 0, -height],
              {
                ...clamp,
                easing: Easing.inOut(Easing.cubic),
              },
            )}px`,
          }}
        />
      ))}

      <FloatingShapes
        name="Shapes"
        shape="mixed"
        color="#E07A2E"
        count={6}
        seed="intro-a"
        depth="back"
        {...bands[0]}
      />
      <FloatingShapes
        name="Shapes pink"
        shape="petal"
        color="#FF2E7E"
        count={5}
        seed="intro-b"
        depth="back"
        {...bands[1]}
      />
      <FloatingShapes
        name="Shapes blue"
        shape="ice"
        color="#3B6BFF"
        count={4}
        seed="intro-c"
        depth="back"
        {...bands[2]}
      />

      {/* Thin frame lines that draw in from the corners */}
      <div
        style={{
          position: "absolute",
          left: 60,
          top: 60,
          height: 2,
          background: "rgba(255,255,255,0.5)",
          width: interpolate(frame, [18, 36], [0, width - 120], {
            ...clamp,
            easing: ease,
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 60,
          bottom: 60,
          height: 2,
          background: "rgba(255,255,255,0.5)",
          width: interpolate(frame, [18, 36], [0, width - 120], {
            ...clamp,
            easing: ease,
          }),
        }}
      />
      <TypeOn
        text="SCENTATURE / PERFUME & ATTAR STUDIO"
        start={22}
        charsPerFrame={2.5}
        style={{
          position: "absolute",
          left: 60,
          top: 80,
          fontFamily: bodyFont,
          fontSize: labelSize,
          letterSpacing: 3,
          color: "#fff",
        }}
      />
      <TypeOn
        text="4 SIGNATURE SCENTS  ·  ₹549 EACH"
        start={26}
        charsPerFrame={2}
        style={{
          position: "absolute",
          right: 60,
          bottom: 80,
          fontFamily: bodyFont,
          fontSize: labelSize,
          letterSpacing: 3,
          color: "#fff",
        }}
      />

      {/* Logo writes itself on, then punches forward into the first cut */}
      <div
        style={{
          position: "absolute",
          ...logo,
          width: 860,
          scale: interpolate(frame, [18, 44, 50, 60], [1.12, 1, 1, 1.35], {
            ...clamp,
            easing: ease,
          }),
          opacity: interpolate(frame, [52, 58], [1, 0], clamp),
        }}
      >
        <Img
          src={staticFile("logo-white.png")}
          style={{
            display: "block",
            width: 860,
            clipPath: `inset(0 ${interpolate(frame, [18, 38], [100, 0], {
              ...clamp,
              easing: Easing.inOut(Easing.cubic),
            })}% 0 0)`,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          top: logo.top + 360,
          width: "100%",
          textAlign: "center",
          fontFamily: bodyFont,
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: interpolate(frame, [30, 46], [26, 10], {
            ...clamp,
            easing: ease,
          }),
          color: "#ffffff",
          opacity: interpolate(frame, [30, 38, 50, 56], [0, 1, 1, 0], clamp),
        }}
      >
        {tagline}
      </div>

      <SpinBadge
        name="Badge"
        text="ALL AT ₹549 • SCENTATURE • "
        size={190}
        color="#111111"
        fill="#ffffff"
        delay={28}
        style={
          portrait
            ? { left: width - 290, top: logo.top - 260 }
            : { left: logo.left + 890, top: logo.top - 120 }
        }
      />
      <Sparkle
        name="Sparkle 1"
        size={58}
        color="#ffffff"
        delay={30}
        style={{ left: logo.left - 60, top: logo.top - 30 }}
      />
      <Sparkle
        name="Sparkle 2"
        size={30}
        color="#FF2E7E"
        delay={34}
        style={{ left: logo.left + 830, top: logo.top + 290 }}
      />
      <Sparkle
        name="Sparkle 3"
        size={40}
        color="#E07A2E"
        delay={38}
        style={{ left: logo.left + 70, top: logo.top + 320 }}
      />

      <Grain opacity={0.22} />
    </>
  );
};

export const IntroScene = Interactive.create({
  Component: IntroSceneInner,
  layout: "absolute-fill",
  schema: {
    ...Interactive.backgroundSchema,
    tagline: {
      type: "string",
      default: "THE SIGNATURE COLLECTION",
      description: "Tagline under the logo",
    },
  },
});
