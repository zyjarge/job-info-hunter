-- 检查当前序列值
SELECT last_value FROM job_execution_history_id_seq;

-- 检查表中最大ID
SELECT MAX(id) FROM job_execution_history;

-- 调整 job_execution_history 表的序列值
ALTER SEQUENCE job_execution_history_id_seq RESTART WITH 1362;

-- 验证序列值
SELECT currval('job_execution_history_id_seq');

-- 测试下一个值（可选）
-- SELECT nextval('job_execution_history_id_seq'); -- 这将返回 1363 