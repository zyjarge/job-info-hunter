# MySQL 到 PostgreSQL 数据迁移总结

## 背景
为了简化项目的运维成本，需要将调度系统的数据从 MySQL 迁移到 PostgreSQL。主要涉及两张表：
- `scheduler_jobs`: 存储调度任务信息
- `job_execution_history`: 存储任务执行历史

## 迁移过程中遇到的问题

### 1. 参数绑定语法差异
#### 问题描述
最初使用 SQLAlchemy 的参数绑定语法 `:name` 时遇到错误：
```
syntax error at or near ":"
LINE 5: ...任务', '测试dummy站点的爬虫任务', '*/2 * * * *', :job_param...
```

#### 尝试的解决方案
1. 首次尝试：使用 `:name` 格式
```python
insert_stmt = text("""
    INSERT INTO scheduler_jobs (...) 
    VALUES (:id, :name, ...)
""")
```
结果：失败，PostgreSQL 不支持这种语法

2. 第二次尝试：使用 `%(name)s` 格式
```python
insert_stmt = text("""
    INSERT INTO scheduler_jobs (...) 
    VALUES (%(id)s, %(name)s, ...)
""")
```
结果：失败，出现语法错误

3. 第三次尝试：使用 `$1, $2` 占位符
```python
insert_stmt = text("""
    INSERT INTO scheduler_jobs (...) 
    VALUES ($1, $2, ...)
""").bindparams(...)
```
结果：失败，出现 `'int' object has no attribute '_orig_key'` 错误

### 2. 数据类型转换问题
#### 问题描述
- JSON 字段需要显式转换为 PostgreSQL 的 JSONB 类型
- 时间戳格式需要处理
- NULL 值处理
- 布尔值转换

### 3. 最终解决方案
采用直接字符串构建 SQL 的方式，同时确保安全性：

```python
insert_stmt = text(f"""
    INSERT INTO scheduler_jobs 
    (id, name, description, cron_expression, job_params, is_active, created_at, updated_at)
    VALUES 
    ({job_dict['id']}, 
     '{job_dict['name'].replace("'", "''")}', 
     '{job_dict['description'].replace("'", "''")}', 
     '{job_dict['cron_expression']}', 
     '{job_dict['job_params']}'::jsonb,
     {bool(job_dict['is_active'])}, 
     '{job_dict['created_at'].isoformat()}', 
     '{job_dict['updated_at'].isoformat()}')
""")
```

主要改进：
1. 使用字符串格式化而不是参数绑定
2. 正确处理特殊字符（单引号转义）
3. 显式类型转换（如 JSONB）
4. 适当的时间格式化
5. NULL 值处理
6. 布尔值转换

## 迁移结果验证
最终迁移成功，验证结果：
- `scheduler_jobs` 表：4 条记录完全匹配
- `job_execution_history` 表：1361 条记录完全匹配
- 迁移耗时：不到 1 秒

## 经验总结

1. 数据库差异处理
   - 不同数据库的参数绑定语法可能不兼容
   - 需要注意数据类型的显式转换
   - 时间戳格式需要特别注意

2. 安全性考虑
   - 即使使用字符串构建 SQL，也要确保正确转义
   - 处理特殊字符和 NULL 值
   - 验证数据完整性

3. 性能优化
   - 使用事务进行批量操作
   - 合理的错误处理和日志记录
   - 添加进度指示和验证步骤

4. 最佳实践
   - 先测试数据库连接
   - 创建表结构
   - 迁移数据
   - 同步序列
   - 验证迁移结果
   - 生成迁移报告

## 后续建议

1. 定期备份
   - 建议定期备份 PostgreSQL 数据
   - 保留一段时间的 MySQL 备份，以备不时之需

2. 监控建议
   - 监控 PostgreSQL 的性能指标
   - 关注数据增长趋势
   - 定期检查日志

3. 维护建议
   - 定期进行数据库维护
   - 适时优化查询性能
   - 及时更新统计信息 