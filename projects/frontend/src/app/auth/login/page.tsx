"use client";

import { useState } from "react";
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
    username: z.string().min(2, "用户名至少需要2个字符"),
    password: z.string().min(6, "密码至少需要6个字符"),
});

type FormValues = z.infer<typeof formSchema>;

export default function LoginPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            username: "",
            password: "",
        },
    });

    async function onSubmit(values: FormValues) {
        try {
            setLoading(true);
            const { access_token } = await login({
                username: values.username,
                password: values.password
            });
            localStorage.setItem("token", access_token);
            localStorage.setItem("username", values.username);

            // 获取重定向路径
            const redirectPath = localStorage.getItem("redirectPath") || "/";
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
            setLoading(false);
        }
    }

    return (
        <div className="flex items-center justify-center min-h-screen bg-background">
            <div className="w-full max-w-[400px] p-6 space-y-6 bg-card rounded-lg shadow-lg">
                <div className="space-y-2 text-center">
                    <h1 className="text-2xl font-bold">登录</h1>
                    <p className="text-sm text-muted-foreground">
                        输入您的账号密码登录系统
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
                                            disabled={loading}
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
                                            disabled={loading}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? "登录中..." : "登录"}
                        </Button>
                    </form>
                </Form>
            </div>
        </div>
    );
} 