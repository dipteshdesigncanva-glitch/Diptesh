// Drawn as SVG because Montserrat's latin subset has no "→" glyph
export const Arrow: React.FC<{ readonly size: number }> = ({ size }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2.6}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M4 12h15M13 6l6 6-6 6" />
  </svg>
);
