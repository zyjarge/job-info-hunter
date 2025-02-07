import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, Calendar, Home, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
    isCollapsed: boolean;
}

const menuItems = [
    {
        title: "首页",
        icon: Home,
        href: "/",
    },
    {
        title: "爬虫管理",
        icon: Bot,
        href: "/crawler",
    },
    {
        title: "调度管理",
        icon: Calendar,
        href: "/scheduler",
    },
    {
        title: "系统设置",
        icon: Settings,
        href: "/settings",
    },
];

export function Sidebar({ isCollapsed }: SidebarProps) {
    const pathname = usePathname();

    return (
        <div
            className={cn(
                "flex h-full flex-col gap-4 p-4 pt-8 bg-sidebar-background",
                isCollapsed && "items-center"
            )}
        >
            <nav className="flex flex-col gap-4">
                {menuItems.map((item, index) => (
                    <Link
                        key={index}
                        href={item.href}
                        className={cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-sidebar-foreground transition-all hover:text-sidebar-primary",
                            pathname === item.href && "bg-sidebar-accent text-sidebar-accent-foreground",
                            isCollapsed && "justify-center"
                        )}
                    >
                        <item.icon className="h-4 w-4" />
                        {!isCollapsed && <span>{item.title}</span>}
                    </Link>
                ))}
            </nav>
        </div>
    );
} 