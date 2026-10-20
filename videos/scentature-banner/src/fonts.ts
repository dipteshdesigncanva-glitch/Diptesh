import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Bundled in public/fonts so renders don't depend on reaching Google Fonts.
// Anton matches the condensed bold type on the bottle labels.
export const displayFont = "Anton";
export const bodyFont = "Montserrat";

loadFont({
  family: displayFont,
  url: staticFile("fonts/Anton-Regular.woff2"),
  weight: "400",
});
loadFont({
  family: bodyFont,
  url: staticFile("fonts/Montserrat-Variable.woff2"),
  weight: "100 900",
});
