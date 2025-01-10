"use client";

import { useEffect, useRef } from "react";

interface CodeBlockProps {
    children: React.ReactNode;
    language?: string;
}

export function CodeBlock({ children, language }: CodeBlockProps) {
    const preRef = useRef<HTMLPreElement>(null);

    useEffect(() => {
        const pre = preRef.current;
        if (!pre) return;

        let scale = 1;
        let isZoomed = false;

        const handleWheel = (e: WheelEvent) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                scale = Math.min(Math.max(0.5, scale + delta), 2);
                pre.style.transform = `scale(${scale})`;
            }
        };

        const handleClick = () => {
            isZoomed = !isZoomed;
            scale = isZoomed ? 1.5 : 1;
            pre.style.transform = `scale(${scale})`;
        };

        pre.addEventListener("wheel", handleWheel);
        pre.addEventListener("click", handleClick);

        return () => {
            pre.removeEventListener("wheel", handleWheel);
            pre.removeEventListener("click", handleClick);
        };
    }, []);

    return (
        <div className="relative overflow-hidden">
            <pre ref={preRef} className={language ? `language-${language}` : ""}>
                <code>{children}</code>
            </pre>
        </div>
    );
} 