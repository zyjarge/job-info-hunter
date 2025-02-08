import { Crawler } from "./crawler";

export type ScheduleFrequency = "hourly" | "every_6_hours" | "daily" | "weekly";

export interface CrawlerScheduleStatus {
  crawlerId: string;
  lastRunTime?: string;
  nextRunTime?: string;
  enabled: boolean;
  totalJobs?: number;  // 该爬虫采集到的职位数量
  lastError?: string;  // 最后一次运行时的错误信息
}

export interface Schedule {
  id: string;
  name: string;
  keyword: string;
  frequency: ScheduleFrequency;
  crawlerStatuses: CrawlerScheduleStatus[];  // 每个爬虫的状态
  createdAt: string;
  updatedAt: string;
}

export interface CreateScheduleRequest {
  name: string;
  keyword: string;
  frequency: ScheduleFrequency;
  crawlerIds: string[];  // 要创建调度的爬虫ID列表
}

export interface UpdateScheduleRequest {
  id: string;
  name?: string;
  keyword?: string;
  frequency?: ScheduleFrequency;
}

// 更新单个爬虫的状态
export interface UpdateCrawlerStatusRequest {
  scheduleId: string;
  crawlerId: string;
  enabled: boolean;
}

export interface ScheduleWithCrawlers extends Schedule {
  crawlerDetails: Map<string, Crawler>;  // 爬虫ID到爬虫详情的映射
} 