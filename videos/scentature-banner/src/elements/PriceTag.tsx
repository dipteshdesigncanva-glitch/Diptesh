import type React from "react";
import { Interactive, useCurrentFrame } from "remotion";
import { bodyFont } from "../fonts";

type PriceTagProps = {
  readonly price: string;
  readonly accent: string;
  readonly delay: number;
  readonly style?: React.CSSProperties;
};

// A paper price tag hanging on a string. It swings in and settles like a pendulum.
const PriceTagInner: React.FC<PriceTagProps> = ({
  price,
  accent,
  delay,
  style,
}) => {
  const t = Math.max(0, useCurrentFrame() - delay);
  const swing =
    38 * Math.exp(-t / 14) * Math.cos(t / 3.2) + Math.sin(t / 16) * 3;

  return (
    <div
      style={{
        position: "absolute",
        width: 0,
        height: 0,
        transformOrigin: "0 0",
        rotate: `${swing}deg`,
        opacity: t > 0 ? 1 : 0,
        ...style,
      }}
    >
      {/* String */}
      <div
        style={{
          position: "absolute",
          left: -1,
          top: 0,
          width: 2,
          height: 70,
          background: "#F3E6CF",
        }}
      />
      {/* Tag */}
      <div
        style={{
          position: "absolute",
          left: -82,
          top: 66,
          width: 164,
          height: 210,
          background: "#FFF8EC",
          clipPath: "polygon(30% 0, 70% 0, 100% 18%, 100% 100%, 0 100%, 0 18%)",
          borderRadius: 14,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          fontFamily: bodyFont,
          color: "#151515",
        }}
      >
        <div
          style={{
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: "#151515",
            marginBottom: 14,
          }}
        />
        <div
          style={{
            fontSize: 15,
            fontWeight: 600,
            letterSpacing: 3,
            color: accent,
          }}
        >
          ONLY
        </div>
        <div style={{ fontSize: 50, fontWeight: 700, lineHeight: 1 }}>
          {price}
        </div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 500,
            letterSpacing: 2,
            opacity: 0.7,
          }}
        >
          50 ML
        </div>
      </div>
    </div>
  );
};

export const PriceTag = Interactive.create({
  Component: PriceTagInner,
  layout: "none",
  schema: {
    price: { type: "string", default: "₹299", description: "Price" },
    accent: { type: "color", default: "#E07A2E", description: "Accent colour" },
  },
});
