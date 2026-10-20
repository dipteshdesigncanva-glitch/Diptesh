import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Bundled in public/fonts so renders don't depend on reaching Google Fonts.
// Syne for big names and buttons, Instrument Serif italic for taglines,
// Space Mono for small labels.
export const displayFont = "Syne";
export const serifFont = "Instrument Serif";
export const monoFont = "Space Mono";

loadFont({
  family: displayFont,
  url: staticFile("fonts/Syne-Variable.woff2"),
  weight: "400 800",
});
loadFont({
  family: serifFont,
  url: staticFile("fonts/InstrumentSerif-Italic.woff2"),
  style: "italic",
  weight: "400",
});
loadFont({
  family: monoFont,
  url: staticFile("fonts/SpaceMono-Regular.woff2"),
  weight: "400",
});
loadFont({
  family: monoFont,
  url: staticFile("fonts/SpaceMono-Bold.woff2"),
  weight: "700",
});
