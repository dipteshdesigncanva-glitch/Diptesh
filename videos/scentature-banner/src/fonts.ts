import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Bundled in public/fonts so renders don't depend on reaching Google Fonts.
// Playfair Display for names and taglines; Poppins for prices, labels and buttons.
// Poppins' Devanagari files are only loaded for the rupee sign.
export const displayFont = "Playfair Display";
export const bodyFont = "Poppins";

const LATIN =
  "U+0000-00FF, U+0131, U+0152-0153, U+2000-206F, U+20AC, U+2122, U+2212";

loadFont({
  family: displayFont,
  url: staticFile("fonts/PlayfairDisplay-Variable.woff2"),
  weight: "400 900",
});
loadFont({
  family: displayFont,
  url: staticFile("fonts/PlayfairDisplay-Italic-Variable.woff2"),
  weight: "400 900",
  style: "italic",
});

for (const [weight, file] of [
  ["400", "Regular"],
  ["500", "Medium"],
  ["600", "SemiBold"],
  ["700", "Bold"],
] as const) {
  loadFont({
    family: bodyFont,
    url: staticFile(`fonts/Poppins-${file}.woff2`),
    weight,
    unicodeRange: LATIN,
  });
}
loadFont({
  family: bodyFont,
  url: staticFile("fonts/Poppins-SemiBold-Devanagari.woff2"),
  weight: "600",
  unicodeRange: "U+20B9",
});
loadFont({
  family: bodyFont,
  url: staticFile("fonts/Poppins-Bold-Devanagari.woff2"),
  weight: "700",
  unicodeRange: "U+20B9",
});
