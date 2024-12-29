"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Bot, Plus, Pencil, Trash2, Power, Globe, Calendar, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
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
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Crawler } from "@/lib/types/crawler";
import { getCrawlers, createCrawler, updateCrawler, deleteCrawler, toggleCrawlerStatus } from "@/lib/api/crawler";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const formSchema = z.object({
    name: z.string().min(2, "名称至少需要2个字符"),
    description: z.string().min(2, "描述至少需要2个字符"),
    homepage: z.string().url("请输入有效的网址"),
    enabled: z.boolean().optional(),
});

export default function CrawlerPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [crawlers, setCrawlers] = useState<Crawler[]>([]);
    const [loading, setLoading] = useState(true);
    const [showDialog, setShowDialog] = useState(false);
    const [editingCrawler, setEditingCrawler] = useState<Crawler | null>(null);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            homepage: "",
            enabled: false,
        },
    });

    useEffect(() => {
        loadCrawlers();
    }, []);

    useEffect(() => {
        if (editingCrawler) {
            form.reset({
                name: editingCrawler.name,
                description: editingCrawler.description,
                homepage: editingCrawler.homepage,
                enabled: editingCrawler.enabled,
            });
        } else {
            form.reset({
                name: "",
                description: "",
                homepage: "",
                enabled: false,
            });
        }
    }, [editingCrawler, form]);

    async function loadCrawlers() {
        try {
            const data = await getCrawlers();
            setCrawlers(data);
        } catch (error) {
            toast({
                variant: "destructive",
                title: "加载失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setLoading(false);
        }
    }

    async function onSubmit(values: z.infer<typeof formSchema>) {
        try {
            if (editingCrawler) {
                await updateCrawler({ id: editingCrawler.id, ...values });
                toast({
                    title: "更新成功",
                    description: "爬虫信息已更新",
                });
            } else {
                await createCrawler(values);
                toast({
                    title: "创建成功",
                    description: "新爬虫已创建",
                });
            }
            setShowDialog(false);
            loadCrawlers();
        } catch (error) {
            toast({
                variant: "destructive",
                title: editingCrawler ? "更新失败" : "创建失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleDelete(id: string) {
        if (!confirm("确定要删除这个爬虫吗？")) {
            return;
        }

        try {
            await deleteCrawler(id);
            toast({
                title: "删除成功",
                description: "爬虫已删除",
            });
            loadCrawlers();
        } catch (error) {
            toast({
                variant: "destructive",
                title: "删除失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleToggleStatus(crawler: Crawler) {
        try {
            await toggleCrawlerStatus(crawler.id);
            toast({
                title: crawler.enabled ? "停用成功" : "启用成功",
                description: `爬虫已${crawler.enabled ? "停用" : "启用"}`,
            });
            loadCrawlers();
        } catch (error) {
            toast({
                variant: "destructive",
                title: "操作失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    function handleEdit(crawler: Crawler) {
        setEditingCrawler(crawler);
        setShowDialog(true);
    }

    function handleAdd() {
        setEditingCrawler(null);
        setShowDialog(true);
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Bot className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">爬虫管理</h2>
                <Button onClick={handleAdd}>
                    <Plus className="mr-2 h-4 w-4" />
                    添加爬虫
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {crawlers.map((crawler) => (
                    <Card key={crawler.id}>
                        <CardHeader>
                            <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                    <CardTitle className="text-xl">{crawler.name}</CardTitle>
                                    <CardDescription>
                                        <div className="flex items-center gap-2">
                                            <Globe className="h-4 w-4" />
                                            <a
                                                href={crawler.homepage}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-500 hover:underline"
                                            >
                                                {new URL(crawler.homepage).hostname}
                                            </a>
                                        </div>
                                    </CardDescription>
                                </div>
                                <Badge
                                    className={cn(
                                        "ml-2",
                                        crawler.enabled ? "bg-green-500 hover:bg-green-600" : "bg-red-500 hover:bg-red-600"
                                    )}
                                >
                                    {crawler.enabled ? "已启用" : "已停用"}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <div className="text-sm text-muted-foreground mb-1">描述</div>
                                    <div className="text-sm">{crawler.description}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-muted-foreground mb-1">创建时间</div>
                                    <div className="text-sm flex items-center gap-2">
                                        <Calendar className="h-4 w-4" />
                                        {new Date(crawler.createdAt).toLocaleDateString()}
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter>
                            <div className="flex items-center justify-end w-full gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleToggleStatus(crawler)}
                                >
                                    <Power className={`mr-2 h-4 w-4 ${crawler.enabled ? "text-green-600" : "text-red-600"}`} />
                                    {crawler.enabled ? "停用" : "启用"}
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleEdit(crawler)}
                                >
                                    <Pencil className="mr-2 h-4 w-4" />
                                    编辑
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleDelete(crawler.id)}
                                >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    删除
                                </Button>
                            </div>
                        </CardFooter>
                    </Card>
                ))}

                {crawlers.length === 0 && (
                    <Card className="col-span-full">
                        <CardContent className="flex items-center justify-center h-32">
                            <p className="text-muted-foreground">暂无爬虫，请点击右上角添加</p>
                        </CardContent>
                    </Card>
                )}
            </div>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {editingCrawler ? "编辑爬虫" : "添加爬虫"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingCrawler
                                ? "修改爬虫的信息"
                                : "添加一个新的网站爬虫"}
                        </DialogDescription>
                    </DialogHeader>

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>名称</FormLabel>
                                        <FormControl>
                                            <Input placeholder="请输入爬虫名称" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="description"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>描述</FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="请输入爬虫的详细描述信息"
                                                className="min-h-[100px]"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="homepage"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>主页</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="url"
                                                placeholder="请输入网站主页"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="enabled"
                                render={({ field }) => (
                                    <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                                        <FormControl>
                                            <Checkbox
                                                checked={field.value}
                                                onCheckedChange={field.onChange}
                                            />
                                        </FormControl>
                                        <div className="space-y-1 leading-none">
                                            <FormLabel>
                                                启用状态
                                            </FormLabel>
                                            <p className="text-sm text-muted-foreground">
                                                启用后可以在创建调度任务时选择该爬虫
                                            </p>
                                        </div>
                                    </FormItem>
                                )}
                            />
                            <DialogFooter>
                                <Button type="submit">
                                    {editingCrawler ? "更新" : "创建"}
                                </Button>
                            </DialogFooter>
                        </form>
                    </Form>
                </DialogContent>
            </Dialog>
        </div>
    );
} 