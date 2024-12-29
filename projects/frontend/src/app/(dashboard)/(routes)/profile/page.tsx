"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, Upload, X, Plus, Minus, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
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
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/components/ui/use-toast";
import { Profile, UpdateProfileRequest } from "@/lib/types/profile";
import { getProfile, updateProfile, uploadAvatar, uploadResume } from "@/lib/api/profile";

const formSchema = z.object({
    name: z.string().min(2, "姓名至少2个字符"),
    phone: z.string().regex(/^1[3-9]\d{9}$/, "请输入正确的手机号"),
    location: z.string().min(2, "请输入所在城市"),
    title: z.string().min(2, "请输入当前职位"),
    experience: z.number().min(0, "工作年限不能为负数"),
    education: z.object({
        degree: z.string().min(1, "请选择学历"),
        school: z.string().min(2, "请输入学校名称"),
        major: z.string().min(2, "请输入专业名称"),
        graduation_year: z.number().min(1900).max(new Date().getFullYear() + 10),
    }),
    skills: z.array(z.string()).min(1, "请至少添加一个技能标签"),
    job_preferences: z.object({
        expected_salary_min: z.number().min(0, "薪资不能为负数").optional(),
        expected_salary_max: z.number().min(0, "薪资不能为负数").optional(),
        preferred_locations: z.array(z.string()).min(1, "请至少添加一个期望城市"),
        preferred_industries: z.array(z.string()).min(1, "请至少添加一个期望行业"),
        preferred_positions: z.array(z.string()).min(1, "请至少添加一个期望职位"),
    }),
});

const DEGREE_OPTIONS = [
    { value: "高中", label: "高中" },
    { value: "专科", label: "专科" },
    { value: "本科", label: "本科" },
    { value: "硕士", label: "硕士" },
    { value: "博士", label: "博士" },
];

