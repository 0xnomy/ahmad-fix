import { loadFont, fontFamily } from "@remotion/google-fonts/Poppins";

// Load only essential font weights and subsets to avoid timeout issues
export const poppinsFont = loadFont("normal", {
    weights: ["400", "500"],
    subsets: ["latin"],  // Only load latin subset
});

export const FONT_FAMILY = fontFamily;

export const waitForFonts = () => {
    return poppinsFont.waitUntilDone();
};
