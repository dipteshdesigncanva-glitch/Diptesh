import type React from "react";
import {
  Easing,
  Interactive,
  interpolate,
  random,
  useCurrentFrame,
} from "remotion";

export type ShapeKind = "drop" | "petal" | "leaf" | "ice" | "mixed";

type FloatingShapesProps = {
  readonly shape: ShapeKind;
  readonly color: string;
  readonly count: number;
  readonly seed: string;
  // "back" shapes are small and sharp; "front" shapes are big and out of focus
  readonly depth: "back" | "front";
  // Horizontal band the shapes stay inside, so they keep clear of text
  readonly xMin: number;
  readonly xMax: number;
  readonly style?: React.CSSProperties;
};

const KINDS: Exclude<ShapeKind, "mixed">[] = ["drop", "petal", "leaf", "ice"];

const Shape: React.FC<{
  readonly kind: Exclude<ShapeKind, "mixed">;
  readonly color: string;
}> = ({ kind, color }) => {
  if (kind === "drop") {
    return (
      <svg viewBox="0 0 100 140" width="100%" height="100%">
        <path
          d="M50 0 C50 0 95 62 95 92 A45 45 0 0 1 5 92 C5 62 50 0 50 0 Z"
          fill={color}
        />
        <ellipse cx={34} cy={92} rx={9} ry={16} fill="rgba(255,255,255,0.45)" />
      </svg>
    );
  }
  if (kind === "petal") {
    return (
      <svg viewBox="0 0 100 120" width="100%" height="100%">
        <path
          d="M50 118 C8 92 0 40 22 14 C34 0 50 10 50 22 C50 10 66 0 78 14 C100 40 92 92 50 118 Z"
          fill={color}
        />
        <path
          d="M50 110 C46 80 46 50 50 26"
          stroke="rgba(255,255,255,0.35)"
          strokeWidth={3}
          fill="none"
        />
      </svg>
    );
  }
  if (kind === "leaf") {
    return (
      <svg viewBox="0 0 100 140" width="100%" height="100%">
        <path d="M50 2 C92 32 96 92 50 138 C4 92 8 32 50 2 Z" fill={color} />
        <path
          d="M50 136 L50 16 M50 60 L30 44 M50 84 L72 64 M50 104 L32 90"
          stroke="rgba(0,0,0,0.25)"
          strokeWidth={3}
          fill="none"
        />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 100 100" width="100%" height="100%">
      <rect
        x={6}
        y={6}
        width={88}
        height={88}
        rx={18}
        fill={color}
        fillOpacity={0.55}
        stroke="rgba(255,255,255,0.8)"
        strokeWidth={3}
      />
      <path
        d="M22 30 L40 22 M22 46 L30 42"
        stroke="#ffffff"
        strokeWidth={6}
        strokeLinecap="round"
      />
    </svg>
  );
};

// Themed shapes drifting upward, tumbling slowly, with a little sway
const FloatingShapesInner: React.FC<FloatingShapesProps> = ({
  shape,
  color,
  count,
  seed,
  depth,
  xMin,
  xMax,
  style,
}) => {
  const frame = useCurrentFrame();
  const front = depth === "front";

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
      {new Array(count).fill(true).map((_, i) => {
        const r = (k: string) => random(`${seed}-${depth}-${k}-${i}`);
        const kind = shape === "mixed" ? KINDS[Math.floor(r("k") * 4)] : shape;
        const size = front ? 110 + r("s") * 90 : 34 + r("s") * 56;
        const speed = (front ? 2.4 : 0.9) + r("v") * 1.2;
        const y =
          ((((r("y") * 1300 - frame * speed) % 1300) + 1300) % 1300) - 160;
        const x =
          xMin + r("x") * (xMax - xMin) + Math.sin((frame + i * 20) / 26) * 24;
        const spin = (r("r") - 0.5) * 3;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size * 1.3,
              rotate: `${r("a") * 360 + frame * spin}deg`,
              opacity: front ? 0.85 : 0.55 + r("o") * 0.35,
              filter: front ? "blur(7px)" : undefined,
              scale: interpolate(frame, [i * 0.6, i * 0.6 + 14], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.back(1.6)),
              }),
            }}
          >
            <Shape kind={kind} color={color} />
          </div>
        );
      })}
    </div>
  );
};

export const FloatingShapes = Interactive.create({
  Component: FloatingShapesInner,
  layout: "none",
  schema: {
    color: { type: "color", default: "#ffffff", description: "Colour" },
    count: {
      type: "number",
      default: 14,
      min: 0,
      max: 60,
      step: 1,
      description: "How many",
      hiddenFromList: false,
    },
  },
});
