"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bot, BarChart, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { UserNav } from "@/components/user-nav";

interface SidebarNavProps extends React.HTMLAttributes<HTMLElement> {
    items: {
        href: string;
        title: string;
        icon: React.ReactNode;
    }[];
}

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        // 检查是否已登录
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/auth/login");
        }
    }, [router]);

    if (!mounted) {
        return null;
    }

    const sidebarNavItems = [
        {
            title: "爬虫管理",
            href: "/crawler",
            icon: <Bot className="h-4 w-4" />,
        },
        {
            title: "任务调度",
            href: "/scheduler",
            icon: <BarChart className="h-4 w-4" />,
        },
        {
            title: "系统设置",
            href: "/settings",
            icon: <Settings className="h-4 w-4" />,
        },
    ];

    return (
        <div className="flex min-h-screen">
            {/* 侧边栏 */}
            <div className="w-[200px] border-r bg-background px-3 py-4 flex flex-col">
                <div className="mb-8">
                    <h2 className="text-lg font-semibold mb-4">Job Info Hunter</h2>
                    <nav className="space-y-1">
                        {sidebarNavItems.map((item) => (
                            <Link key={item.href} href={item.href}>
                                <Button
                                    variant="ghost"
                                    className={cn(
                                        "w-full justify-start",
                                        window.location.pathname === item.href
                                            ? "bg-muted"
                                            : "hover:bg-transparent hover:underline"
                                    )}
                                >
                                    {item.icon}
                                    <span className="ml-2">{item.title}</span>
                                </Button>
                            </Link>
                        ))}
                    </nav>
                </div>
                {/* 用户导航 - 放在底部 */}
                <div className="mt-auto">
                    <UserNav />
                </div>
            </div>
            {/* 主内容区域 */}
            <div className="flex-1 p-8">{children}</div>
        </div>
    );
} 