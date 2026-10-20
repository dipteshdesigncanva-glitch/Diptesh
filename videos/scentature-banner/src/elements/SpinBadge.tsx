import type React from "react";
import { useId } from "react";
import { Easing, Interactive, interpolate, useCurrentFrame } from "remotion";
import { monoFont } from "../fonts";

type SpinBadgeProps = {
  readonly text: string;
  readonly size: number;
  readonly color: string;
  readonly fill: string;
  readonly delay: number;
  readonly style?: React.CSSProperties;
};

// A round sticker with text running around its edge, spinning slowly
const SpinBadgeInner: React.FC<SpinBadgeProps> = ({
  text,
  size,
  color,
  fill,
  delay,
  style,
}) => {
  const frame = useCurrentFrame() - delay;
  const r = 38;
  const pathId = `badge-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      style={{
        position: "absolute",
        overflow: "visible",
        scale: interpolate(frame, [0, 12], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.back(2.4)),
        }),
        ...style,
      }}
    >
      <circle cx={50} cy={50} r={49} fill={fill} />
      <g style={{ transformOrigin: "50px 50px", rotate: `${frame * 2.4}deg` }}>
        <path
          id={pathId}
          d={`M50 ${50 - r} a${r} ${r} 0 1 1 -0.01 0`}
          fill="none"
        />
        <text
          fill={color}
          fontFamily={monoFont}
          fontSize={(2 * Math.PI * r) / (text.length * 0.62)}
          fontWeight={700}
          letterSpacing={0}
        >
          <textPath href={`#${pathId}`}>{text}</textPath>
        </text>
      </g>
      <path
        d="M50 34 C51.6 46 54 48.4 66 50 C54 51.6 51.6 54 50 66 C48.4 54 46 51.6 34 50 C46 48.4 48.4 46 50 34 Z"
        fill={color}
        style={{ transformOrigin: "50px 50px", rotate: `${-frame * 4}deg` }}
      />
    </svg>
  );
};

export const SpinBadge = Interactive.create({
  Component: SpinBadgeInner,
  layout: "none",
  schema: {
    text: {
      type: "string",
      default: "EAU DE PARFUM • 50 ML • ",
      description: "Text around the edge",
    },
    color: { type: "color", default: "#111111", description: "Text colour" },
    fill: { type: "color", default: "#ffffff", description: "Badge colour" },
  },
});
