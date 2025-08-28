// This is your entry file! Refer to it when you render:
// npx remotion render <entry-file> AgedReel out/video.mp4

import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";
import { AgedReel } from "./AgedReel";

registerRoot(RemotionRoot);

// Export the component for direct access
export { AgedReel };
