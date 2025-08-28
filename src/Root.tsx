import React from "react";
import "./style.css";
import { Composition } from "remotion";
import { AgedReel } from "./AgedReel";
import { z } from "zod";

export const RemotionRoot: React.FC = () => {
  // Updated schema to match the new dynamic AgedReel component
  type Schema = {
    title: string;
    name: string;
    images: Array<{
      year: string;
      age: string;
      image: string;
      caption?: string;
    }>;
    audioFile: string;
    durationPerImage?: number;
    transitionDuration?: number;
    textTransitionDuration?: number;
  };

  const schema = z.object({
    title: z.string(),
    name: z.string(),
    images: z.array(
      z.object({
        year: z.string(),
        age: z.string(),
        image: z.string(),
        caption: z.string().optional(),
      })
    ),
    audioFile: z.string(),
    durationPerImage: z.number().optional().default(2.0),
    transitionDuration: z.number().optional().default(0.5),
    textTransitionDuration: z.number().optional().default(1.0),
  }) satisfies z.ZodType<Schema>;

  // Dynamic duration calculation based on actual number of images and timing
  const calculateDuration = (
    numImages: number,
    durationPerImage: number = 2.0,
    transitionDuration: number = 0.5
  ) => {
    const totalImageTime = numImages * durationPerImage;
    const totalTransitionTime = Math.max(0, numImages - 1) * transitionDuration;
    const introOutroTime = 2; // 1 second intro + 1 second outro
    const totalSeconds = Math.max(totalImageTime + totalTransitionTime + introOutroTime, 3);
    const fps = 30;
    return Math.round(totalSeconds * fps);
  };

  return (
    <>
      {/* Dynamic Aged Reel - NO hardcoded default props */}
      <Composition
        id="DynamicAgedReel"
        component={AgedReel as React.ComponentType<z.infer<typeof schema>>}
        durationInFrames={180} // Default 6 seconds (30fps * 6)
        fps={30}
        width={1080}
        height={1920}
        schema={schema}
        calculateMetadata={({ props }: { props: Schema }) => {
          // Dynamically calculate duration based on actual props from API
          const actualDuration = calculateDuration(
            props.images.length,
            props.durationPerImage || 2.0,
            props.transitionDuration || 0.5
          );
          return {
            durationInFrames: actualDuration,
          };
        }}
        // Minimal safe default props - will be replaced by API data
        defaultProps={{
          title: "Loading...",
          name: "Please wait",
          images: [], // Empty array - no placeholder images
          audioFile: "aud_0.mp3",
          durationPerImage: 2.0,
          transitionDuration: 0.5,
          textTransitionDuration: 1.0,
        }}
      />
    </>
  );
};
