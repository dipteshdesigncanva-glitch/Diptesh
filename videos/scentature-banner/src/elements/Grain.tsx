import { useId } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

// Moving film grain so flat colour backgrounds feel printed, not digital
export const Grain: React.FC<{ readonly opacity: number }> = ({ opacity }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const id = `grain-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;

  return (
    <svg
      width={width}
      height={height}
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    >
      <filter id={id}>
        <feTurbulence
          type="fractalNoise"
          baseFrequency={0.9}
          numOctaves={2}
          seed={frame % 12}
          stitchTiles="stitch"
        />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#${id})`} />
    </svg>
  );
};
