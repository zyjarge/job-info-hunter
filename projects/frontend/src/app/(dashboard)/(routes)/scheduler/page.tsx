"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, Power, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { useToast } from "@/components/ui/use-toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Schedule, ScheduleFrequency, CrawlerScheduleStatus } from "@/lib/types/scheduler";
import { Crawler } from "@/lib/types/crawler";
import { getCrawlers } from "@/lib/api/crawler";
import {
    getSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    updateCrawlerStatus,
} from "@/lib/api/scheduler";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loading } from "@/components/ui/loading";

const frequencyOptions = [
    { value: "hourly", label: "每小时" },
    { value: "every_6_hours", label: "每6小时" },
    { value: "daily", label: "每天" },
    { value: "weekly", label: "每周" },
] as const;

const formSchema = z.object({
    name: z.string().min(2, "名称至少需要2个字符"),
    keyword: z.string().min(1, "请输入搜索关键词"),
    frequency: z.enum(["hourly", "every_6_hours", "daily", "weekly"] as const),
    crawlerIds: z.array(z.string()).min(1, "请至少选择一个爬虫"),
});

export default function SchedulerPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [crawlers, setCrawlers] = useState<Crawler[]>([]);
    const [loading, setLoading] = useState(true);
    const [showDialog, setShowDialog] = useState(false);
    const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            keyword: "",
            frequency: "daily",
            crawlerIds: [],
        },
    });

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        if (editingSchedule) {
            form.reset({
                name: editingSchedule.name,
                keyword: editingSchedule.keyword,
                frequency: editingSchedule.frequency,
                crawlerIds: editingSchedule.crawlerStatuses.map(s => s.crawlerId),
            });
        } else {
            form.reset({
                name: "",
                keyword: "",
                frequency: "daily",
                crawlerIds: [],
            });
        }
    }, [editingSchedule, form]);

    async function loadData() {
        try {
            const [schedulesData, crawlersData] = await Promise.all([
                getSchedules(),
                getCrawlers(),
            ]);
            setSchedules(schedulesData);
            setCrawlers(crawlersData);
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
            if (editingSchedule) {
                await updateSchedule({
                    id: editingSchedule.id,
                    name: values.name,
                    keyword: values.keyword,
                    frequency: values.frequency,
                });
                toast({
                    title: "更新成功",
                    description: "调度任务已更新",
                });
            } else {
                await createSchedule({
                    name: values.name,
                    keyword: values.keyword,
                    frequency: values.frequency,
                    crawlerIds: values.crawlerIds,
                });
                toast({
                    title: "创建成功",
                    description: "新调度任务已创建",
                });
            }
            setShowDialog(false);
            loadData();
        } catch (error) {
            toast({
                variant: "destructive",
                title: editingSchedule ? "更新失败" : "创建失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleDelete(id: string) {
        if (!confirm("确定要删除这个调度任务吗？")) {
            return;
        }

        try {
            await deleteSchedule(id);
            toast({
                title: "删除成功",
                description: "调度任务已删除",
            });
            loadData();
        } catch (error) {
            toast({
                variant: "destructive",
                title: "删除失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleToggleCrawlerStatus(scheduleId: string, crawlerId: string, currentEnabled: boolean) {
        try {
            await updateCrawlerStatus({
                scheduleId,
                crawlerId,
                enabled: !currentEnabled,
            });
            toast({
                title: currentEnabled ? "停用成功" : "启用成功",
                description: `爬虫已${currentEnabled ? "停用" : "启用"}`,
            });
            loadData();
        } catch (error) {
            toast({
                variant: "destructive",
                title: "操作失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    function handleEdit(schedule: Schedule) {
        setEditingSchedule(schedule);
        setShowDialog(true);
    }

    function handleAdd() {
        setEditingSchedule(null);
        setShowDialog(true);
    }

    function formatFrequency(frequency: ScheduleFrequency): string {
        return frequencyOptions.find(f => f.value === frequency)?.label || frequency;
    }

    function getCrawlerName(crawlerId: string): string {
        return crawlers.find(c => c.id === crawlerId)?.name || crawlerId;
    }

    if (loading) {
        return <Loading />;
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">调度管理</h2>
                <Button onClick={handleAdd}>
                    <Plus className="mr-2 h-4 w-4" />
                    添加调度
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {schedules.map((schedule) => (
                    <Card key={schedule.id} className="relative">
                        <div className="absolute top-4 right-4 flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleEdit(schedule)}
                                title="编辑"
                            >
                                <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDelete(schedule.id)}
                                title="删除"
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>

                        <CardHeader>
                            <CardTitle className="text-xl">{schedule.name}</CardTitle>
                            <CardDescription>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">关键词：</span>
                                        <span className="text-primary">{schedule.keyword}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">执行频率：</span>
                                        <span>{formatFrequency(schedule.frequency)}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">创建时间：</span>
                                        <span>{new Date(schedule.createdAt).toLocaleString()}</span>
                                    </div>
                                </div>
                            </CardDescription>
                        </CardHeader>

                        <CardContent>
                            <div className="space-y-2">
                                <div className="font-medium mb-2">爬虫状态</div>
                                <div className="grid gap-2">
                                    {schedule.crawlerStatuses.map((status) => (
                                        <div
                                            key={status.crawlerId}
                                            className={`p-3 rounded-lg border ${status.enabled
                                                ? "bg-green-50 border-green-200"
                                                : "bg-red-50 border-red-200"
                                                }`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium">
                                                        {getCrawlerName(status.crawlerId)}
                                                    </span>
                                                    {status.totalJobs !== undefined && (
                                                        <span className="text-sm text-muted-foreground">
                                                            采集数量：{status.totalJobs}
                                                        </span>
                                                    )}
                                                    {status.lastError && (
                                                        <TooltipProvider>
                                                            <Tooltip>
                                                                <TooltipTrigger>
                                                                    <AlertCircle className="h-4 w-4 text-red-500" />
                                                                </TooltipTrigger>
                                                                <TooltipContent>
                                                                    <p>{status.lastError}</p>
                                                                </TooltipContent>
                                                            </Tooltip>
                                                        </TooltipProvider>
                                                    )}
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6"
                                                    onClick={() =>
                                                        handleToggleCrawlerStatus(
                                                            schedule.id,
                                                            status.crawlerId,
                                                            status.enabled
                                                        )
                                                    }
                                                >
                                                    <Power
                                                        className={`h-3 w-3 ${status.enabled
                                                            ? "text-green-600"
                                                            : "text-red-600"
                                                            }`}
                                                    />
                                                </Button>
                                            </div>
                                            <div className="mt-2 text-sm text-muted-foreground">
                                                <div>
                                                    上次运行：
                                                    {status.lastRunTime
                                                        ? new Date(status.lastRunTime).toLocaleString()
                                                        : "未运行"}
                                                </div>
                                                <div>
                                                    下次运行：
                                                    {status.nextRunTime
                                                        ? new Date(status.nextRunTime).toLocaleString()
                                                        : "-"}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {schedules.length === 0 && (
                    <Card className="col-span-full">
                        <CardContent className="flex items-center justify-center h-32">
                            <p className="text-muted-foreground">暂无调度任务</p>
                        </CardContent>
                    </Card>
                )}
            </div>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {editingSchedule ? "编辑调度" : "添加调度"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingSchedule
                                ? "修改调度任务的信息"
                                : "添加一个新的调度任务"}
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
                                            <Input placeholder="请输入调度任务名称" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="keyword"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>搜索关键词</FormLabel>
                                        <FormControl>
                                            <Input placeholder="请输入要搜索的职位关键词" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="frequency"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>执行频率</FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="请选择执行频率" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {frequencyOptions.map((option) => (
                                                    <SelectItem key={option.value} value={option.value}>
                                                        {option.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="crawlerIds"
                                render={() => (
                                    <FormItem>
                                        <FormLabel>选择爬虫</FormLabel>
                                        <div className="space-y-2">
                                            {crawlers
                                                .filter((crawler) => crawler.enabled)
                                                .map((crawler) => (
                                                    <FormField
                                                        key={crawler.id}
                                                        control={form.control}
                                                        name="crawlerIds"
                                                        render={({ field }) => {
                                                            return (
                                                                <FormItem
                                                                    key={crawler.id}
                                                                    className="flex flex-row items-start space-x-3 space-y-0"
                                                                >
                                                                    <FormControl>
                                                                        <Checkbox
                                                                            checked={field.value?.includes(crawler.id)}
                                                                            onCheckedChange={(checked) => {
                                                                                return checked
                                                                                    ? field.onChange([
                                                                                        ...(field.value || []),
                                                                                        crawler.id,
                                                                                    ])
                                                                                    : field.onChange(
                                                                                        field.value?.filter(
                                                                                            (value) => value !== crawler.id
                                                                                        )
                                                                                    );
                                                                            }}
                                                                        />
                                                                    </FormControl>
                                                                    <div className="space-y-1 leading-none">
                                                                        <FormLabel className="text-sm font-normal">
                                                                            {crawler.name}
                                                                        </FormLabel>
                                                                    </div>
                                                                </FormItem>
                                                            );
                                                        }}
                                                    />
                                                ))}
                                        </div>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <DialogFooter>
                                <Button type="submit">
                                    {editingSchedule ? "更新" : "创建"}
                                </Button>
                            </DialogFooter>
                        </form>
                    </Form>
                </DialogContent>
            </Dialog>
        </div>
    );
} 