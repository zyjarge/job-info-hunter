"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { login } from "@/lib/api/auth";

const formSchema = z.object({
    username: z.string().min(1, "请输入用户名"),
    password: z.string().min(1, "请输入密码"),
});

export default function LoginPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [isLoading, setIsLoading] = useState(false);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            username: "",
            password: "",
        },
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        try {
            setIsLoading(true);
            const { access_token } = await login({
                username: values.username,
                password: values.password
            });

            // 保存用户名
            localStorage.setItem("username", values.username);

            // 获取重定向路径
            const redirectPath = localStorage.getItem("redirectPath") || "/crawler";
            localStorage.removeItem("redirectPath"); // 清除重定向路径

            toast({
                title: "登录成功",
                description: "正在跳转...",
            });

            // 延迟跳转以显示成功提示
            setTimeout(() => {
                router.push(redirectPath);
            }, 1000);
        } catch (error) {
            toast({
                variant: "destructive",
                title: "登录失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="container flex h-screen w-screen flex-col items-center justify-center">
            <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
                <div className="flex flex-col space-y-2 text-center">
                    <h1 className="text-2xl font-semibold tracking-tight">欢迎回来</h1>
                    <p className="text-sm text-muted-foreground">
                        请输入您的用户名和密码登录
                    </p>
                </div>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="username"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>用户名</FormLabel>
                                    <FormControl>
                                        <Input
                                            placeholder="请输入用户名"
                                            {...field}
                                            disabled={isLoading}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="password"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>密码</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="password"
                                            placeholder="请输入密码"
                                            {...field}
                                            disabled={isLoading}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? "登录中..." : "登录"}
                        </Button>
                    </form>
                </Form>

                <div className="flex flex-col space-y-4 text-center text-sm">
                    <div className="text-muted-foreground">
                        测试账号: admin<br />
                        测试密码: secret
                    </div>
                    <div>
                        还没有账号？{" "}
                        <Link href="/auth/register" className="text-primary hover:underline">
                            立即注册
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
} 