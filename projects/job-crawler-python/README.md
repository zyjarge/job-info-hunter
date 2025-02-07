# Job Crawler Python

一个分布式的职位信息爬虫系统，支持多个招聘网站的数据采集。

## 依赖服务

系统依赖以下外部服务：

- RabbitMQ: 消息队列服务，用于任务分发和结果收集
  - 端口: 5672
  - 管理界面端口: 15672
  - 默认用户名/密码: guest/guest

- etcd: 配置中心，用于动态管理爬虫配置
  - 端口: 2379
  - 无需认证

## 基础数据

系统需要以下基础数据：

1. 网站登录 Cookies
   - 存放路径: `cookies/{site_id}_cookies.json`
   - 示例: `cookies/liepin_cookies.json`, `cookies/zhipin_cookies.json`

2. 网站配置文件
   - 存放路径: `conf/{site_id}.json`
   - 示例: `conf/liepin.json`, `conf/zhipin.json`

## 配置说明

### 1. 主配置文件 (conf/config.json)

```json
{
    "site_mapping": {
        "zhipin.com": {
            "module": "sites_crawlers.zhipin.search",
            "class": "BossSearcher",
            "login_module": "sites_crawlers.zhipin.login",
            "login_class": "BossLogin",
            "site_id": "zhipin.com"
        }
    },
    "mq": {
        "host": "job_hunter_mq",
        "port": 5672,
        "username": "guest",
        "password": "guest",
        "queue_name": "crawler.jobs", //调度器向爬虫服务推送消息队列
        "exchange": "job_crawler",
        "routing_key": "crawler.jobs",
        "result_queue_name": "crawler.results", //爬虫服务向数据服务推送消息的队列名称
        "result_routing_key": "crawler.result"
    }
}
```

### 2. 站点配置文件 (conf/{site_id}.json)

```json
{
    "login_url": "https://www.example.com/login",
    "home_url": "https://www.example.com",
    "cookies_file": "cookies/example_cookies.json",
    "headless": true,
    "log_name": "example",
    "log_level": "DEBUG"
}
```

### 3. etcd 配置结构

```
/crawlers/
  ├── sites/                 # 爬虫站点配置
  │   ├── zhipin.com
  │   └── liepin.com
  └── mq/                    # 消息队列配置
      └── config            # MQ 配置信息
```

MQ 配置示例 (/crawlers/mq/config):
```json
{
    "host": "job_hunter_mq",
    "port": 5672,
    "username": "guest",
    "password": "guest",
    "queue_name": "crawler-jobs",
    "exchange": "job_crawler",
    "routing_key": "crawler.job",
    "result_queue_name": "crawler-results",
    "result_routing_key": "crawler.result"
}
```

站点配置示例 (/crawlers/sites/zhipin.com):
```json
{
    "name": "BOSS直聘",
    "description": "BOSS直聘爬虫",
    "homepage": "zhipin.com",
    "enabled": true,
    "config": {
        "module": "sites_crawlers.zhipin.search",
        "class": "BossSearcher",
        "login_module": "sites_crawlers.zhipin.login",
        "login_class": "BossLogin",
        "site_id": "zhipin.com"
    }
}
```

## 代码结构

```
job-crawler-python/
├── conf/                    # 配置文件目录
├── cookies/                 # Cookies 存储目录
├── data/                    # 数据存储目录
├── logs/                    # 日志目录
├── sites_crawlers/          # 爬虫实现目录
│   ├── zhipin/             # BOSS直聘爬虫
│   ├── liepin/             # 猎聘爬虫
│   └── dummy/              # 测试用爬虫
├── tests/                   # 测试代码
├── utils/                   # 工具类
├── crawler_listener.py      # 爬虫监听器入口
└── requirements.txt         # 依赖包列表
```

### 主要模块说明

- `crawler_listener.py`: 爬虫主程序，监听 MQ 消息并执行爬虫任务
- `utils/config_manager.py`: 配置管理器，负责从 etcd 获取和监听配置变更
- `utils/mq_publisher.py`: 消息发布工具，用于发送爬虫结果
- `sites_crawlers/`: 各网站爬虫的具体实现
  - `login.py`: 登录相关功能
  - `search.py`: 搜索和数据采集功能

## 开发新爬虫

要添加新的网站爬虫，需要：

1. 在 `sites_crawlers/` 下创建新的目录
2. 实现 `login.py` 和 `search.py`
3. 在 `conf/config.json` 中添加站点映射
4. 在 `conf/` 下添加站点配置文件
5. 在 `cookies/` 下添加站点 cookies 文件

## 测试工具

- `tests/send_test_message.py`: 发送测试任务
- `tests/consume_results.py`: 消费爬虫结果
- `tests/send_dummy_test.py`: 发送测试任务到 dummy 爬虫