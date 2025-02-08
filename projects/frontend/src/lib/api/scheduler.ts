import { Schedule, CreateScheduleRequest, UpdateScheduleRequest, UpdateCrawlerStatusRequest, ScheduleWithCrawlers, CrawlerScheduleStatus } from "../types/scheduler";
import { getCrawler } from "./crawler";

// 模拟数据
const MOCK_SCHEDULES: Schedule[] = [
  {
    id: "1",
    name: "数据仓库职位",
    keyword: "数据仓库",
    frequency: "daily",
    crawlerStatuses: [
      {
        crawlerId: "1",  // 智联招聘
        enabled: true,
        lastRunTime: "2023-12-28T08:00:00Z",
        nextRunTime: "2023-12-29T08:00:00Z",
        totalJobs: 156,
      },
      {
        crawlerId: "2",  // 前程无忧
        enabled: true,
        lastRunTime: "2023-12-28T08:00:00Z",
        nextRunTime: "2023-12-29T08:00:00Z",
        totalJobs: 89,
      }
    ],
    createdAt: "2023-12-01T00:00:00Z",
    updatedAt: "2023-12-01T00:00:00Z",
  },
  {
    id: "2",
    name: "架构师职位",
    keyword: "架构师",
    frequency: "weekly",
    crawlerStatuses: [
      {
        crawlerId: "2",  // 前程无忧
        enabled: true,
        lastRunTime: "2023-12-25T08:00:00Z",
        nextRunTime: "2024-01-01T08:00:00Z",
        totalJobs: 245,
      },
      {
        crawlerId: "3",  // BOSS直聘
        enabled: false,
        lastRunTime: "2023-12-25T08:00:00Z",
        nextRunTime: "2024-01-01T08:00:00Z",
        totalJobs: 178,
        lastError: "网站访问超时",
      }
    ],
    createdAt: "2023-12-02T00:00:00Z",
    updatedAt: "2023-12-02T00:00:00Z",
  }
];

// 获取调度任务列表
export async function getSchedules(): Promise<Schedule[]> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  return MOCK_SCHEDULES;
}

// 获取调度任务详情（包含爬虫信息）
export async function getScheduleWithCrawlers(id: string): Promise<ScheduleWithCrawlers> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const schedule = MOCK_SCHEDULES.find(s => s.id === id);
  if (!schedule) {
    throw new Error("调度任务不存在");
  }

  // 获取每个爬虫的详细信息
  const crawlerDetails = new Map();
  await Promise.all(
    schedule.crawlerStatuses.map(async status => {
      const crawler = await getCrawler(status.crawlerId);
      crawlerDetails.set(status.crawlerId, crawler);
    })
  );

  return {
    ...schedule,
    crawlerDetails,
  };
}

// 创建调度任务
export async function createSchedule(data: CreateScheduleRequest): Promise<Schedule> {
  await new Promise(resolve => setTimeout(resolve, 1000));

  // 生成下次运行时间
  const nextRunTime = new Date();
  switch (data.frequency) {
    case "hourly":
      nextRunTime.setHours(nextRunTime.getHours() + 1);
      break;
    case "every_6_hours":
      nextRunTime.setHours(nextRunTime.getHours() + 6);
      break;
    case "daily":
      nextRunTime.setDate(nextRunTime.getDate() + 1);
      break;
    case "weekly":
      nextRunTime.setDate(nextRunTime.getDate() + 7);
      break;
  }

  // 为每个爬虫创建状态
  const crawlerStatuses: CrawlerScheduleStatus[] = data.crawlerIds.map(crawlerId => ({
    crawlerId,
    enabled: true,
    nextRunTime: nextRunTime.toISOString(),
    totalJobs: 0,
  }));

  const schedule: Schedule = {
    id: Math.random().toString(36).substr(2, 9),
    name: data.name,
    keyword: data.keyword,
    frequency: data.frequency,
    crawlerStatuses,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  MOCK_SCHEDULES.push(schedule);
  return schedule;
}

// 更新调度任务
export async function updateSchedule(data: UpdateScheduleRequest): Promise<Schedule> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const index = MOCK_SCHEDULES.findIndex(s => s.id === data.id);
  if (index === -1) {
    throw new Error("调度任务不存在");
  }

  // 如果更改了频率，重新计算所有爬虫的下次运行时间
  if (data.frequency) {
    const baseTime = new Date();
    let nextRunTime: string;
    
    switch (data.frequency) {
      case "hourly":
        baseTime.setHours(baseTime.getHours() + 1);
        break;
      case "every_6_hours":
        baseTime.setHours(baseTime.getHours() + 6);
        break;
      case "daily":
        baseTime.setDate(baseTime.getDate() + 1);
        break;
      case "weekly":
        baseTime.setDate(baseTime.getDate() + 7);
        break;
    }
    nextRunTime = baseTime.toISOString();

    // 更新所有启用状态的爬虫的下次运行时间
    MOCK_SCHEDULES[index].crawlerStatuses.forEach(status => {
      if (status.enabled) {
        status.nextRunTime = nextRunTime;
      }
    });
  }

  const schedule = {
    ...MOCK_SCHEDULES[index],
    ...data,
    updatedAt: new Date().toISOString(),
  };

  MOCK_SCHEDULES[index] = schedule;
  return schedule;
}

// 删除调度任务
export async function deleteSchedule(id: string): Promise<void> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const index = MOCK_SCHEDULES.findIndex(s => s.id === id);
  if (index === -1) {
    throw new Error("调度任务不存在");
  }

  MOCK_SCHEDULES.splice(index, 1);
}

// 更新爬虫状态
export async function updateCrawlerStatus(data: UpdateCrawlerStatusRequest): Promise<Schedule> {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const scheduleIndex = MOCK_SCHEDULES.findIndex(s => s.id === data.scheduleId);
  if (scheduleIndex === -1) {
    throw new Error("调度任务不存在");
  }

  const schedule = MOCK_SCHEDULES[scheduleIndex];
  const statusIndex = schedule.crawlerStatuses.findIndex(
    status => status.crawlerId === data.crawlerId
  );

  if (statusIndex === -1) {
    throw new Error("爬虫不存在于该调度任务中");
  }

  // 更新爬虫状态
  schedule.crawlerStatuses[statusIndex] = {
    ...schedule.crawlerStatuses[statusIndex],
    enabled: data.enabled,
  };

  // 如果启用爬虫，计算下次运行时间
  if (data.enabled) {
    const nextRunTime = new Date();
    switch (schedule.frequency) {
      case "hourly":
        nextRunTime.setHours(nextRunTime.getHours() + 1);
        break;
      case "every_6_hours":
        nextRunTime.setHours(nextRunTime.getHours() + 6);
        break;
      case "daily":
        nextRunTime.setDate(nextRunTime.getDate() + 1);
        break;
      case "weekly":
        nextRunTime.setDate(nextRunTime.getDate() + 7);
        break;
    }
    schedule.crawlerStatuses[statusIndex].nextRunTime = nextRunTime.toISOString();
  }

  MOCK_SCHEDULES[scheduleIndex] = schedule;
  return schedule;
} 