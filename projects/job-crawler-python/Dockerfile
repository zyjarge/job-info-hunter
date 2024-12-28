# 依赖安装阶段
FROM python:3.12-slim as builder

WORKDIR /install

# 只复制依赖相关文件
COPY requirements.txt .

# 安装依赖到特定目录
RUN pip install --no-cache-dir -r requirements.txt --target=/install

# 运行阶段
FROM python:3.12-slim

WORKDIR /app

# 复制依赖
COPY --from=builder /install /usr/local/lib/python3.12/site-packages/

# 安装 playwright 并设置浏览器
RUN pip install --no-cache-dir playwright && \
    python -m playwright install chromium && \
    python -m playwright install-deps

# 创建必要的目录
RUN mkdir -p logs data

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 最后才复制应用代码
COPY . .

# 运行爬虫监听器
CMD ["python", "crawler_listener.py"] 