"use client";

import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar";
import { DashboardSidebar } from "./dashboard-sidebar";
import { UserNav } from "./user-nav";

interface DashboardLayoutProps {
    children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    return (
        <SidebarProvider>
            <div className="flex min-h-screen">
                <DashboardSidebar />
                <SidebarInset className="flex w-[90vw] flex-col">
                    <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b bg-background px-6">
                        <SidebarTrigger />
                        <div className="flex flex-1 items-center justify-between">
                            <h2 className="text-lg font-semibold">职位信息猎手</h2>
                            <UserNav />
                        </div>
                    </header>
                    <main className="flex-1 p-6 w-full">
                        {children}
                    </main>
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
} 