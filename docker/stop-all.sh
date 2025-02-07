#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 错误处理
set -e
trap 'echo "错误: 在第 $LINENO 行发生错误"' ERR

# 检查容器健康状态和日志的函数
check_container_health() {
    local container_name=$1
    if docker ps -q -f name="^${container_name}$" > /dev/null; then
        echo -e "${YELLOW}容器 ${container_name} 状态：${NC}"
        docker inspect --format "{{.State.Health.Status}}" "${container_name}" 2>/dev/null || echo "No health status"
        echo -e "${YELLOW}容器 ${container_name} 最近的日志：${NC}"
        docker logs --tail 10 "${container_name}" 2>&1 || true
    fi
}

echo -e "${YELLOW}开始停止所有服务...${NC}"

# 检查不健康的容器
echo -e "${YELLOW}检查不健康的容器状态：${NC}"
containers=(
    "job_hunter_meilisearch"
    "job_hunter_postgres"
    "job_hunter_mq"
    "job_hunter_etcd"
)

for container in "${containers[@]}"; do
    check_container_health "${container}"
done

# 使用主 compose 文件停止所有服务
echo -e "${YELLOW}停止所有服务...${NC}"
docker compose -f docker-compose.yml down

# 确保所有相关容器都已停止
echo -e "${YELLOW}确保所有容器已停止...${NC}"
containers=(
    "job_hunter_frontend"
    "job_hunter_api"
    "job_data_service"
    "job_crawler"
    "job_hunter_scheduler"
    "job_hunter_mq"
    "job_hunter_postgres"
    "job_hunter_etcd"
    "job_hunter_meilisearch"
)

for container in "${containers[@]}"; do
    if docker ps -q -f name="^${container}$" > /dev/null; then
        echo -e "${YELLOW}强制停止容器 ${container}...${NC}"
        docker stop "${container}" || true
        docker rm "${container}" || true
    fi
done

# 删除网络（如果存在）
echo -e "${YELLOW}清理网络...${NC}"
docker network rm job_hunter_net 2>/dev/null || true
echo -e "${GREEN}网络已清理${NC}"

# 显示当前运行的容器
echo -e "${YELLOW}检查剩余运行的容器：${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "job_hunter|job_data|job_crawler" || true

echo -e "${GREEN}所有服务已停止！${NC}" 