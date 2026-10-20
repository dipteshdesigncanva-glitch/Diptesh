import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame } from "remotion";

type PanelWipeProps = {
  readonly first: string;
  readonly second: string;
  readonly style?: React.CSSProperties;
};

// Two slanted colour panels sweep right-to-left and hide the cut.
// The cut should sit at frame 8 of this element; give it 18 frames.
const PanelWipeInner: React.FC<PanelWipeProps> = ({ first, second, style }) => {
  const frame = useCurrentFrame();
  const sweep = (start: number) =>
    interpolate(frame, [start, start + 14], [2100, -2700], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.7, 0, 0.3, 1),
    });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -100,
          width: 2500,
          height: 1280,
          transform: "skewX(-14deg)",
          background: first,
          translate: `${sweep(0)}px 0`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: -100,
          width: 2500,
          height: 1280,
          transform: "skewX(-14deg)",
          background: second,
          translate: `${sweep(3)}px 0`,
        }}
      />
    </div>
  );
};

export const PanelWipe = Interactive.create({
  Component: PanelWipeInner,
  layout: "none",
  schema: {
    first: { type: "color", default: "#ffffff", description: "First panel" },
    second: { type: "color", default: "#111111", description: "Second panel" },
  },
});
