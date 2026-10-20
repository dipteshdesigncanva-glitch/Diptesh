import type React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Letters rise out of a mask one after another, each with a small tilt
export const KineticLine: React.FC<{
  readonly text: string;
  readonly start: number;
  readonly stagger: number;
  readonly style: React.CSSProperties;
}> = ({ text, start, stagger, style }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{ display: "flex", overflow: "hidden", paddingTop: 8, ...style }}
    >
      {text.split("").map((char, i) => {
        const s = start + i * stagger;
        return (
          <span
            key={`${char}-${i}`}
            style={{
              display: "inline-block",
              whiteSpace: "pre",
              translate: `0 ${interpolate(frame, [s, s + 12], [115, 0], {
                ...clamp,
                easing: Easing.bezier(0.16, 1, 0.3, 1),
              })}%`,
              rotate: `${interpolate(frame, [s, s + 12], [14, 0], { ...clamp, easing: Easing.out(Easing.cubic) })}deg`,
            }}
          >
            {char}
          </span>
        );
      })}
    </div>
  );
};

// Text that types itself out, with a blinking block cursor
export const TypeOn: React.FC<{
  readonly text: string;
  readonly start: number;
  readonly charsPerFrame: number;
  readonly style: React.CSSProperties;
}> = ({ text, start, charsPerFrame, style }) => {
  const frame = useCurrentFrame();
  const shown = Math.max(
    0,
    Math.min(text.length, Math.floor((frame - start) * charsPerFrame)),
  );
  const typing = shown < text.length;

  return (
    <div style={{ whiteSpace: "pre", ...style }}>
      {text.slice(0, shown)}
      <span
        style={{
          display: "inline-block",
          width: "0.6em",
          height: "1em",
          marginLeft: 4,
          verticalAlign: "-0.15em",
          background: "currentColor",
          opacity: typing || Math.floor(frame / 8) % 2 === 0 ? 1 : 0,
        }}
      />
    </div>
  );
};
