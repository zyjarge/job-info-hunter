"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    LayoutDashboard,
    Bot,
    Calendar,
    Search,
    UserCircle,
} from "lucide-react";

const sidebarNavItems = [
    {
        title: "概览",
        href: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "爬虫管理",
        href: "/crawler",
        icon: Bot,
    },
    {
        title: "调度管理",
        href: "/scheduler",
        icon: Calendar,
    },
    {
        title: "职位搜索",
        href: "/jobs",
        icon: Search,
    },
    {
        title: "个人信息",
        href: "/profile",
        icon: UserCircle,
    },
];

export function DashboardSidebar() {
    const pathname = usePathname();

    return (
        <nav className="flex h-screen w-[10vw] flex-col border-r bg-background px-3 py-4">
            <div className="flex h-14 items-center border-b px-2">
                <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
                    <Bot className="h-6 w-6" />
                    <span>Job Hunter</span>
                </Link>
            </div>
            <div className="flex-1 space-y-1 py-4">
                {sidebarNavItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Button
                            key={item.href}
                            variant={pathname === item.href ? "secondary" : "ghost"}
                            className={cn(
                                "w-full justify-start gap-2",
                                pathname === item.href && "bg-secondary"
                            )}
                            asChild
                        >
                            <Link href={item.href}>
                                <Icon className="h-4 w-4" />
                                {item.title}
                            </Link>
                        </Button>
                    );
                })}
            </div>
        </nav>
    );
} 