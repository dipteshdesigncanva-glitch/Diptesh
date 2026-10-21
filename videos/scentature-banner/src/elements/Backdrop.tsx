import type React from "react";
import { Interactive, useCurrentFrame, useVideoConfig } from "remotion";

type BackdropProps = {
  readonly accent: string;
  readonly base: string;
  readonly ringsX: number;
  readonly ringsY: number;
  readonly style?: React.CSSProperties;
};

// Soft two-tone gradient, a drifting dot grid and slowly turning dashed rings
const BackdropInner: React.FC<BackdropProps> = ({
  accent,
  base,
  ringsX,
  ringsY,
  style,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  return (
    <div
      style={{ position: "absolute", inset: 0, overflow: "hidden", ...style }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(125deg, ${base} 0%, ${base} 45%, ${accent}40 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: -60,
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.16) 2px, transparent 2.5px)",
          backgroundSize: "44px 44px",
          translate: `${(frame * 0.6) % 44}px ${(frame * 0.4) % 44}px`,
          maskImage: "linear-gradient(90deg, black 0%, transparent 60%)",
        }}
      />
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0 }}
      >
        {[260, 380, 500, 640].map((r, i) => (
          <circle
            key={r}
            cx={ringsX}
            cy={ringsY}
            r={r}
            fill="none"
            stroke={i % 2 ? accent : "rgba(255,255,255,0.5)"}
            strokeOpacity={i % 2 ? 0.5 : 0.25}
            strokeWidth={i === 3 ? 1.5 : 2}
            strokeDasharray={i % 2 ? "2 14" : "40 18"}
            style={{
              transformOrigin: `${ringsX}px ${ringsY}px`,
              rotate: `${frame * (i % 2 ? -0.5 : 0.35) * (i + 1)}deg`,
            }}
          />
        ))}
      </svg>
    </div>
  );
};

export const Backdrop = Interactive.create({
  Component: BackdropInner,
  layout: "none",
  schema: {
    accent: { type: "color", default: "#E07A2E", description: "Accent colour" },
    base: { type: "color", default: "#120A06", description: "Base colour" },
  },
});
