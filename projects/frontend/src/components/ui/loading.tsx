"use client";

import { Bot } from "lucide-react";

export function Loading() {
    return (
        <div className="flex items-center justify-center h-full">
            <Bot className="h-8 w-8 animate-spin" />
        </div>
    );
} 