import type React from "react";
import { Interactive, random, useCurrentFrame } from "remotion";

type ParticlesProps = {
  readonly color: string;
  readonly count: number;
  readonly seed: string;
  readonly style?: React.CSSProperties;
};

// Soft bokeh dots drifting upwards, like light catching mist from a spray
const ParticlesInner: React.FC<ParticlesProps> = ({
  color,
  count,
  seed,
  style,
}) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        mixBlendMode: "screen",
        ...style,
      }}
    >
      {new Array(count).fill(true).map((_, i) => {
        const x = random(`${seed}-x-${i}`) * 1920;
        const startY = random(`${seed}-y-${i}`) * 1200;
        const speed = 0.6 + random(`${seed}-s-${i}`) * 1.8;
        const size = 4 + random(`${seed}-r-${i}`) ** 3 * 34;
        const sway = Math.sin((frame + i * 13) / 22) * 14;
        const y = ((((startY - frame * speed) % 1200) + 1200) % 1200) - 60;
        const twinkle = 0.35 + 0.65 * Math.abs(Math.sin((frame + i * 7) / 15));

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + sway,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
              opacity: twinkle * (size > 20 ? 0.45 : 0.9),
              filter: size > 20 ? "blur(3px)" : undefined,
            }}
          />
        );
      })}
    </div>
  );
};

export const Particles = Interactive.create({
  Component: ParticlesInner,
  layout: "none",
  schema: {
    color: { type: "color", default: "#ffffff", description: "Particle color" },
    count: {
      type: "number",
      default: 30,
      min: 0,
      max: 120,
      step: 1,
      description: "Particle count",
      hiddenFromList: false,
    },
  },
});
