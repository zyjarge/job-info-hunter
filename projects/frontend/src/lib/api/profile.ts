import { Profile, UpdateProfileRequest } from "../types/profile";

// 模拟数据
const MOCK_PROFILE: Profile = {
  id: "1",
  name: "张三",
  email: "zhangsan@example.com",
  avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
  phone: "13800138000",
  location: "上海",
  title: "高级前端工程师",
  experience: 5,
  education: {
    degree: "本科",
    school: "上海大学",
    major: "计算机科学与技术",
    graduation_year: 2018,
  },
  skills: [
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node.js",
    "Webpack",
    "Docker",
  ],
  job_preferences: {
    expected_salary_min: 25,
    expected_salary_max: 35,
    preferred_locations: ["上海", "杭州", "深圳"],
    preferred_industries: ["互联网", "人工智能", "云计算"],
    preferred_positions: ["前端工程师", "全栈工程师", "技术主管"],
  },
  resume_url: "https://example.com/resume.pdf",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-12-28T10:00:00Z",
};

// 获取个人信息
export async function getProfile(): Promise<Profile> {
  await new Promise(resolve => setTimeout(resolve, 500));
  return MOCK_PROFILE;
}

// 更新个人信息
export async function updateProfile(data: UpdateProfileRequest): Promise<Profile> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  return {
    ...MOCK_PROFILE,
    ...data,
    updated_at: new Date().toISOString(),
  };
}

// 上传头像
export async function uploadAvatar(file: File): Promise<string> {
  await new Promise(resolve => setTimeout(resolve, 1500));
  // 模拟上传成功后返回头像 URL
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${file.name}`;
}

// 上传简历
export async function uploadResume(file: File): Promise<string> {
  await new Promise(resolve => setTimeout(resolve, 1500));
  // 模拟上传成功后返回简历 URL
  return `https://example.com/${file.name}`;
} 