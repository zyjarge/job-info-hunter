#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import create_engine, text
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# MySQL 配置
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "ro123ot"),
    "database": os.getenv("MYSQL_DB", "apscheduler"),
}

# PostgreSQL 配置
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "database": os.getenv("PG_DB", "job_hunter"),
}

# 创建数据库连接
mysql_url = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
pg_url = f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"

# 添加所需的导入
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    logger.error("请先安装 pymysql: pip install pymysql")
    sys.exit(1)


def test_connection(engine, db_type):
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"{db_type} 数据库连接测试成功")
        return True
    except SQLAlchemyError as e:
        logger.error(f"{db_type} 数据库连接测试失败: {str(e)}")
        return False


# 创建数据库引擎
mysql_engine = create_engine(mysql_url)
pg_engine = create_engine(pg_url)


def sync_sequences():
    """同步 PostgreSQL 序列"""
    try:
        with pg_engine.connect() as conn:
            # 获取 scheduler_jobs 表的最大 ID
            max_job_id = conn.execute(
                text("SELECT COALESCE(MAX(id), 0) FROM scheduler_jobs")
            ).scalar()
            # 重置序列
            conn.execute(
                text(
                    f"ALTER SEQUENCE scheduler_jobs_id_seq RESTART WITH {max_job_id + 1}"
                )
            )

            # 获取 job_execution_history 表的最大 ID
            max_history_id = conn.execute(
                text("SELECT COALESCE(MAX(id), 0) FROM job_execution_history")
            ).scalar()
            # 重置序列
            conn.execute(
                text(
                    f"ALTER SEQUENCE job_execution_history_id_seq RESTART WITH {max_history_id + 1}"
                )
            )

        logger.info("PostgreSQL 序列同步成功")
    except Exception as e:
        logger.error(f"PostgreSQL 序列同步失败: {str(e)}")
        raise


def create_pg_tables():
    """在 PostgreSQL 中创建表结构"""
    try:
        with pg_engine.begin() as conn:  # 使用事务
            # 创建 scheduler_jobs 表
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS scheduler_jobs (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    description VARCHAR(1000),
                    cron_expression VARCHAR(100),
                    job_params JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                )
                """
                )
            )

            # 创建 job_execution_history 表
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS job_execution_history (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER,
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    status VARCHAR(20),
                    result JSONB,
                    error_message VARCHAR(1000)
                )
                """
                )
            )

            # 创建索引
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_jobs_name ON scheduler_jobs(name)")
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_history_job_id ON job_execution_history(job_id)"
                )
            )

        logger.info("PostgreSQL 表结构创建成功")
    except Exception as e:
        logger.error(f"创建 PostgreSQL 表结构失败: {str(e)}")
        raise


def migrate_data():
    """迁移数据从 MySQL 到 PostgreSQL"""
    try:
        # 从 MySQL 读取数据
        with mysql_engine.connect() as mysql_conn:
            # 迁移 scheduler_jobs 表
            jobs = mysql_conn.execute(text("SELECT * FROM scheduler_jobs")).fetchall()

            # 迁移到 PostgreSQL
            with pg_engine.begin() as pg_conn:
                for job in jobs:
                    job_dict = job._asdict()
                    # 确保 job_params 是 JSON 字符串
                    if job_dict.get("job_params") is None:
                        job_dict["job_params"] = "{}"

                    # 构建基本的插入语句
                    insert_stmt = text(
                        f"""
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
                        """
                    )
                    pg_conn.execute(insert_stmt)

                # 从 MySQL 读取历史数据
                history = mysql_conn.execute(
                    text("SELECT * FROM job_execution_history")
                ).fetchall()

                # 迁移历史数据到 PostgreSQL
                for record in history:
                    record_dict = record._asdict()
                    # 确保 result 是 JSON 字符串
                    if record_dict.get("result") is None:
                        record_dict["result"] = "{}"

                    # 处理可能为 None 的时间字段
                    start_time = (
                        f"'{record_dict['start_time'].isoformat()}'"
                        if record_dict["start_time"]
                        else "NULL"
                    )
                    end_time = (
                        f"'{record_dict['end_time'].isoformat()}'"
                        if record_dict["end_time"]
                        else "NULL"
                    )
                    error_message = (
                        f"'{record_dict['error_message'].replace("'", "''")}'"
                        if record_dict["error_message"]
                        else "NULL"
                    )

                    # 构建基本的插入语句
                    insert_stmt = text(
                        f"""
                        INSERT INTO job_execution_history 
                        (id, job_id, start_time, end_time, status, result, error_message)
                        VALUES 
                        ({record_dict['id']}, 
                         {record_dict['job_id']}, 
                         {start_time}, 
                         {end_time},
                         '{record_dict['status']}', 
                         '{record_dict['result']}'::jsonb,
                         {error_message})
                        """
                    )
                    pg_conn.execute(insert_stmt)

        logger.info(f"数据迁移成功 - 任务数: {len(jobs)}, 历史记录数: {len(history)}")
    except Exception as e:
        logger.error(f"数据迁移失败: {str(e)}")
        raise


