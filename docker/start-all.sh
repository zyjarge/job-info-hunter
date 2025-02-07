#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 错误处理
set -e
trap 'echo "错误: 在第 $LINENO 行发生错误"' ERR

echo -e "${YELLOW}开始启动所有服务...${NC}"

# 清理可能存在的已停止或失败的容器
echo -e "${YELLOW}清理已停止的容器...${NC}"
docker rm -f job_hunter_frontend job_hunter_api job_data_service job_crawler job_hunter_scheduler 2>/dev/null || true

echo -e "${YELLOW}启动所有服务...${NC}"
docker compose -f docker-compose.yml up -d

echo -e "${GREEN}所有服务启动完成！${NC}"

# 显示所有容器状态
echo -e "${YELLOW}当前所有容器状态：${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 