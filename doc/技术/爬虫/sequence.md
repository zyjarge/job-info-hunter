sequenceDiagram
    participant Main
    participant CrawlerListener
    participant MQPublisher
    participant RabbitMQ
    participant LoginModule
    participant CrawlerModule
    
    Note over Main,RabbitMQ: 启动和初始化流程
    Main->>CrawlerListener: 1. 创建实例
    CrawlerListener->>CrawlerListener: 2. 加载 config.json
    CrawlerListener->>MQPublisher: 3. 初始化 MQPublisher
    
    Note over CrawlerListener,RabbitMQ: 连接建立
    CrawlerListener->>RabbitMQ: 4. 连接 RabbitMQ
    CrawlerListener->>RabbitMQ: 5. 声明交换机和队列
    MQPublisher->>RabbitMQ: 6. 建立发布者连接
    
    Note over CrawlerListener,CrawlerModule: 消息处理流程
    RabbitMQ-->>CrawlerListener: 7. 接收爬虫任务消息
    CrawlerListener->>CrawlerListener: 8. 解析消息内容
    
    alt 消息格式正确
        CrawlerListener->>LoginModule: 9. 动态加载登录模块
        LoginModule-->>CrawlerListener: 10. 返回登录实例
        CrawlerListener->>LoginModule: 11. 执行登录
        
        alt 登录成功
            CrawlerListener->>CrawlerModule: 12. 动态加载爬虫模块
            CrawlerModule-->>CrawlerListener: 13. 返回爬虫实例
            CrawlerListener->>CrawlerModule: 14. 执行爬取
            CrawlerModule-->>CrawlerListener: 15. 返回爬取结果
            CrawlerListener->>MQPublisher: 16. 发送结果
            MQPublisher->>RabbitMQ: 17. 发布到结果队列
        else 登录失败
            LoginModule-->>CrawlerListener: 11a. 返回登录失败
            CrawlerListener->>CrawlerListener: 11b. 记录错误日志
        end
        
    else 消息格式错误
        CrawlerListener->>CrawlerListener: 8a. 记录错误日志
    end
    
    Note over CrawlerListener,RabbitMQ: 资源清理
    CrawlerListener->>LoginModule: 18. 关闭浏览器
    CrawlerListener->>RabbitMQ: 19. 确认消息处理完成