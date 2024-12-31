import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter } from "next/navigation";

export function UserNav() {
    const router = useRouter();
    const username = localStorage.getItem("username") || "用户";

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        router.push("/auth/login");
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                    <Avatar className="h-10 w-10">
                        <AvatarFallback className="bg-primary/10">
                            {username.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{username}</p>
                    </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    className="text-red-600 cursor-pointer"
                    onClick={handleLogout}
                >
                    退出登录
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
} 