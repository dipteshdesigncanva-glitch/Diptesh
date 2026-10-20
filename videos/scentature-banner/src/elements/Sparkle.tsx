import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame } from "remotion";

type SparkleProps = {
  readonly size: number;
  readonly color: string;
  readonly delay: number;
  readonly style?: React.CSSProperties;
};

// A four-point star that pops in, spins, and keeps twinkling every 30 frames (two beats)
const SparkleInner: React.FC<SparkleProps> = ({
  size,
  color,
  delay,
  style,
}) => {
  const frame = useCurrentFrame() - delay;
  const cycle = ((frame % 30) + 30) % 30;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      style={{
        position: "absolute",
        overflow: "visible",
        scale:
          frame < 0
            ? 0
            : interpolate(frame, [0, 10], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.back(3)),
              }) * interpolate(cycle, [0, 4, 15, 30], [1.25, 1, 0.8, 1.25]),
        rotate: `${frame * 3}deg`,
        ...style,
      }}
    >
      <path
        d="M50 0 C54 36 64 46 100 50 C64 54 54 64 50 100 C46 64 36 54 0 50 C36 46 46 36 50 0 Z"
        fill={color}
      />
    </svg>
  );
};

export const Sparkle = Interactive.create({
  Component: SparkleInner,
  layout: "none",
  schema: {
    color: { type: "color", default: "#ffffff", description: "Colour" },
    size: {
      type: "number",
      default: 40,
      min: 4,
      max: 300,
      step: 1,
      description: "Size",
      hiddenFromList: false,
    },
  },
});
