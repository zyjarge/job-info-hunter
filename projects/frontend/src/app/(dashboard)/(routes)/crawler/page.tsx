"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Bot, Plus, Pencil, Trash2, Power, Globe, Calendar, ArrowUpDown } from "lucide-react";
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
import { Crawler, CrawlerBase } from "@/lib/types/crawler";
import { getCrawlers, createCrawler, updateCrawler, deleteCrawler, toggleCrawlerStatus } from "@/lib/api/crawler";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn, formatDate } from "@/lib/utils";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const formSchema = z.object({
    name: z.string().min(2, "名称至少需要2个字符"),
    description: z.string().min(2, "描述至少需要2个字符"),
    homepage: z.string().url("请输入有效的网址"),
    enabled: z.boolean().default(false),
    config: z.object({
        module: z.string().min(1, "请输入模块路径"),
        class: z.string().min(1, "请输入类名"),
        login_module: z.string().min(1, "请输入登录模块路径"),
        login_class: z.string().min(1, "请输入登录类名"),
        site_id: z.string().min(1, "请输入站点ID"),
    }),
});

type FormValues = z.infer<typeof formSchema>;

export default function CrawlerPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [crawlers, setCrawlers] = useState<Crawler[]>([]);
    const [loading, setLoading] = useState(true);
    const [showDialog, setShowDialog] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [editingCrawler, setEditingCrawler] = useState<Crawler | null>(null);
    const [deletingCrawler, setDeletingCrawler] = useState<Crawler | null>(null);
    const [sortField, setSortField] = useState<"id" | "created_at" | "updated_at">("id");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            homepage: "",
            enabled: false,
            config: {
                module: "",
                class: "",
                login_module: "",
                login_class: "",
                site_id: "",
            },
        },
    });

    const loadCrawlers = useCallback(async () => {
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
    }, [toast]);

    useEffect(() => {
        loadCrawlers();
    }, [loadCrawlers]);

    useEffect(() => {
        if (editingCrawler) {
            form.reset({
                name: editingCrawler.name,
                description: editingCrawler.description,
                homepage: editingCrawler.homepage,
                enabled: editingCrawler.enabled,
                config: {
                    module: editingCrawler.config?.module || "",
                    class: editingCrawler.config?.class || "",
                    login_module: editingCrawler.config?.login_module || "",
                    login_class: editingCrawler.config?.login_class || "",
                    site_id: editingCrawler.config?.site_id || "",
                },
            });
        } else {
            form.reset({
                name: "",
                description: "",
                homepage: "",
                enabled: false,
                config: {
                    module: "",
                    class: "",
                    login_module: "",
                    login_class: "",
                    site_id: "",
                },
            });
        }
    }, [editingCrawler, form]);

    async function onSubmit(values: FormValues) {
        try {
            if (editingCrawler) {
                await updateCrawler({
                    id: editingCrawler.id,
                    ...values,
                });
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

    async function handleDelete(crawler: Crawler) {
        setDeletingCrawler(crawler);
        setShowDeleteDialog(true);
    }

    async function confirmDelete() {
        if (!deletingCrawler) return;

        try {
            await deleteCrawler(deletingCrawler.id);
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
        } finally {
            setShowDeleteDialog(false);
            setDeletingCrawler(null);
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

    const sortedCrawlers = useMemo(() => {
        return [...crawlers].sort((a, b) => {
            if (sortField === "id") {
                return sortOrder === "asc" ? a.id - b.id : b.id - a.id;
            }
            const aValue = new Date(a[sortField]).getTime();
            const bValue = new Date(b[sortField]).getTime();
            return sortOrder === "asc" ? aValue - bValue : bValue - aValue;
        });
    }, [crawlers, sortField, sortOrder]);

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
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Select value={sortField} onValueChange={(value: "id" | "created_at" | "updated_at") => setSortField(value)}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="选择排序字段" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="id">按ID</SelectItem>
                                <SelectItem value="created_at">按创建时间</SelectItem>
                                <SelectItem value="updated_at">按更新时间</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select value={sortOrder} onValueChange={(value: "asc" | "desc") => setSortOrder(value)}>
                            <SelectTrigger className="w-[120px]">
                                <SelectValue placeholder="排序方式" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="asc">升序</SelectItem>
                                <SelectItem value="desc">降序</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <Button onClick={handleAdd}>
                        <Plus className="mr-2 h-4 w-4" />
                        添加爬虫
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedCrawlers.map((crawler) => (
                    <Card key={crawler.id}>
                        <CardHeader>
                            <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                    <CardTitle className="text-xl">{crawler.name}</CardTitle>
                                    <CardDescription>
                                        <div className="flex items-center gap-2">
                                            <Globe className="h-4 w-4" />
                                            {(() => {
                                                try {
                                                    const url = new URL(crawler.homepage);
                                                    return (
                                                        <a
                                                            href={url.href}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-blue-500 hover:underline"
                                                        >
                                                            {url.hostname}
                                                        </a>
                                                    );
                                                } catch (error) {
                                                    return (
                                                        <span className="text-muted-foreground">
                                                            {crawler.homepage || "未设置"}
                                                        </span>
                                                    );
                                                }
                                            })()}
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
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-muted-foreground mb-1">创建时间</div>
                                        <div className="text-sm flex items-center gap-2">
                                            <Calendar className="h-4 w-4" />
                                            {formatDate(crawler.created_at)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-muted-foreground mb-1">更新时间</div>
                                        <div className="text-sm flex items-center gap-2">
                                            <Calendar className="h-4 w-4" />
                                            {formatDate(crawler.updated_at)}
                                        </div>
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
                                    className={cn(
                                        crawler.enabled
                                            ? "border-red-500 hover:border-red-600 text-red-500 hover:text-red-600"
                                            : "border-green-500 hover:border-green-600 text-green-500 hover:text-green-600"
                                    )}
                                >
                                    <Power className={`mr-2 h-4 w-4 ${crawler.enabled ? "text-red-500" : "text-green-500"}`} />
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
                                    onClick={() => handleDelete(crawler)}
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
                <DialogContent className="max-w-[1000px] w-[90vw]">
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
                            <div className="grid grid-cols-2 gap-4">
                                {/* 基础配置 */}
                                <div className="space-y-4 rounded-lg border p-4">
                                    <h3 className="text-lg font-medium">基础配置</h3>
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
                                </div>

                                {/* 高级配置 */}
                                <div className="space-y-4 rounded-lg border p-4">
                                    <h3 className="text-lg font-medium">高级配置</h3>
                                    <FormField
                                        control={form.control}
                                        name="config.module"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>模块路径</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="例如：sites_crawlers.zhipin.search" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="config.class"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>类名</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="例如：BossSearcher" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="config.login_module"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>登录模块路径</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="例如：sites_crawlers.zhipin.login" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="config.login_class"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>登录类名</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="例如：BossLogin" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="config.site_id"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>站点ID</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="例如：zhipin.com" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                            </div>

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

            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>确认删除</AlertDialogTitle>
                        <AlertDialogDescription>
                            确定要删除爬虫 "{deletingCrawler?.name}" 吗？此操作无法撤销。
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>取消</AlertDialogCancel>
                        <AlertDialogAction onClick={confirmDelete}>确认删除</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
} 