def verify_migration():
    """验证迁移结果"""
    try:
        # 验证 scheduler_jobs 表
        with mysql_engine.connect() as mysql_conn:
            mysql_jobs_count = mysql_conn.execute(
                text("SELECT COUNT(*) FROM scheduler_jobs")
            ).scalar()

        with pg_engine.connect() as pg_conn:
            pg_jobs_count = pg_conn.execute(
                text("SELECT COUNT(*) FROM scheduler_jobs")
            ).scalar()

            # 验证 job_execution_history 表
            with mysql_engine.connect() as mysql_conn:
                mysql_history_count = mysql_conn.execute(
                    text("SELECT COUNT(*) FROM job_execution_history")
                ).scalar()

            pg_history_count = pg_conn.execute(
                text("SELECT COUNT(*) FROM job_execution_history")
            ).scalar()

        # 生成验证报告
        report = f"""
迁移验证报告
============
时间: {datetime.now()}

数据对比:
- scheduler_jobs 表:
  * MySQL: {mysql_jobs_count} 条记录
  * PostgreSQL: {pg_jobs_count} 条记录
  * 结果: {'匹配' if mysql_jobs_count == pg_jobs_count else '不匹配'}

- job_execution_history 表:
  * MySQL: {mysql_history_count} 条记录
  * PostgreSQL: {pg_history_count} 条记录
  * 结果: {'匹配' if mysql_history_count == pg_history_count else '不匹配'}

迁移状态: {'成功' if mysql_jobs_count == pg_jobs_count and mysql_history_count == pg_history_count else '失败'}
"""

        # 保存报告
        with open("migration_report.txt", "w") as f:
            f.write(report)

        logger.info("迁移验证完成，报告已生成")
        print(report)

        return (
            mysql_jobs_count == pg_jobs_count
            and mysql_history_count == pg_history_count
        )
    except Exception as e:
        logger.error(f"迁移验证失败: {str(e)}")
        raise


def main():
    """主函数"""
    try:
        logger.info("开始数据库迁移...")

        # 测试数据库连接
        logger.info("步骤 0: 测试数据库连接")
        if not test_connection(mysql_engine, "MySQL") or not test_connection(
            pg_engine, "PostgreSQL"
        ):
            logger.error("数据库连接测试失败，终止迁移")
            sys.exit(1)

        # 1. 创建 PostgreSQL 表结构
        logger.info("步骤 1: 创建 PostgreSQL 表结构")
        create_pg_tables()

        # 2. 迁移数据
        logger.info("步骤 2: 迁移数据")
        migrate_data()

        # 3. 同步序列
        logger.info("步骤 3: 同步序列")
        sync_sequences()

        # 4. 验证迁移
        logger.info("步骤 4: 验证迁移")
        success = verify_migration()

        if success:
            logger.info("迁移成功完成！")
        else:
            logger.error("迁移验证失败！")

    except Exception as e:
        logger.error(f"迁移过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