export default function ProfilePage() {
    const router = useRouter();
    const { toast } = useToast();
    const [profile, setProfile] = useState<Profile | null>(null);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [newSkill, setNewSkill] = useState("");
    const [newLocation, setNewLocation] = useState("");
    const [newIndustry, setNewIndustry] = useState("");
    const [newPosition, setNewPosition] = useState("");

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            phone: "",
            location: "",
            title: "",
            experience: 0,
            education: {
                degree: "",
                school: "",
                major: "",
                graduation_year: new Date().getFullYear(),
            },
            skills: [],
            job_preferences: {
                expected_salary_min: undefined,
                expected_salary_max: undefined,
                preferred_locations: [],
                preferred_industries: [],
                preferred_positions: [],
            },
        },
    });

    useEffect(() => {
        loadProfile();
    }, []);

    async function loadProfile() {
        try {
            const data = await getProfile();
            setProfile(data);
            form.reset({
                name: data.name,
                phone: data.phone || "",
                location: data.location || "",
                title: data.title || "",
                experience: data.experience || 0,
                education: data.education || {
                    degree: "",
                    school: "",
                    major: "",
                    graduation_year: new Date().getFullYear(),
                },
                skills: data.skills || [],
                job_preferences: {
                    expected_salary_min: data.job_preferences?.expected_salary_min,
                    expected_salary_max: data.job_preferences?.expected_salary_max,
                    preferred_locations: data.job_preferences?.preferred_locations || [],
                    preferred_industries: data.job_preferences?.preferred_industries || [],
                    preferred_positions: data.job_preferences?.preferred_positions || [],
                },
            });
        } catch (error) {
            toast({
                variant: "destructive",
                title: "加载个人信息失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        }
    }

    async function handleSubmit(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            const data = await updateProfile(values);
            setProfile(data);
            toast({
                title: "更新成功",
                description: "个人信息已更新",
            });
        } catch (error) {
            toast({
                variant: "destructive",
                title: "更新失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setLoading(false);
        }
    }

    async function handleAvatarUpload(event: React.ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploading(true);
        try {
            const url = await uploadAvatar(file);
            const data = await updateProfile({ avatar: url });
            setProfile(data);
            toast({
                title: "上传成功",
                description: "头像已更新",
            });
        } catch (error) {
            toast({
                variant: "destructive",
                title: "上传失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setUploading(false);
        }
    }

    async function handleResumeUpload(event: React.ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploading(true);
        try {
            const url = await uploadResume(file);
            const data = await updateProfile({ resume_url: url });
            setProfile(data);
            toast({
                title: "上传成功",
                description: "简历已更新",
            });
        } catch (error) {
            toast({
                variant: "destructive",
                title: "上传失败",
                description: error instanceof Error ? error.message : "请稍后重试",
            });
        } finally {
            setUploading(false);
        }
    }

    function handleAddSkill(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter" && newSkill) {
            event.preventDefault();
            const skills = form.getValues("skills");
            if (!skills.includes(newSkill)) {
                form.setValue("skills", [...skills, newSkill]);
            }
            setNewSkill("");
        }
    }

    function handleRemoveSkill(skill: string) {
        const skills = form.getValues("skills");
        form.setValue(
            "skills",
            skills.filter(s => s !== skill)
        );
    }

    function handleAddLocation(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter" && newLocation) {
            event.preventDefault();
            const locations = form.getValues("job_preferences.preferred_locations");
            if (!locations.includes(newLocation)) {
                form.setValue("job_preferences.preferred_locations", [...locations, newLocation]);
            }
            setNewLocation("");
        }
    }

    function handleRemoveLocation(location: string) {
        const locations = form.getValues("job_preferences.preferred_locations");
        form.setValue(
            "job_preferences.preferred_locations",
            locations.filter(l => l !== location)
        );
    }

    function handleAddIndustry(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter" && newIndustry) {
            event.preventDefault();
            const industries = form.getValues("job_preferences.preferred_industries");
            if (!industries.includes(newIndustry)) {
                form.setValue("job_preferences.preferred_industries", [...industries, newIndustry]);
            }
            setNewIndustry("");
        }
    }

    function handleRemoveIndustry(industry: string) {
        const industries = form.getValues("job_preferences.preferred_industries");
        form.setValue(
            "job_preferences.preferred_industries",
            industries.filter(i => i !== industry)
        );
    }

    function handleAddPosition(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter" && newPosition) {
            event.preventDefault();
            const positions = form.getValues("job_preferences.preferred_positions");
            if (!positions.includes(newPosition)) {
                form.setValue("job_preferences.preferred_positions", [...positions, newPosition]);
            }
            setNewPosition("");
        }
    }

    function handleRemovePosition(position: string) {
        const positions = form.getValues("job_preferences.preferred_positions");
        form.setValue(
            "job_preferences.preferred_positions",
            positions.filter(p => p !== position)
        );
    }

    if (!profile) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">个人信息</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>基本信息</CardTitle>
                        <CardDescription>完善你的基本信息，让招聘方更了解你</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                                <div className="flex items-center space-x-4">
                                    <div className="relative h-20 w-20">
                                        <Image
                                            src={profile.avatar || "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan"}
                                            alt="头像"
                                            className="rounded-full"
                                            fill
                                            unoptimized
                                            style={{ objectFit: "cover" }}
                                        />
                                        <label
                                            htmlFor="avatar-upload"
                                            className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full cursor-pointer opacity-0 hover:opacity-100 transition-opacity"
                                        >
                                            <Upload className="h-6 w-6 text-white" />
                                        </label>
                                        <input
                                            id="avatar-upload"
                                            type="file"
                                            accept="image/*"
                                            className="hidden"
                                            onChange={handleAvatarUpload}
                                            disabled={uploading}
                                        />
                                    </div>
                                    <div>
                                        <h3 className="font-medium">{profile.name}</h3>
                                        <p className="text-sm text-muted-foreground">{profile.email}</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <FormField
                                        control={form.control}
                                        name="name"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>姓名</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="请输入姓名" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="phone"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>手机号</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="请输入手机号" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="location"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>所在城市</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="请输入所在城市" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="title"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>当前职位</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="请输入当前职位" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="experience"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>工作年限</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        type="number"
                                                        placeholder="请输入工作年限"
                                                        {...field}
                                                        onChange={e => field.onChange(Number(e.target.value))}
                                                    />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>

                                <Separator />

                                <div className="space-y-4">
                                    <h4 className="font-medium">教育背景</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <FormField
                                            control={form.control}
                                            name="education.degree"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>学历</FormLabel>
                                                    <Select
                                                        onValueChange={field.onChange}
                                                        defaultValue={field.value}
                                                    >
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="请选择学历" />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            {DEGREE_OPTIONS.map(option => (
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
                                            name="education.school"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>学校</FormLabel>
                                                    <FormControl>
                                                        <Input placeholder="请输入学校名称" {...field} />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name="education.major"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>专业</FormLabel>
                                                    <FormControl>
                                                        <Input placeholder="请输入专业名称" {...field} />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name="education.graduation_year"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>毕业年份</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="请输入毕业年份"
                                                            {...field}
                                                            onChange={e => field.onChange(Number(e.target.value))}
                                                        />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                </div>

                                <Separator />

                                <div className="space-y-4">
                                    <h4 className="font-medium">技能标签</h4>
                                    <div className="space-y-2">
                                        <Input
                                            placeholder="输入技能标签，按回车添加"
                                            value={newSkill}
                                            onChange={e => setNewSkill(e.target.value)}
                                            onKeyDown={handleAddSkill}
                                        />
                                        <div className="flex flex-wrap gap-2">
                                            {form.getValues("skills").map(skill => (
                                                <Badge
                                                    key={skill}
                                                    variant="secondary"
                                                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                                                    onClick={() => handleRemoveSkill(skill)}
                                                >
                                                    {skill}
                                                    <X className="ml-1 h-3 w-3" />
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                <div className="space-y-4">
                                    <h4 className="font-medium">求职意向</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <FormField
                                            control={form.control}
                                            name="job_preferences.expected_salary_min"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>期望最低薪资(K)</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="请输入期望最低薪资"
                                                            {...field}
                                                            onChange={e =>
                                                                field.onChange(
                                                                    e.target.value ? Number(e.target.value) : undefined
                                                                )
                                                            }
                                                        />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name="job_preferences.expected_salary_max"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>期望最高薪资(K)</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="请输入期望最高薪资"
                                                            {...field}
                                                            onChange={e =>
                                                                field.onChange(
                                                                    e.target.value ? Number(e.target.value) : undefined
                                                                )
                                                            }
                                                        />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <FormLabel>期望城市</FormLabel>
                                        <Input
                                            placeholder="输入期望城市，按回车添加"
                                            value={newLocation}
                                            onChange={e => setNewLocation(e.target.value)}
                                            onKeyDown={handleAddLocation}
                                        />
                                        <div className="flex flex-wrap gap-2">
                                            {form.getValues("job_preferences.preferred_locations").map(location => (
                                                <Badge
                                                    key={location}
                                                    variant="secondary"
                                                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                                                    onClick={() => handleRemoveLocation(location)}
                                                >
                                                    {location}
                                                    <X className="ml-1 h-3 w-3" />
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <FormLabel>期望行业</FormLabel>
                                        <Input
                                            placeholder="输入期望行业，按回车添加"
                                            value={newIndustry}
                                            onChange={e => setNewIndustry(e.target.value)}
                                            onKeyDown={handleAddIndustry}
                                        />
                                        <div className="flex flex-wrap gap-2">
                                            {form.getValues("job_preferences.preferred_industries").map(industry => (
                                                <Badge
                                                    key={industry}
                                                    variant="secondary"
                                                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                                                    onClick={() => handleRemoveIndustry(industry)}
                                                >
                                                    {industry}
                                                    <X className="ml-1 h-3 w-3" />
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <FormLabel>期望职位</FormLabel>
                                        <Input
                                            placeholder="输入期望职位，按回车添加"
                                            value={newPosition}
                                            onChange={e => setNewPosition(e.target.value)}
                                            onKeyDown={handleAddPosition}
                                        />
                                        <div className="flex flex-wrap gap-2">
                                            {form.getValues("job_preferences.preferred_positions").map(position => (
                                                <Badge
                                                    key={position}
                                                    variant="secondary"
                                                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                                                    onClick={() => handleRemovePosition(position)}
                                                >
                                                    {position}
                                                    <X className="ml-1 h-3 w-3" />
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end">
                                    <Button type="submit" disabled={loading}>
                                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        保存
                                    </Button>
                                </div>
                            </form>
                        </Form>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>简历附件</CardTitle>
                        <CardDescription>上传你的简历，让招聘方更了解你的经历</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center justify-center w-full h-32 px-4 transition bg-muted border-2 border-dashed rounded-lg appearance-none cursor-pointer hover:border-primary focus:outline-none">
                                <div className="flex flex-col items-center space-y-2">
                                    <Upload className="w-8 h-8 text-muted-foreground" />
                                    <span className="text-sm text-muted-foreground">
                                        点击或拖拽文件到此处上传
                                    </span>
                                </div>
                                <input
                                    type="file"
                                    accept=".pdf,.doc,.docx"
                                    className="hidden"
                                    onChange={handleResumeUpload}
                                    disabled={uploading}
                                />
                            </div>
                            {profile.resume_url && (
                                <div className="flex items-center justify-between p-2 bg-muted rounded-lg">
                                    <span className="text-sm truncate">{profile.resume_url}</span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        asChild
                                    >
                                        <a href={profile.resume_url} target="_blank" rel="noopener noreferrer">
                                            <ExternalLink className="h-4 w-4" />
                                        </a>
                                    </Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 