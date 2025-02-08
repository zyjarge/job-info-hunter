export interface Profile {
  id: string;
  name: string;
  avatar?: string;
  email: string;
  phone?: string;
  location?: string;
  title?: string;  // 职位
  experience?: number;  // 工作年限
  education?: {
    degree: string;  // 学历
    school: string;  // 学校
    major: string;   // 专业
    graduation_year: number;  // 毕业年份
  };
  skills?: string[];  // 技能标签
  job_preferences?: {
    expected_salary_min?: number;  // 期望最低薪资
    expected_salary_max?: number;  // 期望最高薪资
    preferred_locations?: string[];  // 期望工作地点
    preferred_industries?: string[];  // 期望行业
    preferred_positions?: string[];  // 期望职位
  };
  resume_url?: string;  // 简历文件链接
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  name?: string;
  avatar?: string;
  phone?: string;
  location?: string;
  title?: string;
  experience?: number;
  education?: {
    degree: string;
    school: string;
    major: string;
    graduation_year: number;
  };
  skills?: string[];
  job_preferences?: {
    expected_salary_min?: number;
    expected_salary_max?: number;
    preferred_locations?: string[];
    preferred_industries?: string[];
    preferred_positions?: string[];
  };
  resume_url?: string;  // 添加简历文件链接字段
} 