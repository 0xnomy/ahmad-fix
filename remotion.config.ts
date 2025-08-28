// See all configuration options: https://remotion.dev/docs/config
// Each option also is available as a CLI flag: https://remotion.dev/docs/cli

// Note: When using the Node.JS APIs, the config file doesn't apply. Instead, pass options directly to the APIs

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// Increase timeout to handle font loading and complex renders
Config.setDelayRenderTimeoutInMilliseconds(10000); // 10 seconds max for delayRender()
Config.setTimeoutInMilliseconds(120000); // 2 minutes total render timeout

// Memory and performance optimizations
Config.setChromiumOpenGlRenderer("swangle"); // Use software rendering instead of EGL
Config.setConcurrency(1); // Single thread to prevent memory issues

// Enable Tailwind
Config.overrideWebpackConfig(enableTailwind);

// Note: Text transitions and fade effects are implemented in the React components
// using interpolate() for smooth fade in/out effects based on transitionDuration prop
