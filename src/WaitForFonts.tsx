import React, { useState, useEffect } from "react";
import { continueRender, delayRender } from "remotion";

export const WaitForFonts: React.FC<{ children: React.ReactNode }> = ({
    children
}) => {
    const [handle] = useState(() => delayRender("Loading fonts"));
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        // Set a much shorter timeout for font loading (2 seconds max)
        const fontLoadingTimeout = setTimeout(() => {
            console.log("Font loading timeout reached, continuing render");
            setIsReady(true);
            continueRender(handle);
        }, 2000);

        // Try to load fonts, but don't wait too long
        const quickFontCheck = setTimeout(() => {
            // Check if fonts are available
            try {
                document.fonts.ready.then(() => {
                    console.log("Fonts ready");
                    clearTimeout(fontLoadingTimeout);
                    setIsReady(true);
                    continueRender(handle);
                }).catch(() => {
                    console.log("Font loading failed, using fallback");
                    clearTimeout(fontLoadingTimeout);
                    setIsReady(true);
                    continueRender(handle);
                });
            } catch {
                console.log("Font API not available, using fallback");
                clearTimeout(fontLoadingTimeout);
                setIsReady(true);
                continueRender(handle);
            }
        }, 100);

        return () => {
            clearTimeout(fontLoadingTimeout);
            clearTimeout(quickFontCheck);
            if (!isReady) {
                continueRender(handle);
            }
        };
    }, [handle, isReady]);

    return <>{children}</>;
};
