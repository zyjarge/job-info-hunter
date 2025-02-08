export interface JobPost {
  job_id: string;
  site_id: string;
  title: string;
  company: string;
  salary: string;
  location: string;
  description: string;
  requirements: string;
  url: string;
  timestamp: string;
}

export interface JobSearchParams {
  keyword: string;
  location?: string;
  company?: string;
  salary_min?: number;
  salary_max?: number;
  site_ids?: string[];  // 指定搜索的网站来源
  page: number;
  page_size: number;
  sort_by?: 'timestamp' | 'salary';
  sort_order?: 'asc' | 'desc';
}

export interface JobSearchResponse {
  total: number;
  items: JobPost[];
  page: number;
  page_size: number;
  total_pages: number;
} 