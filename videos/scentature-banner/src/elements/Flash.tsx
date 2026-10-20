import type React from "react";
import { Interactive, interpolate, useCurrentFrame } from "remotion";

type FlashProps = {
  readonly color: string;
  readonly style?: React.CSSProperties;
};

// A quick light burst that hides each cut and lands on the beat
const FlashInner: React.FC<FlashProps> = ({ color, style }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `radial-gradient(circle at 68% 50%, #ffffff 0%, ${color} 45%, transparent 85%)`,
        mixBlendMode: "screen",
        pointerEvents: "none",
        opacity: interpolate(frame, [0, 2, 10], [0, 0.95, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
        ...style,
      }}
    />
  );
};

export const Flash = Interactive.create({
  Component: FlashInner,
  layout: "none",
  schema: {
    color: { type: "color", default: "#ffffff", description: "Flash color" },
  },
});
