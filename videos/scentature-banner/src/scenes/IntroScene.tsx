import type React from "react";
import {
  Easing,
  Img,
  Interactive,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { Particles } from "../elements/Particles";
import { bodyFont } from "../fonts";

type IntroSceneProps = {
  readonly tagline: string;
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);

const IntroSceneInner: React.FC<IntroSceneProps> = ({ tagline }) => {
  const frame = useCurrentFrame();

  return (
    <>
      {/* Slowly turning glow in all four collection colours */}
      <div
        style={{
          position: "absolute",
          inset: -400,
          background:
            "conic-gradient(from 0deg at 50% 50%, #E08A3C33, #FF2E7E33, #2BD96033, #4D7CFF33, #E08A3C33)",
          filter: "blur(120px)",
          rotate: interpolate(frame, [0, 60], ["0deg", "90deg"]),
          opacity: interpolate(frame, [0, 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />
      <Particles name="Gold dust" color="#F3D9A4" count={40} seed="intro" />

      {/* Light line that draws across before the logo */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 540,
          height: 2,
          translate: "-50% 0",
          background: "linear-gradient(90deg, transparent, #fff, transparent)",
          boxShadow: "0 0 24px 4px rgba(255,255,255,0.6)",
          width: interpolate(frame, [0, 14], [0, 1400], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: ease,
          }),
          opacity: interpolate(frame, [0, 4, 16, 26], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      {/* Glow sits outside the wipe mask so it isn't cut into a box */}
      <div
        style={{
          position: "absolute",
          left: 550,
          top: 315,
          width: 820,
          filter: "drop-shadow(0 0 28px rgba(255,255,255,0.45))",
          scale: interpolate(frame, [8, 40, 48, 60], [1.08, 1, 1, 1.18], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: ease,
          }),
          opacity: interpolate(frame, [50, 59], [1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <Img
          src={staticFile("logo-white.png")}
          style={{
            display: "block",
            width: 820,
            clipPath: `inset(0 ${interpolate(frame, [8, 30], [100, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.inOut(Easing.cubic),
            })}% 0 0)`,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          top: 660,
          width: "100%",
          textAlign: "center",
          fontFamily: bodyFont,
          fontWeight: 600,
          fontSize: 30,
          letterSpacing: interpolate(frame, [24, 44], [30, 14], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: ease,
          }),
          color: "#F3D9A4",
          opacity: interpolate(frame, [24, 36, 48, 56], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {tagline}
      </div>
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
