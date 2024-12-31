# 基础依赖阶段
FROM node:18-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 开发依赖阶段
FROM base AS deps
COPY package.json package-lock.json ./
# 设置 npm 输出详细日志
ENV NPM_CONFIG_LOGLEVEL verbose
RUN npm ci

# 开发环境
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json

# 设置开发环境变量
ENV NODE_ENV development
ENV NEXT_TELEMETRY_DISABLED 1
ENV NPM_CONFIG_LOGLEVEL verbose

# 暴露开发端口
EXPOSE 3000
EXPOSE 9229

# 启动开发服务器
CMD ["npm", "run", "dev"]

# 构建阶段
FROM base AS builder
WORKDIR /app

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json

# 复制源代码
COPY . .

# 禁用遥测
ENV NEXT_TELEMETRY_DISABLED 1

# 构建应用
RUN npm run build

# 生产阶段
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制必要文件
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 设置权限
USER nextjs

# 配置运行环境
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# 启动命令
CMD ["node", "server.js"] 