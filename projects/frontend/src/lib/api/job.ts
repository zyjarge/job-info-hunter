import { JobPost, JobSearchParams, JobSearchResponse } from "../types/job";

// 模拟数据
const MOCK_JOBS: JobPost[] = [
  {
    job_id: "1",
    site_id: "51job",
    title: "高级数据工程师",
    company: "阿里巴巴",
    salary: "30k-50k",
    location: "杭州",
    description: "负责数据仓库的设计和开发，参与大数据平台建设...",
    requirements: "5年以上相关工作经验，精通 SQL、Python、Spark...",
    url: "https://jobs.51job.com/...",
    timestamp: "2023-12-28T10:00:00Z",
  },
  {
    job_id: "2",
    site_id: "zhilian",
    title: "资深数据工程师",
    company: "腾讯",
    salary: "35k-60k",
    location: "深圳",
    description: "负责公司核心数据平台的架构设计和开发...",
    requirements: "本科及以上学历，3年以上相关经验，熟悉大数据技术栈...",
    url: "https://zhilian.com/...",
    timestamp: "2023-12-28T09:30:00Z",
  },
  {
    job_id: "3",
    site_id: "boss",
    title: "数据仓库工程师",
    company: "字节跳动",
    salary: "40k-60k",
    location: "北京",
    description: "负责公司数据仓库的建设和优化...",
    requirements: "统招本科及以上，精通 SQL，熟悉 Hadoop 生态...",
    url: "https://www.zhipin.com/...",
    timestamp: "2023-12-28T09:00:00Z",
  },
];

// 搜索职位
export async function searchJobs(params: JobSearchParams): Promise<JobSearchResponse> {
  await new Promise(resolve => setTimeout(resolve, 1000));

  // 模拟搜索逻辑
  let filteredJobs = [...MOCK_JOBS];

  // 关键词搜索
  if (params.keyword) {
    const keyword = params.keyword.toLowerCase();
    filteredJobs = filteredJobs.filter(job =>
      job.title.toLowerCase().includes(keyword) ||
      job.description.toLowerCase().includes(keyword) ||
      job.requirements.toLowerCase().includes(keyword)
    );
  }

  // 地点筛选
  if (params.location) {
    const location = params.location.toLowerCase();
    filteredJobs = filteredJobs.filter(job =>
      job.location.toLowerCase().includes(location)
    );
  }

  // 公司筛选
  if (params.company) {
    const company = params.company.toLowerCase();
    filteredJobs = filteredJobs.filter(job =>
      job.company.toLowerCase().includes(company)
    );
  }

  // 薪资范围筛选
  if (params.salary_min || params.salary_max) {
    filteredJobs = filteredJobs.filter(job => {
      const [min, max] = job.salary
        .toLowerCase()
        .replace(/[^0-9-]/g, '')
        .split('-')
        .map(Number);

      if (params.salary_min && (!min || min < params.salary_min)) {
        return false;
      }
      if (params.salary_max && (!max || max > params.salary_max)) {
        return false;
      }
      return true;
    });
  }

  // 来源网站筛选
  if (params.site_ids && params.site_ids.length > 0) {
    filteredJobs = filteredJobs.filter(job =>
      params.site_ids!.includes(job.site_id)
    );
  }

  // 排序
  if (params.sort_by) {
    filteredJobs.sort((a, b) => {
      if (params.sort_by === 'timestamp') {
        return params.sort_order === 'desc'
          ? new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          : new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      }
      // 其他排序方式...
      return 0;
    });
  }

  // 分页
  const total = filteredJobs.length;
  const total_pages = Math.ceil(total / params.page_size);
  const start = (params.page - 1) * params.page_size;
  const end = start + params.page_size;
  const items = filteredJobs.slice(start, end);

  return {
    total,
    items,
    page: params.page,
    page_size: params.page_size,
    total_pages,
  };
}

// 获取职位详情
export async function getJobDetail(jobId: string, siteId: string): Promise<JobPost | null> {
  await new Promise(resolve => setTimeout(resolve, 500));

  const job = MOCK_JOBS.find(job => job.job_id === jobId && job.site_id === siteId);
  return job || null;
} 