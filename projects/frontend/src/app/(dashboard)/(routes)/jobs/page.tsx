"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, Filter, ArrowUpDown, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/components/ui/use-toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { JobPost, JobSearchParams } from "@/lib/types/job";
import { searchJobs } from "@/lib/api/job";
import { getCrawlers } from "@/lib/api/crawler";
import { Crawler } from "@/lib/types/crawler";
import { Loading } from "@/components/ui/loading";

const formSchema = z.object({
    keyword: z.string().min(1, "请输入搜索关键词"),
    location: z.string().optional(),
    company: z.string().optional(),
    salary_min: z.number().optional(),
    salary_max: z.number().optional(),
    site_ids: z.array(z.string()).optional(),
    sort_by: z.enum(["timestamp", "salary"]).optional(),
    sort_order: z.enum(["asc", "desc"]).optional(),
});

export default function JobsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { toast } = useToast();
    const [jobs, setJobs] = useState<JobPost[]>([]);
    const [crawlers, setCrawlers] = useState<Crawler[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            keyword: searchParams.get("keyword") || "",
            location: searchParams.get("location") || "",
            company: searchParams.get("company") || "",
            salary_min: searchParams.get("salary_min")
                ? Number(searchParams.get("salary_min"))
                : undefined,
            salary_max: searchParams.get("salary_max")
                ? Number(searchParams.get("salary_max"))
                : undefined,
            site_ids: searchParams.get("site_ids")
                ? searchParams.get("site_ids")!.split(",")
                : [],
            sort_by: (searchParams.get("sort_by") as "timestamp" | "salary") || "timestamp",
            sort_order: (searchParams.get("sort_order") as "asc" | "desc") || "desc",
        },
    });

    useEffect(() => {
        loadCrawlers();
    }, []);

    useEffect(() => {
        const values = form.getValues();
        handleSearch(values);
    }, [page]);

    async function loadCrawlers() {
        try {
            const data = await getCrawlers();
            setCrawlers(data);
        } catch (error) {
            toast({
                variant: "destructive",
                title: "加载爬虫列表失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleSearch(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            const params: JobSearchParams = {
                ...values,
                page,
                page_size: pageSize,
            };
            const response = await searchJobs(params);
            setJobs(response.items);
            setTotal(response.total);
        } catch (error) {
            toast({
                variant: "destructive",
                title: "搜索失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setLoading(false);
        }
    }

    function formatSalary(salary: string): string {
        return salary.toUpperCase();
    }

    function formatTimestamp(timestamp: string): string {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const minutes = Math.floor(diff / 1000 / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) {
            return `${days}天前`;
        }
        if (hours > 0) {
            return `${hours}小时前`;
        }
        if (minutes > 0) {
            return `${minutes}分钟前`;
        }
        return "刚刚";
    }

    function getCrawlerName(siteId: string): string {
        return crawlers.find(c => c.id === siteId)?.name || siteId;
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">职位搜索</h2>
            </div>

            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <Form {...form}>
                        <form
                            onSubmit={form.handleSubmit(handleSearch)}
                            className="flex items-center gap-2"
                        >
                            <FormField
                                control={form.control}
                                name="keyword"
                                render={({ field }) => (
                                    <FormItem className="flex-1">
                                        <FormControl>
                                            <Input
                                                placeholder="搜索职位名称、描述或要求"
                                                {...field}
                                            />
                                        </FormControl>
                                    </FormItem>
                                )}
                            />
                            <Button type="submit" disabled={loading}>
                                <Search className="mr-2 h-4 w-4" />
                                搜索
                            </Button>
                        </form>
                    </Form>
                </div>

                <Sheet>
                    <SheetTrigger asChild>
                        <Button variant="outline">
                            <Filter className="mr-2 h-4 w-4" />
                            筛选
                        </Button>
                    </SheetTrigger>
                    <SheetContent>
                        <SheetHeader>
                            <SheetTitle>搜索筛选</SheetTitle>
                            <SheetDescription>
                                设置筛选条件以缩小搜索范围
                            </SheetDescription>
                        </SheetHeader>
                        <div className="mt-4">
                            <Form {...form}>
                                <form onSubmit={form.handleSubmit(handleSearch)} className="space-y-4">
                                    <FormField
                                        control={form.control}
                                        name="location"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>工作地点</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="输入城市名称" {...field} />
                                                </FormControl>
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="company"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>公司名称</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="输入公司名称" {...field} />
                                                </FormControl>
                                            </FormItem>
                                        )}
                                    />
                                    <div className="grid grid-cols-2 gap-2">
                                        <FormField
                                            control={form.control}
                                            name="salary_min"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>最低薪资(K)</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="最低薪资"
                                                            {...field}
                                                            onChange={e =>
                                                                field.onChange(
                                                                    e.target.value ? Number(e.target.value) : undefined
                                                                )
                                                            }
                                                        />
                                                    </FormControl>
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name="salary_max"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>最高薪资(K)</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="最高薪资"
                                                            {...field}
                                                            onChange={e =>
                                                                field.onChange(
                                                                    e.target.value ? Number(e.target.value) : undefined
                                                                )
                                                            }
                                                        />
                                                    </FormControl>
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                    <FormField
                                        control={form.control}
                                        name="site_ids"
                                        render={() => (
                                            <FormItem>
                                                <FormLabel>数据来源</FormLabel>
                                                <div className="space-y-2">
                                                    {crawlers
                                                        .filter(crawler => crawler.enabled)
                                                        .map(crawler => (
                                                            <FormField
                                                                key={crawler.id}
                                                                control={form.control}
                                                                name="site_ids"
                                                                render={({ field }) => {
                                                                    return (
                                                                        <FormItem
                                                                            key={crawler.id}
                                                                            className="flex flex-row items-start space-x-3 space-y-0"
                                                                        >
                                                                            <FormControl>
                                                                                <Checkbox
                                                                                    checked={field.value?.includes(
                                                                                        crawler.id
                                                                                    )}
                                                                                    onCheckedChange={checked => {
                                                                                        return checked
                                                                                            ? field.onChange([
                                                                                                ...(field.value || []),
                                                                                                crawler.id,
                                                                                            ])
                                                                                            : field.onChange(
                                                                                                field.value?.filter(
                                                                                                    value =>
                                                                                                        value !==
                                                                                                        crawler.id
                                                                                                )
                                                                                            );
                                                                                    }}
                                                                                />
                                                                            </FormControl>
                                                                            <FormLabel className="text-sm font-normal">
                                                                                {crawler.name}
                                                                            </FormLabel>
                                                                        </FormItem>
                                                                    );
                                                                }}
                                                            />
                                                        ))}
                                                </div>
                                            </FormItem>
                                        )}
                                    />
                                    <div className="grid grid-cols-2 gap-2">
                                        <FormField
                                            control={form.control}
                                            name="sort_by"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>排序字段</FormLabel>
                                                    <Select
                                                        onValueChange={field.onChange}
                                                        defaultValue={field.value}
                                                    >
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="选择排序字段" />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            <SelectItem value="timestamp">发布时间</SelectItem>
                                                            <SelectItem value="salary">薪资</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name="sort_order"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>排序方式</FormLabel>
                                                    <Select
                                                        onValueChange={field.onChange}
                                                        defaultValue={field.value}
                                                    >
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="选择排序方式" />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            <SelectItem value="desc">降序</SelectItem>
                                                            <SelectItem value="asc">升序</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                    <Button type="submit" className="w-full" disabled={loading}>
                                        应用筛选
                                    </Button>
                                </form>
                            </Form>
                        </div>
                    </SheetContent>
                </Sheet>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {loading ? (
                    <div className="col-span-full h-[300px]">
                        <Loading />
                    </div>
                ) : (
                    <>
                        {jobs.map(job => (
                            <Card key={`${job.site_id}_${job.job_id}`}>
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <CardTitle className="text-lg">{job.title}</CardTitle>
                                            <CardDescription>{job.company}</CardDescription>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            asChild
                                        >
                                            <a href={job.url} target="_blank" rel="noopener noreferrer">
                                                <ExternalLink className="h-4 w-4" />
                                            </a>
                                        </Button>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-lg font-medium text-primary">
                                                {formatSalary(job.salary)}
                                            </span>
                                            <span>{job.location}</span>
                                        </div>
                                        <Separator />
                                        <div className="space-y-1">
                                            <div className="text-sm text-muted-foreground">职位描述：</div>
                                            <div className="text-sm line-clamp-2">{job.description}</div>
                                        </div>
                                        <div className="space-y-1">
                                            <div className="text-sm text-muted-foreground">任职要求：</div>
                                            <div className="text-sm line-clamp-2">{job.requirements}</div>
                                        </div>
                                    </div>
                                </CardContent>
                                <CardFooter>
                                    <div className="flex items-center justify-between w-full text-sm text-muted-foreground">
                                        <span>{getCrawlerName(job.site_id)}</span>
                                        <span>{formatTimestamp(job.timestamp)}</span>
                                    </div>
                                </CardFooter>
                            </Card>
                        ))}

                        {jobs.length === 0 && (
                            <Card className="col-span-full">
                                <CardContent className="flex items-center justify-center h-32">
                                    <p className="text-muted-foreground">
                                        {form.getValues("keyword")
                                            ? "未找到匹配的职位"
                                            : "请输入关键词搜索职位"}
                                    </p>
                                </CardContent>
                            </Card>
                        )}
                    </>
                )}
            </div>

            {total > pageSize && (
                <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                        共 {total} 个职位
                    </div>
                    <div className="flex items-center space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1 || loading}
                        >
                            上一页
                        </Button>
                        <div className="text-sm">
                            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(p => p + 1)}
                            disabled={page >= Math.ceil(total / pageSize) || loading}
                        >
                            下一页
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
} 