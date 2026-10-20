import type React from "react";
import { Interactive, random, useCurrentFrame } from "remotion";

type MistProps = {
  readonly delay: number;
  readonly style?: React.CSSProperties;
};

// A puff of perfume spray: fine droplets burst out sideways and fade away
const MistInner: React.FC<MistProps> = ({ delay, style }) => {
  const t = useCurrentFrame() - delay;
  if (t < 0 || t > 40) {
    return null;
  }

  return (
    <div style={{ position: "absolute", width: 0, height: 0, ...style }}>
      {new Array(46).fill(true).map((_, i) => {
        const angle = (-160 + random(`a${i}`) * 50) * (Math.PI / 180);
        const speed = 14 + random(`s${i}`) * 26;
        const dist = speed * (1 - Math.exp(-t / 7)) * 7;
        const size = 4 + random(`r${i}`) * 16;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: Math.cos(angle) * dist,
              top: Math.sin(angle) * dist - t * 0.8,
              width: size,
              height: size,
              borderRadius: "50%",
              background: "rgba(255,255,255,0.75)",
              filter: "blur(2px)",
              opacity: Math.max(0, 1 - t / 40) * (0.4 + random(`o${i}`) * 0.6),
            }}
          />
        );
      })}
    </div>
  );
};

export const Mist = Interactive.create({
  Component: MistInner,
  layout: "none",
  schema: {},
});
