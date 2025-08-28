import React from "react";
import {
    AbsoluteFill,
    Audio,
    Img,
    interpolate,
    Series,
    staticFile,
    useCurrentFrame,
    useVideoConfig,
} from "remotion";
import { FONT_FAMILY } from "./fonts";
import { WaitForFonts } from "./WaitForFonts";

export interface AgedReelProps {
    title: string;
    name: string;
    images: {
        year: string;
        age: string;
        image: string;
        caption?: string;
    }[];
    audioFile: string;
    durationPerImage?: number;
    transitionDuration?: number;
    textTransitionDuration?: number;
}

// --- Text Styles ---

const titleStyle: React.CSSProperties = {
    fontFamily: FONT_FAMILY,
    fontSize: "80px",
    fontWeight: 500,
    color: "rgb(255, 255, 255)",
    textAlign: "center",
    lineHeight: "80px",
    textShadow: `
    -3px -3px 0 rgb(0, 0, 0),
    3px -3px 0 rgb(0, 0, 0),
    -3px 3px 0 rgb(0, 0, 0),
    3px 3px 0 rgb(0, 0, 0),
    -3px 0px 0 rgb(0, 0, 0),
    3px 0px 0 rgb(0, 0, 0),
    0px -3px 0 rgb(0, 0, 0),
    0px 3px 0 rgb(0, 0, 0)
  `,
};

const nameStyle: React.CSSProperties = {
    fontFamily: FONT_FAMILY,
    fontSize: "60px",
    fontWeight: 500,
    color: "rgb(255, 255, 255)",
    textAlign: "center",
    lineHeight: "38px",
    textShadow: `
    -2px -2px 0 rgb(0, 0, 0),
    2px -2px 0 rgb(0, 0, 0),
    -2px 2px 0 rgb(0, 0, 0),
    2px 2px 0 rgb(0, 0, 0),
    -2px 0px 0 rgb(0, 0, 0),
    2px 0px 0 rgb(0, 0, 0),
    0px -2px 0 rgb(0, 0, 0),
    0px 2px 0 rgb(0, 0, 0)
  `,
    marginTop: "10px",
};

const yearStyle: React.CSSProperties = {
    fontFamily: FONT_FAMILY,
    fontSize: "60px",
    fontWeight: 500,
    color: "rgb(255, 255, 255)",
    textAlign: "center",
    lineHeight: "48px",
    textShadow: `
    -4px -4px 0 rgb(0, 0, 0),
    4px -4px 0 rgb(0, 0, 0),
    -4px 4px 0 rgb(0, 0, 0),
    4px 4px 0 rgb(0, 0, 0),
    -4px 0px 0 rgb(0, 0, 0),
    4px 0px 0 rgb(0, 0, 0),
    0px -4px 0 rgb(0, 0, 0),
    0px 4px 0 rgb(0, 0, 0)
  `,
};

const ageStyle: React.CSSProperties = {
    fontFamily: FONT_FAMILY,
    fontSize: "60px",
    fontWeight: 700,
    color: "#F57F03",
    textAlign: "center",
    lineHeight: "48px",
    textShadow: `
    -3px -3px 0 rgb(0, 0, 0),
    3px -3px 0 rgb(0, 0, 0),
    -3px 3px 0 rgb(0, 0, 0),
    3px 3px 0 rgb(0, 0, 0),
    -3px 0px 0 rgb(0, 0, 0),
    3px 0px 0 rgb(0, 0, 0),
    0px -3px 0 rgb(0, 0, 0),
    0px 3px 0 rgb(0, 0, 0)
  `,
    marginBottom: "10px",
};

// --- Layout Containers ---

const imageContainerStyle: React.CSSProperties = {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%", // full frame
    overflow: "hidden",
};

const imageStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover", // no black bars
};

const textContainerStyle: React.CSSProperties = {
    position: "absolute",
    bottom: "100px",
    width: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
};

// --- Segment Component ---

const YearSegment: React.FC<{
    year: string;
    age: string;
    image: string;
    transitionDuration?: number;
}> = ({ year, age, image, transitionDuration = 0.5 }) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps } = useVideoConfig();

    const fadeFrames = Math.floor(transitionDuration * fps);

    const opacity = interpolate(
        frame,
        [0, fadeFrames, durationInFrames - fadeFrames, durationInFrames],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    const scale = interpolate(
        frame,
        [0, 15, durationInFrames - 15, durationInFrames],
        [1.1, 1, 1, 1.1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    return (
        <AbsoluteFill>
            {/* Full-screen image */}
            <div style={imageContainerStyle}>
                <Img
                    src={staticFile(image)}
                    style={{
                        ...imageStyle,
                        opacity,
                        transform: `scale(${scale})`,
                    }}
                />
            </div>

            {/* Text overlay */}
            <div style={{ ...textContainerStyle, opacity }}>
                <div style={ageStyle}>{age}</div>
                <div style={yearStyle}>{year}</div>
            </div>
        </AbsoluteFill>
    );
};

// --- Main Reel ---

export const AgedReel: React.FC<AgedReelProps> = ({
    title,
    name,
    images,
    audioFile,
    transitionDuration = 0.5,
    textTransitionDuration = 1.0,
}) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps } = useVideoConfig();

    // Header fade in duration based on textTransitionDuration prop
    const headerFadeFrames = Math.floor(textTransitionDuration * fps);
    const headerOpacity = interpolate(
        frame,
        [0, headerFadeFrames],
        [0, 1],
        { extrapolateRight: "clamp" }
    );

    // Handle empty images gracefully - use safe placeholder
    if (!images || images.length === 0) {
        return (
            <WaitForFonts>
                <AbsoluteFill style={{ backgroundColor: "black", justifyContent: "center", alignItems: "center" }}>
                    <div style={{ color: "white", fontSize: "40px", textAlign: "center" }}>
                        Loading images...
                    </div>
                </AbsoluteFill>
            </WaitForFonts>
        );
    }

    const segmentDuration = Math.floor(durationInFrames / images.length);

    return (
        <WaitForFonts>
            <AbsoluteFill style={{ backgroundColor: "black" }}>
                <Audio src={staticFile(audioFile)} />

                {/* Header at top */}
                <div
                    style={{
                        position: "absolute",
                        bottom: "250px",
                        width: "100%",
                        textAlign: "center",
                        zIndex: 10,
                        opacity: headerOpacity,
                    }}
                >
                    <div style={titleStyle}>{title}</div>
                    <div style={nameStyle}>{name}</div>
                </div>

                {/* Sequence of segments */}
                <Series>
                    {images.map((image, index) => (
                        <Series.Sequence
                            key={index}
                            durationInFrames={segmentDuration}
                            layout="none"
                        >
                            <YearSegment
                                year={image.year}
                                age={image.age}
                                image={image.image}
                                transitionDuration={transitionDuration}
                            />
                        </Series.Sequence>
                    ))}
                </Series>
            </AbsoluteFill>
        </WaitForFonts>
    );
};
