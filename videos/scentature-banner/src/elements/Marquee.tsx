import type React from "react";
import { Interactive, useCurrentFrame, useVideoConfig } from "remotion";

type MarqueeProps = {
  readonly text: string;
  readonly fontFamily: string;
  readonly fontSize: number;
  readonly color: string;
  readonly outline: boolean;
  readonly speed: number;
  readonly style?: React.CSSProperties;
};

// An endless line of text scrolling sideways. Negative speed scrolls right.
const MarqueeInner: React.FC<MarqueeProps> = ({
  text,
  fontFamily,
  fontSize,
  color,
  outline,
  speed,
  style,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width,
        overflow: "hidden",
        whiteSpace: "nowrap",
        fontFamily,
        fontSize,
        fontWeight: 800,
        lineHeight: 1,
        textTransform: "uppercase",
        color: outline ? "transparent" : color,
        WebkitTextStroke: outline ? `2px ${color}` : undefined,
        ...style,
      }}
    >
      <div style={{ translate: `${-((frame * speed) % 2000) - 2000}px 0` }}>
        {text.repeat(12)}
      </div>
    </div>
  );
};

export const Marquee = Interactive.create({
  Component: MarqueeInner,
  layout: "none",
  schema: {
    text: {
      type: "string",
      default: "SCENTATURE — ",
      description: "Text (repeated)",
    },
    color: { type: "color", default: "#ffffff", description: "Colour" },
  },
});
