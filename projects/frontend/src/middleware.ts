import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 需要认证的路由
const protectedRoutes = ["/crawler", "/scheduler"];
// 认证路由
const authRoutes = ["/auth/login", "/auth/register"];

export function middleware(request: NextRequest) {
    const token = request.cookies.get("token");
    const { pathname } = request.nextUrl;

    // 处理根路由
    if (pathname === "/") {
        if (token) {
            return NextResponse.redirect(new URL("/crawler", request.url));
        } else {
            return NextResponse.redirect(new URL("/auth/login", request.url));
        }
    }

    // 如果访问需要认证的路由，但没有 token，重定向到登录页
    if (protectedRoutes.some(route => pathname.startsWith(route)) && !token) {
        return NextResponse.redirect(new URL("/auth/login", request.url));
    }

    // 如果已经有 token，访问登录或注册页面，重定向到首页
    if (authRoutes.some(route => pathname.startsWith(route)) && token) {
        return NextResponse.redirect(new URL("/crawler", request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * 匹配所有需要认证的路由:
         * - /crawler
         * - /scheduler
         * 匹配所有认证相关的路由:
         * - /auth/login
         * - /auth/register
         * 匹配根路由
         * - /
         */
        "/",
        "/crawler/:path*",
        "/scheduler/:path*",
        "/auth/:path*"
    ],
}; 