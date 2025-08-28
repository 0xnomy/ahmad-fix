// DYNAMIC aged reel data - NO hardcoded local images
// This file provides dynamic templates that work with API-generated content

export interface PhotoData {
    year: string;
    age: string;
    image: string;
    caption?: string;
}

export interface AgedReelData {
    title: string;
    name: string;
    audioFile: string;
    photos: PhotoData[];
    durationPerImage?: number;
    transitionDuration?: number;
}

// API Integration Types for dynamic content
export interface AIGeneratedData extends AgedReelData {
    generation_time?: number;
    ai_generated?: boolean;
    images_count?: number;
}

// DYNAMIC default template - uses placeholder data that gets replaced by API
export const defaultAgedReelData: AgedReelData = {
    title: "My Aging Journey",
    name: "AI Generated",
    audioFile: "aud_0.mp3", // Default audio, gets replaced if custom audio provided
    durationPerImage: 2.0,
    transitionDuration: 0.5,
    photos: [
        // These are just fallback placeholders - real data comes from API
        {
            year: "2024",
            age: "20 Years Old",
            image: "images/placeholder1.png",
            caption: "Age 20"
        },
        {
            year: "2044",
            age: "40 Years Old",
            image: "images/placeholder2.png",
            caption: "Age 40"
        },
        {
            year: "2064",
            age: "60 Years Old",
            image: "images/placeholder3.png",
            caption: "Age 60"
        }
    ]
};

// Dynamic template builder - creates template from API data
export const createDynamicReelData = (
    title: string,
    name: string,
    images: Array<{
        url: string;
        age: string;
        year: string;
        caption?: string;
    }>,
    audioFile: string = "aud_0.mp3",
    durationPerImage: number = 2.0,
    transitionDuration: number = 0.5
): AgedReelData => {
    return {
        title,
        name,
        audioFile,
        durationPerImage,
        transitionDuration,
        photos: images.map(img => ({
            year: img.year,
            age: img.age,
            image: img.url, // Uses API-generated image URLs
            caption: img.caption || img.age
        }))
    };
};

// Helper function to create aging progression with any number of images
export const createAgingProgression = (
    baseConfig: {
        title: string;
        name: string;
        audioFile?: string;
        durationPerImage?: number;
        transitionDuration?: number;
    },
    generatedImages: Array<{
        url: string;
        age: string;
        year?: string;
        caption?: string;
    }>
): AgedReelData => {
    return {
        title: baseConfig.title,
        name: baseConfig.name,
        audioFile: baseConfig.audioFile || "aud_0.mp3",
        durationPerImage: baseConfig.durationPerImage || 2.0,
        transitionDuration: baseConfig.transitionDuration || 0.5,
        photos: generatedImages.map((img, index) => ({
            year: img.year || `Year ${index + 1}`,
            age: img.age,
            image: img.url,
            caption: img.caption || img.age
        }))
    };
};

// Template for single image (when only 1 image is generated)
export const createSingleImageReel = (
    title: string,
    name: string,
    image: { url: string; age: string; caption?: string },
    audioFile: string = "aud_0.mp3"
): AgedReelData => {
    return {
        title,
        name,
        audioFile,
        durationPerImage: 5.0, // Longer duration for single image
        transitionDuration: 0,
        photos: [{
            year: "Now",
            age: image.age,
            image: image.url,
            caption: image.caption || image.age
        }]
    };
};

// Template for comparison reels (2 images - before/after)
export const createComparisonReel = (
    title: string,
    name: string,
    beforeImage: { url: string; age: string },
    afterImage: { url: string; age: string },
    audioFile: string = "aud_0.mp3"
): AgedReelData => {
    return {
        title,
        name,
        audioFile,
        durationPerImage: 3.0,
        transitionDuration: 1.0,
        photos: [
            {
                year: "Before",
                age: beforeImage.age,
                image: beforeImage.url,
                caption: `${beforeImage.age} - Before`
            },
            {
                year: "After",
                age: afterImage.age,
                image: afterImage.url,
                caption: `${afterImage.age} - After`
            }
        ]
    };
};

// NO MORE HARDCODED EXAMPLES - everything is dynamic now
// The system now creates content based on:
// 1. User input (prompt, title, name)
// 2. AI-generated images (any number from 1-20+)
// 3. Dynamic timing calculations
// 4. Custom or default audio
